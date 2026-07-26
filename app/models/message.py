"""
Core data contract for a single chat/LLM message.

This module defines ONLY the data shape used to represent a message
exchanged between the user, an agent, and/or an LLM backend. It contains
no business logic, no AI logic, and no API calls.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in a conversation.

    Attributes:
        role: Who authored the message (e.g. "user", "assistant", "system").
        content: The textual content of the message.
        timestamp: When the message was created. Defaults to the current
            UTC time if not explicitly provided.
    """

    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
