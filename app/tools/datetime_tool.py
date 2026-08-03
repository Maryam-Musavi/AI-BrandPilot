"""
DateTime tool implementation.

Answers simple date/time questions (e.g. "What time is it?", "What is
today's date?", "What day is today?") using the system clock. No AI
logic, external API calls, or persistence is implemented here.
"""

import re
from datetime import datetime
from typing import Tuple

from app.tools.base_tool import BaseTool

_TIME_PATTERNS: Tuple[str, ...] = (r"\btime\b", r"\bclock\b", r"\bhour\b")
_DATE_PATTERNS: Tuple[str, ...] = (r"\bdate\b",)
_DAY_PATTERNS: Tuple[str, ...] = (r"\bday\b", r"\bweekday\b")


def _matches_any(patterns: Tuple[str, ...], text: str) -> bool:
    """Check whether any regex pattern matches the given text.

    Args:
        patterns: A tuple of regex patterns to test.
        text: The text to search within.

    Returns:
        True if at least one pattern matches, False otherwise.
    """
    return any(re.search(pattern, text) for pattern in patterns)


class DateTimeTool(BaseTool):
    """Tool that answers current date/time/day-of-week questions.

    Attributes:
        name: Short identifier for this tool.
        description: Human-readable summary of what this tool does.
    """

    name: str = "datetime_tool"
    description: str = (
        "Answers questions about the current time, date, or day of the "
        "week using the system clock."
    )

    def can_handle(self, query: str) -> bool:
        """Determine whether this tool can answer the given query.

        Args:
            query: The user's input text.

        Returns:
            True if the query appears to ask about the current time,
            date, or day of the week, False otherwise.
        """
        normalized = query.lower()
        return (
            _matches_any(_TIME_PATTERNS, normalized)
            or _matches_any(_DATE_PATTERNS, normalized)
            or _matches_any(_DAY_PATTERNS, normalized)
        )

    def execute(self, query: str) -> str:
        """Answer a date/time/day question using the current system time.

        Args:
            query: The user's input text.

        Returns:
            A natural-language answer describing the current time,
            date, and/or day, depending on what was asked. If the query
            matched but doesn't clearly specify which one, the full
            timestamp is returned instead.
        """
        normalized = query.lower()
        now = datetime.now()

        wants_time = _matches_any(_TIME_PATTERNS, normalized)
        wants_date = _matches_any(_DATE_PATTERNS, normalized)
        wants_day = _matches_any(_DAY_PATTERNS, normalized)

        if not (wants_time or wants_date or wants_day):
            return f"It is currently {now.strftime('%A, %B %d, %Y %H:%M:%S')}."

        parts = []
        if wants_time:
            parts.append(f"the time is {now.strftime('%H:%M:%S')}")
        if wants_date:
            parts.append(f"today's date is {now.strftime('%B %d, %Y')}")
        if wants_day:
            parts.append(f"today is {now.strftime('%A')}")

        return "Right now, " + ", and ".join(parts) + "."
