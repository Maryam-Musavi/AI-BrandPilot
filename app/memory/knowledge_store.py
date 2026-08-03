"""
Knowledge memory (RAG store).

Persists ingested documents and their embedded chunks in a dedicated
SQLite file (memory/knowledge.db), kept entirely separate from business
memory (memory/database.py: posts, topics, agent_logs). The two have
different lifecycles: business memory should never be recreated, while
the knowledge base can be safely wiped and rebuilt at any time by
re-running ingestion.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "knowledge.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
"""


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        The current UTC timestamp formatted as an ISO-8601 string.
    """
    return datetime.now(timezone.utc).isoformat()


class KnowledgeStore:
    """SQLite-backed store for ingested documents and their chunks.

    Each public method opens and closes its own short-lived connection,
    the same simple-and-safe pattern used by memory/database.py.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize the store, creating the file and schema if needed.

        Args:
            db_path: Path to the SQLite database file. Defaults to
                memory/knowledge.db (alongside this module).
        """
        self.db_path: Path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        """Open a new connection with row-as-dict access and FKs enabled.

        Returns:
            A sqlite3.Connection configured with sqlite3.Row as the row
            factory and foreign key enforcement turned on.
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_schema(self) -> None:
        """Create the documents and chunks tables if they don't exist."""
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    # ------------------------------------------------------------------
    # documents
    # ------------------------------------------------------------------

    def get_document_hash(self, source: str) -> Optional[str]:
        """Fetch the stored content hash for a document source, if any.

        Used to make ingestion idempotent: callers compare this against
        a freshly computed hash to decide whether re-embedding is needed.

        Args:
            source: The document's unique source identifier (e.g. a
                file path, or "post:123" for a generated post).

        Returns:
            The stored content hash, or None if this source has never
            been ingested.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT content_hash FROM documents WHERE source = ?",
                (source,),
            ).fetchone()
            return row["content_hash"] if row else None

    def upsert_document(self, source: str, content_hash: str) -> int:
        """Insert a new document, or update an existing one's hash.

        If a document with this source already exists, its content_hash
        and ingested_at are updated and its existing chunks are deleted
        (the caller is expected to insert fresh chunks afterward via
        `replace_chunks`).

        Args:
            source: The document's unique source identifier.
            content_hash: The freshly computed content hash.

        Returns:
            The document's id (new or existing).
        """
        now = _utc_now_iso()
        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT id FROM documents WHERE source = ?", (source,)
            )
            existing = cursor.fetchone()

            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO documents (source, content_hash, ingested_at)
                    VALUES (?, ?, ?)
                    """,
                    (source, content_hash, now),
                )
                return int(cursor.lastrowid)

            document_id = int(existing["id"])
            connection.execute(
                """
                UPDATE documents SET content_hash = ?, ingested_at = ?
                WHERE id = ?
                """,
                (content_hash, now, document_id),
            )
            connection.execute(
                "DELETE FROM chunks WHERE document_id = ?", (document_id,)
            )
            return document_id

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all ingested documents.

        Returns:
            A list of document dicts (id, source, content_hash,
            ingested_at), most recently ingested first.
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY ingested_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_document(self, source: str) -> None:
        """Delete a document and its chunks by source.

        Args:
            source: The document's unique source identifier.
        """
        with self._connect() as connection:
            connection.execute("DELETE FROM documents WHERE source = ?", (source,))

    # ------------------------------------------------------------------
    # chunks
    # ------------------------------------------------------------------

    def replace_chunks(
        self, document_id: int, chunks: Sequence[Tuple[str, List[float]]]
    ) -> None:
        """Replace all chunks for a document with a new set.

        Args:
            document_id: The document these chunks belong to.
            chunks: An ordered sequence of (chunk_text, embedding_vector)
                pairs.
        """
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM chunks WHERE document_id = ?", (document_id,)
            )
            connection.executemany(
                """
                INSERT INTO chunks (document_id, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (document_id, index, content, json.dumps(embedding))
                    for index, (content, embedding) in enumerate(chunks)
                ],
            )

    def list_all_chunks(self) -> List[Dict[str, Any]]:
        """List every chunk across all documents, with embeddings decoded.

        Returns:
            A list of dicts, each shaped as:
            {"id", "document_id", "source", "chunk_index", "content",
             "embedding": List[float]}.
        """
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chunks.id, chunks.document_id, documents.source,
                       chunks.chunk_index, chunks.content, chunks.embedding
                FROM chunks
                JOIN documents ON documents.id = chunks.document_id
                """
            ).fetchall()

        results = []
        for row in rows:
            entry = dict(row)
            entry["embedding"] = json.loads(entry["embedding"])
            results.append(entry)
        return results

    def count_chunks(self) -> int:
        """Return the total number of chunks stored across all documents.

        Useful for quickly checking whether the knowledge base has any
        content at all before attempting retrieval.

        Returns:
            The total chunk count.
        """
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()
            return int(row["n"])
