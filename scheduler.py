"""
Scheduler entrypoint for the twice-weekly LinkedIn draft workflow.

This is deliberately NOT a long-running in-process scheduler and does
not depend on any scheduling library (APScheduler, Celery beat, etc.).
Instead, it is meant to be invoked once per day by an external OS-level
scheduler (cron, systemd timer, Windows Task Scheduler, ...). Each run
checks today's weekday and, on a posting day, researches a topic,
drafts a full post, saves it with status "pending_approval", and emails
it to you for review (see app/services/notification_service.py).

Example crontab entry (runs once daily at 09:00 server time; the
script itself decides whether today is a posting day):

    0 9 * * * cd /path/to/AI-BrandPilot && python scheduler.py >> logs/scheduler.log 2>&1

Posting cadence: twice a week, Tuesday and Friday. Each run produces
ONE complete, ready-to-review draft -- so two full drafts land in your
inbox per week. Nothing is ever posted to LinkedIn automatically; you
still copy the approved text onto LinkedIn yourself. All other days
are a no-op.
"""

import logging
import sys
from datetime import datetime
from typing import Callable, Dict

from app.agent.linkedin_agent import LinkedInAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scheduler")

TUESDAY = 1
FRIDAY = 4


def run_draft_workflow(agent: LinkedInAgent) -> None:
    """Research a fresh topic, draft a full post, save it, and notify.

    Args:
        agent: The LinkedInAgent to run the workflow against.
    """
    result = agent.generate_post_draft()
    logger.info(
        "Draft workflow complete: post_id=%s topic=%r status=%s "
        "(emailed for your review -- nothing was posted automatically)",
        result["post_id"],
        result["topic"],
        result["status"],
    )


_WEEKDAY_TASKS: Dict[int, Callable[[LinkedInAgent], None]] = {
    TUESDAY: run_draft_workflow,
    FRIDAY: run_draft_workflow,
}


def main() -> int:
    """Run today's scheduled LinkedIn workflow step, if any.

    Returns:
        Process exit code: 0 on success (including "nothing scheduled
        today"), 1 if the scheduled task raised an error.
    """
    today = datetime.now().weekday()
    task = _WEEKDAY_TASKS.get(today)

    if task is None:
        logger.info("No scheduled LinkedIn workflow for today. Exiting.")
        return 0

    agent = LinkedInAgent()
    try:
        task(agent)
    except Exception:
        logger.exception("Scheduled LinkedIn workflow failed.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
