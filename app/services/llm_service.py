"""
Abstract contract for an LLM (Large Language Model) backend service.

This module defines ONLY the interface that any concrete LLM integration
(e.g. an OpenAI-backed service, an Ollama-backed service, or any other
provider) must implement. It contains no business logic, no AI logic, and
makes no API calls of any kind. Concrete implementations are out of scope
for this sprint.
"""

from abc import ABC, abstractmethod
from typing import Any, List

from app.models.message import Message


class LLMService(ABC):
    """Abstract base class defining the LLM service contract.

    Any concrete LLM provider integration must subclass this and implement
    both `generate` and `health_check`.
    """

    @abstractmethod
    async def generate(self, messages: List[Message], **kwargs: Any) -> str:
        """Generate a completion for the given list of messages.

        Args:
            messages: The conversation history to send to the LLM.
            **kwargs: Provider-specific generation options (e.g. temperature,
                max_tokens). Left generic on purpose at this stage.

        Returns:
            The generated text completion.
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check whether the underlying LLM backend is reachable and healthy.

        Returns:
            True if the backend is healthy/reachable, False otherwise.
        """
        raise NotImplementedError
