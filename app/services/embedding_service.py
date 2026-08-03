"""
Embedding service implementation.

Generates text embeddings via a locally running Ollama server (using an
embedding-purpose model such as nomic-embed-text), so semantic search
never leaves the machine or touches a cloud API. Mirrors the same
Client-wrapping pattern as LLMService, but for embeddings instead of
chat completions.
"""

from typing import List

from ollama import Client

from app.config.settings import settings


class EmbeddingUnavailableError(Exception):
    """Raised when the embedding backend cannot be reached or fails."""


class EmbeddingService:
    """Embedding service backed by a local Ollama server."""

    def __init__(self) -> None:
        """Initialize a single reusable Ollama client instance."""
        self._client = Client(host=settings.ollama_base_url)

    def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for a single piece of text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector as a list of floats.

        Raises:
            EmbeddingUnavailableError: If the embedding backend is
                unreachable or the request fails for any reason.
        """
        vectors = self.embed_many([text])
        return vectors[0]

    def embed_many(self, texts: List[str]) -> List[List[float]]:
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
            response = self._client.embed(
                model=settings.ollama_embedding_model,
                input=texts,
            )
            return [list(vector) for vector in response.embeddings]
        except Exception as exc:
            raise EmbeddingUnavailableError(
                "Embedding backend is unavailable."
            ) from exc
