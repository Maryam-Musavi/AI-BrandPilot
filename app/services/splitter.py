"""
Document splitter for the knowledge ingestion layer.

Splits normalized document text into overlapping chunks sized for
embedding, each carrying enough metadata (filename, page, source) to
trace a retrieved chunk back to where it came from. Pure Python,
character-based, paragraph-aware -- no external API calls of any kind.
"""

import uuid
from typing import Any, Dict, List, Optional

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100


class TextSplitter:
    """Splits text into overlapping, metadata-carrying chunks.

    Attributes:
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Number of trailing characters from the previous
            chunk repeated at the start of the next, for context
            continuity across chunk boundaries.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """Initialize the splitter with its chunking parameters.

        Args:
            chunk_size: Target maximum characters per chunk. Must be
                greater than 0.
            chunk_overlap: Number of trailing characters carried over
                between consecutive chunks. Must be >= 0 and smaller
                than chunk_size.

        Raises:
            ValueError: If chunk_size <= 0, chunk_overlap < 0, or
                chunk_overlap >= chunk_size.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks, each with its own metadata.

        Args:
            text: The text to split -- typically one document's (or one
                page's) normalized text.
            metadata: Optional context attached to every resulting
                chunk, e.g. {"filename": "brief.docx", "page": 1,
                "source": "app/knowledge/brief.docx"}. Any of
                "filename", "page", "source" that are omitted default
                to None in each chunk's metadata.

        Returns:
            A list of dicts, each shaped as:
            {"chunk_id": str, "text": str, "metadata": {"filename":
            ..., "page": ..., "source": ..., "chunk_index": int}},
            in order. Returns an empty list for blank/whitespace-only
            input.
        """
        base_metadata = metadata or {}
        pieces = self._split_into_pieces(text)

        chunks: List[Dict[str, Any]] = []
        for index, piece in enumerate(pieces):
            chunk_metadata = {
                "filename": base_metadata.get("filename"),
                "page": base_metadata.get("page"),
                "source": base_metadata.get("source"),
                "chunk_index": index,
            }
            chunks.append(
                {
                    "chunk_id": uuid.uuid4().hex,
                    "text": piece,
                    "metadata": chunk_metadata,
                }
            )
        return chunks

    def _split_into_pieces(self, text: str) -> List[str]:
        """Split raw text into paragraph-aware pieces, with overlap applied.

        Splits on paragraph boundaries (blank lines) where possible, to
        avoid cutting sentences mid-thought, falling back to a hard
        character split for any single paragraph longer than
        chunk_size.

        Args:
            text: The text to split.

        Returns:
            A list of non-empty, whitespace-trimmed text pieces, in
            order, with overlap applied between consecutive entries.
            Returns an empty list for blank input.
        """
        normalized = text.strip()
        if not normalized:
            return []

        paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [normalized]

        pieces: List[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}" if current else paragraph

            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                pieces.append(current)

            if len(paragraph) <= self.chunk_size:
                current = paragraph
            else:
                current = ""
                step = max(self.chunk_size - self.chunk_overlap, 1)
                for start in range(0, len(paragraph), step):
                    piece = paragraph[start : start + self.chunk_size].strip()
                    if piece:
                        pieces.append(piece)

        if current:
            pieces.append(current)

        return self._apply_overlap(pieces)

    def _apply_overlap(self, pieces: List[str]) -> List[str]:
        """Prefix each piece (after the first) with trailing overlap text.

        Args:
            pieces: The pieces produced by paragraph-based splitting.

        Returns:
            The pieces with overlap text applied between consecutive
            entries. Returned unchanged if chunk_overlap is 0 or there
            is at most one piece.
        """
        if self.chunk_overlap <= 0 or len(pieces) < 2:
            return pieces

        result = [pieces[0]]
        for index in range(1, len(pieces)):
            previous_tail = pieces[index - 1][-self.chunk_overlap :]
            result.append(f"{previous_tail}\n\n{pieces[index]}")
        return result
