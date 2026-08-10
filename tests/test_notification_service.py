"""Tests for app/services/notification_service.py.

No real SMTP connection is ever made here -- smtplib.SMTP is monkeypatched.
"""

from typing import List

import pytest

from app.services import notification_service as notification_module
from app.services.notification_service import NotificationService


@pytest.fixture(autouse=True)
def _configured_smtp_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give the module fully-configured, fake SMTP settings by default."""
    monkeypatch.setattr(notification_module.settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(notification_module.settings, "smtp_port", 587)
    monkeypatch.setattr(notification_module.settings, "smtp_use_tls", True)
    monkeypatch.setattr(notification_module.settings, "smtp_username", "user@example.com")
    monkeypatch.setattr(notification_module.settings, "smtp_password", "secret")
    monkeypatch.setattr(notification_module.settings, "smtp_from_email", "bot@example.com")
    monkeypatch.setattr(notification_module.settings, "notify_to_email", "me@example.com")


def test_is_configured_true_when_all_fields_present() -> None:
    assert NotificationService().is_configured() is True


def test_is_configured_false_when_smtp_host_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(notification_module.settings, "smtp_host", None)
    assert NotificationService().is_configured() is False


def test_send_draft_for_approval_skipped_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(notification_module.settings, "smtp_host", None)
    service = NotificationService()

    result = service.send_draft_for_approval(1, "Topic", "Body")

    assert result is False


def test_send_draft_for_approval_sends_via_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_messages: List[object] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.host = host
            self.port = port

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *exc_info: object) -> None:
            return None

        def starttls(self) -> None:
            pass

        def login(self, username: str, password: str) -> None:
            pass

        def send_message(self, message: object) -> None:
            sent_messages.append(message)

    monkeypatch.setattr(notification_module.smtplib, "SMTP", FakeSMTP)

    service = NotificationService()
    result = service.send_draft_for_approval(42, "LLMOps", "The full post text.")

    assert result is True
    assert len(sent_messages) == 1
    message = sent_messages[0]
    assert "LLMOps" in message["Subject"]
    assert message["To"] == "me@example.com"


def test_send_draft_for_approval_returns_false_on_smtp_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise(*args: object, **kwargs: object) -> None:
        raise ConnectionRefusedError("no server here")

    monkeypatch.setattr(notification_module.smtplib, "SMTP", _raise)

    service = NotificationService()
    result = service.send_draft_for_approval(1, "Topic", "Body")

    assert result is False
