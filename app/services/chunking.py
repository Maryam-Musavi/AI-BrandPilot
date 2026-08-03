"""
Text chunking utility.

Splits documents into overlapping, retrievable text chunks. Pure Python,
character-based -- no external dependencies. This only prepares text
for the embedding step; no AI logic lives here.
"""

from typing import List

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split text into overlapping chunks of roughly chunk_size characters.

    Splits on paragraph boundaries (blank lines) where possible, to
    avoid cutting sentences mid-thought, falling back to a hard
    character split for any single paragraph longer than chunk_size.

    Args:
        text: The full document text to split.
        chunk_size: Target maximum characters per chunk.
        chunk_overlap: Number of trailing characters from the previous
            chunk to repeat at the start of the next, for context
            continuity across chunk boundaries.

    Returns:
        A list of non-empty, whitespace-trimmed text chunks, in order.
        Returns an empty list for blank input.
    """
    normalized = text.strip()
    if not normalized:
        return []

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [normalized]

    chunks: List[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(paragraph) <= chunk_size:
            current = paragraph
        else:
            current = ""
            step = max(chunk_size - chunk_overlap, 1)
            for start in range(0, len(paragraph), step):
                piece = paragraph[start : start + chunk_size].strip()
                if piece:
                    chunks.append(piece)

    if current:
        chunks.append(current)

    return _apply_overlap(chunks, chunk_overlap)


def _apply_overlap(chunks: List[str], overlap: int) -> List[str]:
    """Prefix each chunk (after the first) with trailing overlap text.

    Args:
        chunks: The chunks produced by paragraph-based splitting.
        overlap: Number of trailing characters to carry over from the
            previous chunk.

    Returns:
        The chunks with overlap text applied between consecutive
        entries. Returned unchanged if overlap is 0 or there is at most
        one chunk.
    """
    if overlap <= 0 or len(chunks) < 2:
        return chunks

    result = [chunks[0]]
    for index in range(1, len(chunks)):
        previous_tail = chunks[index - 1][-overlap:]
        result.append(f"{previous_tail}\n\n{chunks[index]}")
    return result
