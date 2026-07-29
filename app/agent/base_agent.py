"""
Base agent implementation.

BaseAgent loads a system prompt and combines it with the user's message
before delegating generation to LLMService. No AI provider selection,
database, authentication, or memory is implemented here.
"""

from typing import Optional

from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService

SYSTEM_PROMPT_FILENAME = "system_prompt.md"


class BaseAgent:
    """Agent that combines a system prompt with the user's message and
    delegates generation to an LLMService instance.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
    ) -> None:
        """Initialize the agent with an LLMService and a PromptService.

        Args:
            llm_service: The LLM service to use. Defaults to a new
                LLMService instance if not provided.
            prompt_service: The prompt service to use. Defaults to a new
                PromptService instance if not provided.
        """
        self.llm_service = llm_service or LLMService()
        self.prompt_service = prompt_service or PromptService()

    def chat(self, message: str) -> str:
        """Handle a chat message end-to-end.

        Loads the system prompt, combines it with the user's message, and
        delegates generation to the LLM service.

        Args:
            message: The user's chat message text.

        Returns:
            The generated response text from the LLM service.
        """
        system_prompt = self.prompt_service.load_prompt(SYSTEM_PROMPT_FILENAME)
        combined = f"{system_prompt}\n\n{message}"
        return self.llm_service.generate(combined)
