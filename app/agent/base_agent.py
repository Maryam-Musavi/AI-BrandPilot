"""
Base agent implementation.

BaseAgent composes a persona, a system prompt, conversation history, and
the user's message, then either delegates to a registered tool (via
ToolRouter) or falls back to LLMService. The resulting exchange is
persisted back into conversation memory either way. No AI provider
selection, database, authentication, or vector/file-based memory is
implemented here.
"""

from typing import Dict, List, Optional

from app.memory.conversation_memory import ConversationMemory
from app.services.llm_service import LLMService
from app.services.persona_service import PersonaService
from app.services.prompt_service import PromptService
from app.tools.tool_router import ToolRouter

SYSTEM_PROMPT_FILENAME = "system_prompt.md"


class BaseAgent:
    """Agent that composes persona, system prompt, conversation history,
    and the user's message, then either delegates to a matching tool or
    falls back to an LLMService instance, persisting the exchange in
    conversation memory either way.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        prompt_service: Optional[PromptService] = None,
        persona_service: Optional[PersonaService] = None,
        conversation_memory: Optional[ConversationMemory] = None,
        tool_router: Optional[ToolRouter] = None,
    ) -> None:
        """Initialize the agent with its collaborating services.

        Args:
            llm_service: The LLM service to use. Defaults to a new
                LLMService instance if not provided.
            prompt_service: The prompt service to use. Defaults to a new
                PromptService instance if not provided.
            persona_service: The persona service to use. Defaults to a
                new PersonaService instance if not provided.
            conversation_memory: The conversation memory to use. Defaults
                to a new ConversationMemory instance if not provided.
            tool_router: The tool router to use. Defaults to a new
                ToolRouter instance if not provided.
        """
        self.llm_service = llm_service or LLMService()
        self.prompt_service = prompt_service or PromptService()
        self.persona_service = persona_service or PersonaService()
        self.conversation_memory = conversation_memory or ConversationMemory()
        self.tool_router = tool_router or ToolRouter()

    def chat(self, message: str) -> str:
        """Handle a chat message end-to-end.

        Workflow:
            1. Load the persona (optional).
            2. Load the system prompt (required).
            3. Load the conversation history.
            4. Check the tool router for a matching tool.
               - If a tool handles the query, save the exchange to
                 conversation memory and return its result immediately.
               - Otherwise, compose persona + system prompt + history +
                 the current message and delegate to the LLM service.
            5. Save the user message and the response to conversation
               memory.
            6. Return the response.

        Args:
            message: The user's chat message text.

        Returns:
            The tool result (if a tool handled the query) or the
            generated response text from the LLM service.

        Raises:
            FileNotFoundError: If the system prompt file is missing.
        """
        persona = self._load_persona_safely()
        system_prompt = self.prompt_service.load_prompt(SYSTEM_PROMPT_FILENAME)
        history = self.conversation_memory.get_history()

        tool_result = self.tool_router.route(message)
        if tool_result is not None:
            self.conversation_memory.add_user_message(message)
            self.conversation_memory.add_assistant_message(tool_result)
            return tool_result

        conversation = history + [{"role": "user", "content": message}]
        conversation_text = self._format_conversation(conversation)

        sections = [
            section
            for section in (persona, system_prompt, conversation_text)
            if section
        ]
        combined = "\n\n".join(sections)

        response = self.llm_service.generate(combined)

        self.conversation_memory.add_user_message(message)
        self.conversation_memory.add_assistant_message(response)

        return response

    def _load_persona_safely(self) -> str:
        """Load the persona, tolerating a missing persona file.

        Returns:
            The formatted persona text, or an empty string if
            memory/persona.yaml does not exist.
        """
        try:
            return self.persona_service.load_persona()
        except FileNotFoundError:
            return ""

    @staticmethod
    def _format_conversation(conversation: List[Dict[str, str]]) -> str:
        """Format a list of role/content messages into plain text.

        Args:
            conversation: A list of message dicts shaped as
                ``{"role": "user" | "assistant", "content": str}``, in
                chronological order.

        Returns:
            A newline-separated "Role: content" text block.
        """
        lines = [
            f"{entry['role'].capitalize()}: {entry['content']}"
            for entry in conversation
        ]
        return "\n".join(lines)
