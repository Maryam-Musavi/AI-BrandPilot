"""
Embedding generation for the knowledge layer.

Generates text embeddings via a locally running Ollama server, so
semantic search never leaves the machine or touches a cloud API.
Configuration is read from a .env file (or the process environment),
e.g.:

    EMBEDDING_MODEL=nomic-embed-text
    OLLAMA_HOST=http://127.0.0.1:11434

Both have sensible local defaults, so this module works out of the box
against a default local Ollama installation with no configuration at
all. No external API calls are made other than to that local server.
"""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from ollama import Client

load_dotenv()

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


class EmbeddingUnavailableError(Exception):
    """Raised when the embedding backend cannot be reached or fails."""


class EmbeddingService:
    """Generates text embeddings locally via Ollama.

    Attributes:
        model: The Ollama embedding model in use (e.g.
            "nomic-embed-text").
    """

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None) -> None:
        """Initialize the service and its Ollama client.

        Configuration precedence for both `model` and `host`: an
        explicit constructor argument wins, then the corresponding
        environment variable (from .env or the process environment),
        then a built-in local default.

        Args:
            model: The Ollama embedding model to use. Falls back to the
                EMBEDDING_MODEL environment variable, then to
                "nomic-embed-text".
            host: The Ollama server URL. Falls back to the OLLAMA_HOST
                environment variable, then to
                "http://127.0.0.1:11434".
        """
        self.model = model or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        self.host = host or os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
        self._client = Client(host=self.host)

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single piece of text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector as a list of floats.

        Raises:
            EmbeddingUnavailableError: If the embedding backend is
                unreachable or the request fails for any reason.
        """
        return self._embed_many([text])[0]

    def embed_documents(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed a batch of chunks, as produced by TextSplitter.split_text.

        Args:
            chunks: A list of chunk dicts, each with at least a "text"
                key -- e.g. {"chunk_id": ..., "text": ..., "metadata":
                ...} as returned by
                app.knowledge.splitter.TextSplitter.split_text().

        Returns:
            A new list of chunk dicts -- shallow copies of the input,
            each with an added "embedding" key holding its vector, in
            the same order as `chunks`. The input list/dicts are not
            mutated. Returns an empty list for empty input.

        Raises:
            EmbeddingUnavailableError: If the embedding backend is
                unreachable or the request fails for any reason.
        """
        if not chunks:
            return []

        texts = [chunk.get("text", "") for chunk in chunks]
        vectors = self._embed_many(texts)

        embedded_chunks: List[Dict[str, Any]] = []
        for chunk, vector in zip(chunks, vectors):
            enriched = dict(chunk)
            enriched["embedding"] = vector
            embedded_chunks.append(enriched)
        return embedded_chunks

    def _embed_many(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts in one call.

        Args:
            texts: The texts to embed.

        Returns:
            A list of embedding vectors, in the same order as `texts`.
            Returns an empty list if `texts` is empty.

        Raises:
            EmbeddingUnavailableError: If the embedding backend is
                unreachable or the request fails for any reason.
        """
        if not texts:
            return []
        try:
            response = self._client.embed(model=self.model, input=texts)
            return [list(vector) for vector in response.embeddings]
        except Exception as exc:
            raise EmbeddingUnavailableError(
                f"Embedding backend is unavailable "
                f"(model={self.model!r}, host={self.host!r})."
            ) from exc
