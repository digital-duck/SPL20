"""StorageConnection — dd-db backed key-value store for SPL STORAGE params.

Wraps dd_db adapters to provide a uniform get/set interface used by
STORAGE-typed workflow inputs:

    @memory STORAGE(sqlite, '.spl/memory.db')

    @profile      := @memory['chat_user_profile']   -- read
    @memory['chat_user_profile'] := @profile        -- write

Supported backends (matching dd-db adapter names):
  sqlite   — SQLiteDB  (default; stdlib only, zero extra deps)
  duckdb   — DuckDB
  postgres — PostgresDB
"""

from __future__ import annotations

import logging
import os

_log = logging.getLogger(__name__)

_KV_TABLE = "spl_kv"
_INIT_DDL = f"""
CREATE TABLE IF NOT EXISTS {_KV_TABLE} (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


class StorageConnection:
    """Key-value wrapper around a dd-db adapter.

    Parameters
    ----------
    backend : str
        One of 'sqlite', 'duckdb', 'postgres'.
    path : str
        File path for file-based backends (sqlite, duckdb) or
        DSN / host string for server backends.
    """

    def __init__(self, backend: str, path: str):
        self.backend = backend.lower()
        self.path = path
        self._db = self._connect()
        self._ensure_table()

    # ------------------------------------------------------------------
    # Connection bootstrap
    # ------------------------------------------------------------------

    def _connect(self):
        if self.backend == "sqlite":
            from dd_db import SQLiteDB
            resolved = os.path.expanduser(self.path)
            os.makedirs(os.path.dirname(resolved) or ".", exist_ok=True)
            db = SQLiteDB(resolved)
            db.connect()
            return db
        if self.backend == "duckdb":
            from dd_db import DuckDB
            db = DuckDB(os.path.expanduser(self.path))
            db.connect()
            return db
        if self.backend in ("postgres", "postgresql"):
            from dd_db import PostgresDB
            # path is expected to be 'host/dbname' or just 'host'
            host, _, dbname = self.path.partition("/")
            db = PostgresDB(host=host, database=dbname or "spl")
            db.connect()
            return db
        raise ValueError(
            f"Unsupported STORAGE backend: {self.backend!r}. "
            "Supported: sqlite, duckdb, postgres"
        )

    def _ensure_table(self) -> None:
        self._db.run_query(_INIT_DDL)

    # ------------------------------------------------------------------
    # Key-value API
    # ------------------------------------------------------------------

    def get(self, key: str) -> str:
        """Return value for key, or '' if absent."""
        df = self._db.run_query(
            f"SELECT value FROM {_KV_TABLE} WHERE key = :key",
            params={"key": key},
        )
        if df is None or df.empty:
            return ""
        return str(df.iloc[0]["value"])

    def set(self, key: str, value: str) -> None:
        """Upsert a key-value pair."""
        self._db.run_query(
            f"""INSERT INTO {_KV_TABLE} (key, value, updated_at)
                VALUES (:key, :value, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value      = excluded.value,
                    updated_at = excluded.updated_at""",
            params={"key": key, "value": value},
        )
        _log.debug("STORAGE set %r (%d chars)", key, len(value))

    def delete(self, key: str) -> bool:
        """Delete a key; returns True if a row was removed."""
        df = self._db.run_query(
            f"DELETE FROM {_KV_TABLE} WHERE key = :key",
            params={"key": key},
        )
        if df is None or df.empty:
            return False
        return int(df.iloc[0].get("rows_affected", 0)) > 0

    def list_keys(self) -> list[str]:
        """Return all keys sorted by most-recently updated."""
        df = self._db.run_query(
            f"SELECT key FROM {_KV_TABLE} ORDER BY updated_at DESC"
        )
        if df is None or df.empty:
            return []
        return df["key"].tolist()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        try:
            self._db.disconnect()
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"StorageConnection(backend={self.backend!r}, path={self.path!r})"
