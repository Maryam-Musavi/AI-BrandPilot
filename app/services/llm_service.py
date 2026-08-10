"""
LLM service implementation.

Integrates with a locally running Ollama server to generate chat
completions. No other AI provider, streaming, memory, or database is
implemented here.
"""

import logging

from ollama import Client

from app.config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service backed by a local Ollama server."""

    def __init__(self) -> None:
        """Initialize a single reusable Ollama client instance."""
        self._client = Client(host=settings.ollama_base_url)

    def generate(self, text: str) -> str:
        """Generate a response for the given input text via Ollama.

        Args:
            text: The input text/prompt.

        Returns:
            The assistant's reply text, or a fallback message if the
            Ollama server is unavailable or the request fails.
        """
        try:
            response = self._client.chat(
                model=settings.ollama_model,
                messages=[{"role": "user", "content": text}],
                stream=False,
            )
            return response.message.content
        except Exception:
            logger.exception(
                "Ollama request failed (host=%s, model=%s).",
                settings.ollama_base_url,
                settings.ollama_model,
            )
            return "Ollama is unavailable."
