"""SQLite-backed memory store for SPL 2.0.

Provides persistent key-value storage for memory.get()/set(),
prompt caching, and workflow variable state.
"""

from __future__ import annotations
import os
import sqlite3
from datetime import datetime


class MemoryStore:
    """SQLite-backed key-value store for SPL memory operations."""

    def __init__(self, db_path: str = ".spl/memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS prompt_cache (
                prompt_hash TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                model TEXT,
                tokens_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );
        """)
        self._conn.commit()

    def get(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM kv_store WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str, tokens: int | None = None):
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            """INSERT INTO kv_store (key, value, tokens, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
                   value = excluded.value,
                   tokens = excluded.tokens,
                   updated_at = excluded.updated_at""",
            (key, value, tokens or len(value) // 4, now, now)
        )
        self._conn.commit()

    def delete(self, key: str) -> bool:
        cursor = self._conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
        self._conn.commit()
        return cursor.rowcount > 0

    def list_keys(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT key FROM kv_store ORDER BY updated_at DESC"
        ).fetchall()
        return [row["key"] for row in rows]

    def cache_get(self, prompt_hash: str) -> str | None:
        row = self._conn.execute(
            """SELECT result FROM prompt_cache
               WHERE prompt_hash = ?
               AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)""",
            (prompt_hash,)
        ).fetchone()
        return row["result"] if row else None

    def cache_set(self, prompt_hash: str, result: str, model: str = "",
                  tokens_used: int = 0, expires_at: str | None = None):
        self._conn.execute(
            """INSERT OR REPLACE INTO prompt_cache
               (prompt_hash, result, model, tokens_used, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (prompt_hash, result, model, tokens_used, expires_at)
        )
        self._conn.commit()

    def close(self):
        self._conn.close()
