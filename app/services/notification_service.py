"""
Draft-approval email notifications.

Sprint 13 scope: when LinkedInAgent produces a Wednesday draft, it is
saved with status "pending_approval" (see app/agent/linkedin_agent.py)
and this service emails the draft's full text to the configured
recipient. That's it -- there is deliberately no LinkedIn API call, no
auto-publish, and no click-to-approve link anywhere in this module.
The human reads the email, copies the text, and posts it on LinkedIn
themselves whenever they're happy with it.

Sending is always best-effort: any failure (missing config, unreachable
SMTP server, bad credentials, ...) is logged and swallowed rather than
raised, so a broken mailbox can never take down the core posting
workflow. If SMTP_HOST is not configured at all, sending is skipped
silently (notifications are an opt-in feature, off by default).
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends "a draft is ready for you" emails over SMTP."""

    def is_configured(self) -> bool:
        """Check whether enough SMTP settings are present to attempt sending.

        Returns:
            True if smtp_host, smtp_from_email, and notify_to_email are
            all set, False otherwise.
        """
        return bool(
            settings.smtp_host and settings.smtp_from_email and settings.notify_to_email
        )

    def send_draft_for_approval(
        self, post_id: int, topic: str, content: str
    ) -> bool:
        """Email a generated draft to the configured recipient for review.

        Args:
            post_id: The draft's id in the business database, included
                so the person can cross-reference it later if needed.
            topic: The draft's topic, used in the email subject.
            content: The full generated post text.

        Returns:
            True if the email was sent, False if it was skipped
            (notifications not configured) or failed (logged, not
            raised).
        """
        if not self.is_configured():
            logger.info(
                "Email notifications are not configured (SMTP_HOST/"
                "SMTP_FROM_EMAIL/NOTIFY_TO_EMAIL); skipping notification "
                "for post_id=%s.",
                post_id,
            )
            return False

        message = self._build_message(post_id, topic, content)

        try:
            self._send(message)
        except Exception:
            logger.exception(
                "Failed to send draft-approval email for post_id=%s.", post_id
            )
            return False

        logger.info("Sent draft-approval email for post_id=%s.", post_id)
        return True

    @staticmethod
    def _build_message(post_id: int, topic: str, content: str) -> EmailMessage:
        """Build the EmailMessage for a draft-approval notification.

        Args:
            post_id: The draft's id.
            topic: The draft's topic.
            content: The full generated post text.

        Returns:
            A populated EmailMessage, not yet sent.
        """
        message = EmailMessage()
        message["Subject"] = f"[AI BrandPilot] Draft ready for review: {topic}"
        message["From"] = settings.smtp_from_email
        message["To"] = settings.notify_to_email
        message.set_content(
            "A new LinkedIn post draft is waiting for your review.\n\n"
            f"Post ID: {post_id}\n"
            f"Topic: {topic}\n"
            "Status: pending_approval (nothing has been posted -- this "
            "is for your review only)\n\n"
            "--- Draft content ---\n\n"
            f"{content}\n\n"
            "----------------------\n\n"
            "If you're happy with it, copy the text above and post it "
            "on LinkedIn yourself. AI BrandPilot never posts "
            "automatically."
        )
        return message

    def _send(self, message: EmailMessage) -> None:
        """Open an SMTP connection and send the given message.

        Args:
            message: The fully-populated EmailMessage to send.
        """
        host: Optional[str] = settings.smtp_host
        with smtplib.SMTP(host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
