"""Tests for manage.py (the human-side approval-tracking CLI)."""

from pathlib import Path

import pytest

import manage
from app.memory.database import Database


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(db_path=tmp_path / "test_brandpilot.db")


def test_mark_posted_updates_status_and_timestamp(db: Database) -> None:
    post_id = db.create_post(topic="Topic", content="Body", status="pending_approval")

    exit_code = manage.cmd_mark_posted(db, post_id)

    assert exit_code == 0
    post = db.get_post(post_id)
    assert post["status"] == "posted"
    assert post["published_at"] is not None


def test_mark_posted_returns_error_for_unknown_post(db: Database) -> None:
    exit_code = manage.cmd_mark_posted(db, 9999)
    assert exit_code == 1


def test_list_pending_returns_zero_with_no_drafts(db: Database, capsys: pytest.CaptureFixture) -> None:
    exit_code = manage.cmd_list_pending(db)

    assert exit_code == 0
    assert "No drafts" in capsys.readouterr().out


def test_show_prints_full_content(db: Database, capsys: pytest.CaptureFixture) -> None:
    post_id = db.create_post(topic="Topic", content="Full body text", status="pending_approval")

    exit_code = manage.cmd_show(db, post_id)

    assert exit_code == 0
    assert "Full body text" in capsys.readouterr().out
