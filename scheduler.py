"""
Scheduler entrypoint for autonomous LinkedIn workflows.

This is deliberately NOT a long-running in-process scheduler and does
not depend on any scheduling library (APScheduler, Celery beat, etc.),
per Sprint 11 scope. Instead, it is meant to be invoked once per day by
an external OS-level scheduler (cron, systemd timer, Windows Task
Scheduler, ...). Each run checks today's weekday, runs the matching
LinkedIn workflow step (if any) via LinkedInAgent, logs the outcome, and
exits.

Example crontab entry (runs once daily at 09:00 server time):

    0 9 * * * cd /path/to/AI-BrandPilot && python scheduler.py >> logs/scheduler.log 2>&1

Weekly plan (Sprint 11):
    Monday    -> generate_post_idea()   (research + pick a topic)
    Wednesday -> generate_post_draft()  (write the draft, save for approval)

All other days: no-op.
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

MONDAY = 0
WEDNESDAY = 2


def run_monday_workflow(agent: LinkedInAgent) -> None:
    """Run the Monday step: research and select this week's topic.

    Args:
        agent: The LinkedInAgent to run the workflow against.
    """
    result = agent.generate_post_idea()
    logger.info(
        "Monday workflow complete: post_id=%s topic=%r",
        result["post_id"],
        result["brief"]["topic"],
    )


def run_wednesday_workflow(agent: LinkedInAgent) -> None:
    """Run the Wednesday step: draft content for this week's topic.

    Args:
        agent: The LinkedInAgent to run the workflow against.
    """
    result = agent.generate_post_draft()
    logger.info(
        "Wednesday workflow complete: post_id=%s topic=%r status=%s "
        "(awaiting human approval)",
        result["post_id"],
        result["topic"],
        result["status"],
    )


_WEEKDAY_TASKS: Dict[int, Callable[[LinkedInAgent], None]] = {
    MONDAY: run_monday_workflow,
    WEDNESDAY: run_wednesday_workflow,
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
