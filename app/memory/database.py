"""
Long-term business memory.

Stores durable, cross-session data the LinkedIn workflow needs to avoid
repetition and track its own history: generated posts, topic usage, and
agent action logs. Backed by a local SQLite file (no external database
server), which fits the "runs entirely locally" deployment requirement.

This is intentionally separate from app/memory/conversation_memory.py,
which remains the RAM-only, short-term store for interactive chat turns.
Chat memory is NOT migrated into SQLite in this sprint.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "brandpilot.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    published_at TEXT,
    engagement TEXT
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL UNIQUE,
    used_count INTEGER NOT NULL DEFAULT 0,
    last_used TEXT
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
"""


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        The current UTC timestamp formatted as an ISO-8601 string.
    """
    return datetime.now(timezone.utc).isoformat()


class Database:
    """SQLite-backed long-term memory for posts, topics, and agent logs.

    Each public method opens and closes its own short-lived connection,
    which is the simplest safe pattern for SQLite under low/moderate
    concurrency (e.g. a scheduler process and an API process both
    reading/writing occasionally).
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize the database, creating the file and schema if needed.

        Args:
            db_path: Path to the SQLite database file. Defaults to
                memory/brandpilot.db (alongside this module).
        """
        self.db_path: Path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        """Open a new connection with row-as-dict access enabled.

        Returns:
            A sqlite3.Connection configured with sqlite3.Row as the row
            factory, so query results can be read like dicts.
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        """Create the posts, topics, and agent_logs tables if missing."""
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    # ------------------------------------------------------------------
    # posts
    # ------------------------------------------------------------------

    def create_post(
        self, topic: str, content: str, status: str = "draft"
    ) -> int:
        """Insert a new post record.

        Args:
            topic: The topic the post is about.
            content: The post's text content (may be empty for an idea
                that has not been drafted yet).
            status: The post's lifecycle status (e.g. "idea", "draft",
                "pending_approval", "approved", "published"). Defaults
                to "draft".

        Returns:
            The newly created post's id.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO posts (topic, content, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (topic, content, status, _utc_now_iso()),
            )
            return int(cursor.lastrowid)

    def update_post_content(
        self, post_id: int, content: str, status: Optional[str] = None
    ) -> None:
        """Update a post's content and, optionally, its status.

        Args:
            post_id: The id of the post to update.
            content: The new content text.
            status: The new status, if it should change. Left unchanged
                if None.
        """
        with self._connect() as connection:
            if status is None:
                connection.execute(
                    "UPDATE posts SET content = ? WHERE id = ?",
                    (content, post_id),
                )
            else:
                connection.execute(
                    "UPDATE posts SET content = ?, status = ? WHERE id = ?",
                    (content, status, post_id),
                )

    def update_post_status(
        self, post_id: int, status: str, published_at: Optional[str] = None
    ) -> None:
        """Update a post's status and, optionally, its published_at time.

        Args:
            post_id: The id of the post to update.
            status: The new status (e.g. "approved", "published").
            published_at: An ISO-8601 timestamp to record as when the
                post was published. Left unchanged if None.
        """
        with self._connect() as connection:
            if published_at is None:
                connection.execute(
                    "UPDATE posts SET status = ? WHERE id = ?",
                    (status, post_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE posts SET status = ?, published_at = ?
                    WHERE id = ?
                    """,
                    (status, published_at, post_id),
                )

    def update_post_engagement(self, post_id: int, engagement: str) -> None:
        """Record engagement data for a post.

        Args:
            post_id: The id of the post to update.
            engagement: A representation of engagement data (e.g. a JSON
                string of likes/comments/shares). Stored as-is.
        """
        with self._connect() as connection:
            connection.execute(
                "UPDATE posts SET engagement = ? WHERE id = ?",
                (engagement, post_id),
            )

    def get_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single post by id.

        Args:
            post_id: The id of the post to fetch.

        Returns:
            The post as a dict, or None if no post with that id exists.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM posts WHERE id = ?", (post_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_posts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List posts, optionally filtered by status.

        Args:
            status: If provided, only posts with this status are
                returned. All posts are returned if None.

        Returns:
            A list of post dicts, most recently created first.
        """
        with self._connect() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM posts ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM posts WHERE status = ?
                    ORDER BY created_at DESC
                    """,
                    (status,),
                ).fetchall()
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # topics
    # ------------------------------------------------------------------

    def record_topic_used(self, topic: str) -> None:
        """Record that a topic has just been used, updating its stats.

        Increments the topic's used_count and sets its last_used time,
        inserting a new row if the topic hasn't been seen before.

        Args:
            topic: The topic that was used.
        """
        now = _utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO topics (topic, used_count, last_used)
                VALUES (?, 1, ?)
                ON CONFLICT(topic) DO UPDATE SET
                    used_count = used_count + 1,
                    last_used = excluded.last_used
                """,
                (topic, now),
            )

    def get_topic_usage(self, topic: str) -> Optional[Dict[str, Any]]:
        """Fetch usage stats for a single topic.

        Args:
            topic: The topic to look up.

        Returns:
            A dict with the topic's stats, or None if the topic has
            never been used.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM topics WHERE topic = ?", (topic,)
            ).fetchone()
            return dict(row) if row else None

    def list_topics(self) -> List[Dict[str, Any]]:
        """List all known topics and their usage stats.

        Returns:
            A list of topic dicts, most recently used first.
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM topics ORDER BY last_used DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # agent_logs
    # ------------------------------------------------------------------

    def log_agent_action(self, agent_name: str, action: str) -> int:
        """Record an action taken by an agent.

        Args:
            agent_name: The name of the agent that acted (e.g.
                "ResearchAgent", "ContentAgent", "LinkedInAgent").
            action: A short description of the action taken.

        Returns:
            The newly created log entry's id.
        """
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO agent_logs (agent_name, action, timestamp)
                VALUES (?, ?, ?)
                """,
                (agent_name, action, _utc_now_iso()),
            )
            return int(cursor.lastrowid)

    def list_agent_logs(
        self, agent_name: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List recent agent actions, optionally filtered by agent name.

        Args:
            agent_name: If provided, only logs from this agent are
                returned. All agents' logs are returned if None.
            limit: The maximum number of log entries to return.

        Returns:
            A list of log dicts, most recent first.
        """
        with self._connect() as connection:
            if agent_name is None:
                rows = connection.execute(
                    "SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM agent_logs WHERE agent_name = ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (agent_name, limit),
                ).fetchall()
            return [dict(row) for row in rows]
