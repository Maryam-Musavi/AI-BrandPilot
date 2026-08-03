"""
Knowledge service.

Top-level orchestration for the RAG knowledge layer: ingesting local
documents (and generated LinkedIn posts) into the knowledge store, and
retrieving semantically relevant chunks for a query. Ties together
chunking, embedding, and the SQLite-backed KnowledgeStore.

Sprint 12 scope: TXT and Markdown ingestion only. New file types can be
added later purely by registering another loader in `_LOADERS` below --
no other code needs to change.

Every public method degrades gracefully: if the embedding backend is
unavailable, or the knowledge base is empty, ingestion/retrieval simply
have no effect / return no results, rather than raising. This is what
lets ResearchAgent and ContentAgent keep working normally with an empty
or not-yet-ingested knowledge base.
"""

import hashlib
import math
from pathlib import Path
from typing import Callable, Dict, List, Optional

from app.services.chunking import chunk_text
from app.services.embedding_service import EmbeddingService, EmbeddingUnavailableError
from memory.knowledge_store import KnowledgeStore

DEFAULT_TOP_K = 3


def _load_text_file(path: Path) -> str:
    """Read a plain-text or Markdown file as UTF-8 text.

    Args:
        path: Path to the file to read.

    Returns:
        The file's decoded text content.
    """
    return path.read_text(encoding="utf-8")


# Extension -> loader function. Sprint 12 supports .txt/.md only; adding
# PDF/DOCX later is just another entry here (e.g. ".pdf": _load_pdf_file),
# with no change needed to ingest_file/ingest_directory.
_LOADERS: Dict[str, Callable[[Path], str]] = {
    ".txt": _load_text_file,
    ".md": _load_text_file,
}


def _hash_text(text: str) -> str:
    """Compute a stable content hash for change detection.

    Args:
        text: The text to hash.

    Returns:
        A hex-encoded SHA-256 digest of the text.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """Compute cosine similarity between two equal-length vectors.

    Args:
        vector_a: The first vector.
        vector_b: The second vector.

    Returns:
        The cosine similarity in [-1, 1], or 0.0 if either vector has
        zero magnitude (e.g. malformed embeddings).
    """
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class KnowledgeService:
    """Orchestrates ingestion and retrieval for the knowledge layer."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        knowledge_store: Optional[KnowledgeStore] = None,
    ) -> None:
        """Initialize the service with its collaborators.

        Args:
            embedding_service: The embedding backend to use. Defaults to
                a new EmbeddingService instance if not provided.
            knowledge_store: The vector/chunk store to use. Defaults to
                a new KnowledgeStore instance if not provided.
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.knowledge_store = knowledge_store or KnowledgeStore()

    # ------------------------------------------------------------------
    # ingestion
    # ------------------------------------------------------------------

    def ingest_text(self, source: str, text: str) -> bool:
        """Chunk, embed, and store a piece of text under a source id.

        Idempotent: if `source` was already ingested with identical
        content, this is a no-op. If the embedding backend is
        unavailable, ingestion is skipped rather than raising.

        Args:
            source: A unique identifier for this content (e.g. a file
                path, or "post:123" for a generated post).
            text: The full text to ingest.

        Returns:
            True if the document was (re-)ingested, False if it was
            skipped (unchanged, blank, or the embedding backend is
            currently unavailable).
        """
        normalized = text.strip()
        if not normalized:
            return False

        content_hash = _hash_text(normalized)
        if self.knowledge_store.get_document_hash(source) == content_hash:
            return False

        chunks = chunk_text(normalized)
        if not chunks:
            return False

        try:
            vectors = self.embedding_service.embed_many(chunks)
        except EmbeddingUnavailableError:
            return False

        document_id = self.knowledge_store.upsert_document(source, content_hash)
        self.knowledge_store.replace_chunks(document_id, list(zip(chunks, vectors)))
        return True

    def ingest_file(self, path: Path) -> bool:
        """Ingest a single supported file (.txt or .md).

        Args:
            path: Path to the file to ingest.

        Returns:
            True if the file was (re-)ingested, False if it was skipped
            (unsupported extension, unchanged content, or the embedding
            backend is unavailable).
        """
        loader = _LOADERS.get(path.suffix.lower())
        if loader is None:
            return False
        text = loader(path)
        return self.ingest_text(source=str(path), text=text)

    def ingest_directory(self, directory: Path) -> Dict[str, int]:
        """Ingest every supported file under a directory (recursively).

        Args:
            directory: The directory to scan for .txt/.md files.

        Returns:
            A summary dict: {"ingested": n, "skipped": n,
            "unsupported": n}.
        """
        summary = {"ingested": 0, "skipped": 0, "unsupported": 0}
        if not directory.is_dir():
            return summary

        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _LOADERS:
                summary["unsupported"] += 1
                continue
            if self.ingest_file(path):
                summary["ingested"] += 1
            else:
                summary["skipped"] += 1

        return summary

    def ingest_generated_post(self, post_id: int, content: str) -> bool:
        """Ingest a generated LinkedIn post into the knowledge base.

        Args:
            post_id: The post's id in the business database
                (memory/database.py).
            content: The post's text content.

        Returns:
            True if the post was (re-)ingested, False if it was skipped.
        """
        return self.ingest_text(source=f"post:{post_id}", text=content)

    # ------------------------------------------------------------------
    # retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> List[str]:
        """Retrieve the most semantically relevant chunks for a query.

        Args:
            query: The text to search for.
            top_k: The maximum number of chunks to return.

        Returns:
            The top-k most similar chunk texts, most relevant first. An
            empty list if the knowledge base has no chunks yet, or if
            the embedding backend is currently unavailable.
        """
        try:
            query_vector = self.embedding_service.embed(query)
        except EmbeddingUnavailableError:
            return []

        all_chunks = self.knowledge_store.list_all_chunks()
        if not all_chunks:
            return []

        scored = [
            (_cosine_similarity(query_vector, chunk["embedding"]), chunk["content"])
            for chunk in all_chunks
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [content for _, content in scored[:top_k]]

    def list_document_sources(self) -> List[str]:
        """List the source identifiers of every ingested document.

        Returns:
            A list of document source strings (file paths and/or
            "post:<id>" identifiers).
        """
        return [doc["source"] for doc in self.knowledge_store.list_documents()]

    def is_empty(self) -> bool:
        """Check whether the knowledge base currently has any content.

        Returns:
            True if no chunks have been ingested yet, False otherwise.
        """
        return self.knowledge_store.count_chunks() == 0
