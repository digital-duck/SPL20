"""Persistent memory and prompt-cache store for SPL 2.0.

  kv_store    — SQLite-backed key-value store for memory.get()/set()
  prompt_cache — dd-cache DiskCache for LLM response caching (TTL-aware)

The two stores are intentionally separate:
  - kv_store  : long-lived workflow state, no expiry
  - prompt_cache: ephemeral LLM result cache, expires after cache_ttl seconds
"""

from __future__ import annotations
import os
import sqlite3
from datetime import datetime


class MemoryStore:
    """Persistent memory and prompt-cache store for SPL 2.0."""

    def __init__(self, db_path: str = ".spl/memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        # Prompt cache via dd-cache DiskCache (separate SQLite file)
        cache_path = os.path.join(os.path.dirname(db_path) or ".", "prompt_cache.db")
        from dd_cache import DiskCache
        self._cache: DiskCache = DiskCache(path=cache_path)

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # Key-value store (workflow memory)                                   #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Prompt cache (dd-cache DiskCache)                                   #
    # ------------------------------------------------------------------ #

    def cache_get(self, prompt_hash: str) -> str | None:
        """Return cached LLM result for prompt_hash, or None if absent/expired."""
        entry = self._cache.get(prompt_hash)
        if entry is None:
            return None
        return entry.get("result") if isinstance(entry, dict) else str(entry)

    def cache_set(
        self,
        prompt_hash: str,
        result: str,
        model: str = "",
        tokens_used: int = 0,
        ttl: int | None = None,
        # Legacy parameter kept for call-site compat; ignored (use ttl instead)
        expires_at: str | None = None,
    ) -> None:
        """Cache an LLM result with optional TTL (seconds)."""
        self._cache.set(
            prompt_hash,
            {"result": result, "model": model, "tokens_used": tokens_used},
            ttl=ttl,
        )

    def close(self):
        self._conn.close()
