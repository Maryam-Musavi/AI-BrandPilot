"""Tests for app/memory/database.py (long-term business memory)."""

from pathlib import Path

import pytest

from app.memory.database import Database


@pytest.fixture
def db(tmp_path: Path) -> Database:
    """A Database instance backed by a throwaway SQLite file per test."""
    return Database(db_path=tmp_path / "test_brandpilot.db")


def test_create_and_get_post(db: Database) -> None:
    post_id = db.create_post(topic="Test topic", content="", status="idea")
    post = db.get_post(post_id)

    assert post is not None
    assert post["topic"] == "Test topic"
    assert post["status"] == "idea"
    assert post["content"] == ""


def test_update_post_content_sets_status(db: Database) -> None:
    post_id = db.create_post(topic="Topic", content="", status="idea")
    db.update_post_content(post_id, content="Draft body", status="pending_approval")

    post = db.get_post(post_id)
    assert post["content"] == "Draft body"
    assert post["status"] == "pending_approval"


def test_list_posts_filters_by_status(db: Database) -> None:
    db.create_post(topic="A", content="", status="idea")
    db.create_post(topic="B", content="x", status="pending_approval")

    ideas = db.list_posts(status="idea")
    pending = db.list_posts(status="pending_approval")

    assert len(ideas) == 1 and ideas[0]["topic"] == "A"
    assert len(pending) == 1 and pending[0]["topic"] == "B"


def test_record_topic_used_increments_count(db: Database) -> None:
    db.record_topic_used("Some topic")
    db.record_topic_used("Some topic")

    usage = db.get_topic_usage("Some topic")
    assert usage is not None
    assert usage["used_count"] == 2


def test_log_agent_action_is_recorded(db: Database) -> None:
    db.log_agent_action("ContentAgent", "generated_post:Some topic")

    logs = db.list_agent_logs(agent_name="ContentAgent")
    assert len(logs) == 1
    assert logs[0]["action"] == "generated_post:Some topic"
