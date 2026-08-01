"""
In-memory conversation history service.

Stores a single conversation's message history entirely in RAM. No
database, cache, vector store, or file-based persistence is used. History
is kept in chronological order and capped at a maximum length, with the
oldest message evicted once the cap is exceeded.
"""

from typing import Dict, List

MAX_HISTORY_LENGTH = 20


class ConversationMemory:
    """Keeps a bounded, chronological, in-memory conversation history.

    Messages are stored purely in RAM for the lifetime of the instance.
    Once the number of stored messages exceeds ``max_length``, the oldest
    message is removed to make room for the newest one.

    Attributes:
        max_length: The maximum number of messages retained in history.
    """

    def __init__(self, max_length: int = MAX_HISTORY_LENGTH) -> None:
        """Initialize an empty conversation history.

        Args:
            max_length: The maximum number of messages to retain in
                history. Once exceeded, the oldest message is discarded.
                Defaults to 20.
        """
        self.max_length: int = max_length
        self._history: List[Dict[str, str]] = []

    def add_user_message(self, message: str) -> None:
        """Append a user message to the conversation history.

        Args:
            message: The text content of the user's message.
        """
        self._add_message(role="user", content=message)

    def add_assistant_message(self, message: str) -> None:
        """Append an assistant message to the conversation history.

        Args:
            message: The text content of the assistant's message.
        """
        self._add_message(role="assistant", content=message)

    def get_history(self) -> List[Dict[str, str]]:
        """Return the full conversation history in chronological order.

        Returns:
            A list of message dicts, each shaped as
            ``{"role": "user" | "assistant", "content": str}``, ordered
            from oldest to newest. A shallow copy is returned so external
            callers cannot mutate the internal state.
        """
        return list(self._history)

    def clear(self) -> None:
        """Remove all messages from the conversation history."""
        self._history.clear()

    def _add_message(self, role: str, content: str) -> None:
        """Append a message to history, evicting the oldest if needed.

        Args:
            role: The message author's role (``"user"`` or
                ``"assistant"``).
            content: The text content of the message.
        """
        self._history.append({"role": role, "content": content})
        if len(self._history) > self.max_length:
            self._history.pop(0)
