"""
LLM service implementation.

For this sprint, LLMService is a mock implementation used to validate the
end-to-end request flow. No real AI provider (OpenAI, Ollama, etc.) is
connected here.
"""


class LLMService:
    """Mock LLM service used until a real provider is integrated."""

    def generate(self, text: str) -> str:
        """Generate a response for the given input text.

        Args:
            text: The input text/prompt.

        Returns:
            A fixed mock response string.
        """
        return "This is a mock response."
