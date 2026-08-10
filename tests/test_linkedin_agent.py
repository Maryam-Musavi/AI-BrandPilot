"""Integration test for the Sprint 13 email-notification wiring.

Uses fakes for LLM/notification so no real network calls (Ollama, SMTP)
are made, and a throwaway SQLite file so no real business data is
touched.
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest

from app.agent.content_agent import ContentAgent
from app.agent.linkedin_agent import LinkedInAgent
from app.agent.research_agent import LocalMockTopicSource, ResearchAgent
from app.memory.database import Database
from app.services.knowledge_service import KnowledgeService


class FakeLLMService:
    """Stands in for LLMService so no real Ollama call is made."""

    def generate(self, text: str) -> str:
        return "This is a fake generated LinkedIn post about the topic."


class FakeNotificationService:
    """Records every "send" call instead of touching SMTP."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def send_draft_for_approval(self, post_id: int, topic: str, content: str) -> bool:
        self.calls.append({"post_id": post_id, "topic": topic, "content": content})
        return True


@pytest.fixture
def agent(tmp_path: Path) -> LinkedInAgent:
    """A LinkedInAgent wired with fakes so the test is fast and offline."""
    database = Database(db_path=tmp_path / "test_brandpilot.db")
    knowledge_service = KnowledgeService()
    research_agent = ResearchAgent(
        topic_source=LocalMockTopicSource(),
        database=database,
        knowledge_service=knowledge_service,
    )
    content_agent = ContentAgent(llm_service=FakeLLMService(), database=database)

    return LinkedInAgent(
        research_agent=research_agent,
        content_agent=content_agent,
        database=database,
        knowledge_service=knowledge_service,
        notification_service=FakeNotificationService(),
    )


def test_generate_post_draft_sends_approval_notification(agent: LinkedInAgent) -> None:
    result = agent.generate_post_draft()

    notifier: FakeNotificationService = agent.notification_service  # type: ignore[assignment]
    assert len(notifier.calls) == 1
    assert notifier.calls[0]["post_id"] == result["post_id"]
    assert notifier.calls[0]["topic"] == result["topic"]
    assert notifier.calls[0]["content"] == result["content"]


def test_generate_post_draft_saves_pending_approval_status(agent: LinkedInAgent) -> None:
    result = agent.generate_post_draft()

    saved_post = agent.database.get_post(result["post_id"])
    assert saved_post is not None
    assert saved_post["status"] == "pending_approval"
    assert saved_post["content"] == result["content"]
