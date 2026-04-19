"""
memory.py — SQLite-backed conversation memory for April.
Stores all messages persistently so April remembers you across restarts.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

from config import DB_PATH

logger = logging.getLogger("April.Memory")


class ConversationMemory:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
        logger.info(f"Memory database ready: {self.db_path}")

    # ─── Setup ───────────────────────────────────────────────────────────────
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id     INTEGER NOT NULL,
                    role        TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
                    content     TEXT    NOT NULL,
                    created_at  TEXT    DEFAULT (datetime('now'))
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)"
            )
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ─── Write ───────────────────────────────────────────────────────────────
    def add_message(self, chat_id: int, role: str, content: str):
        """Save a message to the database."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content),
            )
            conn.commit()

    def clear_history(self, chat_id: int):
        """Delete all messages for a chat."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            conn.commit()

    # ─── Read ────────────────────────────────────────────────────────────────
    def get_history(self, chat_id: int, limit: int = 30) -> List[Dict[str, str]]:
        """
        Return the last `limit` messages in chronological order,
        formatted for the Groq/OpenAI messages array.
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT role, content
                FROM (
                    SELECT role, content, id
                    FROM messages
                    WHERE chat_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
                """,
                (chat_id, limit),
            )
            rows = cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def get_message_count(self, chat_id: int) -> int:
        """Return total messages stored for a chat."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)
            )
            return cursor.fetchone()[0]

    def get_stats(self, chat_id: int) -> Dict:
        """Return memory statistics for a chat."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) AS user_count,
                    SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) AS assistant_count,
                    MIN(created_at) AS oldest,
                    MAX(created_at) AS latest
                FROM messages
                WHERE chat_id = ?
                """,
                (chat_id,),
            )
            row = cursor.fetchone()

        return {
            "total": row["total"] or 0,
            "user_count": row["user_count"] or 0,
            "assistant_count": row["assistant_count"] or 0,
            "oldest": row["oldest"],
            "latest": row["latest"],
        }
