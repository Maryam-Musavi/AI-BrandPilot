"""
Base agent implementation.

For this sprint, BaseAgent orchestrates a simple chat flow by delegating
to LLMService. No AI provider, database, authentication, or memory is
implemented here.
"""

from app.services.llm_service import LLMService


class BaseAgent:
    """Agent that delegates chat generation to an LLMService instance."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        """Initialize the agent with an LLMService instance.

        Args:
            llm_service: The LLM service to use. Defaults to a new
                LLMService instance if not provided.
        """
        self.llm_service = llm_service or LLMService()

    def chat(self, message: str) -> str:
        """Handle a chat message end-to-end.

        Args:
            message: The user's chat message text.

        Returns:
            The generated response text from the LLM service.
        """
        return self.llm_service.generate(message)
