"""FAISS + SQLite vector store for SPL 2.0 RAG support.

Stores document embeddings in a FAISS index and metadata in a SQLite database.
Falls back gracefully when numpy/faiss are not installed.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import Path

_log = logging.getLogger("spl2.storage.vector")

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore[assignment]


def _default_embedding_fn(text: str, dim: int = 384):
    """Character-level hash embedding: deterministic, no external model needed.

    Produces a normalized float32 vector of the given dimensionality.
    """
    if np is None:
        raise ImportError("numpy is required for vector operations: pip install numpy")
    vec = np.zeros(dim, dtype=np.float32)
    for i, ch in enumerate(text):
        idx = (hash(ch) + i * 31) % dim
        vec[idx] += float(ord(ch))
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


class VectorStore:
    """FAISS-backed vector store with SQLite metadata.

    Parameters
    ----------
    storage_dir : str
        Directory for persisting index and metadata files.
    embedding_dim : int
        Dimensionality of embedding vectors.
    embedding_fn : callable | None
        Function ``(text) -> np.ndarray[float32]``.  Falls back to a simple
        character-level hash embedding when *None*.
    """

    def __init__(
        self,
        storage_dir: str = ".spl",
        embedding_dim: int = 384,
        embedding_fn=None,
    ):
        if faiss is None:
            raise ImportError(
                "faiss is required for VectorStore: pip install faiss-cpu"
            )
        if np is None:
            raise ImportError(
                "numpy is required for VectorStore: pip install numpy"
            )

        self.storage_dir = storage_dir
        self.embedding_dim = embedding_dim
        self.embedding_fn = embedding_fn or (lambda t: _default_embedding_fn(t, embedding_dim))

        self._index_path = os.path.join(storage_dir, "vectors.faiss")
        self._meta_path = os.path.join(storage_dir, "vectors_meta.db")

        os.makedirs(storage_dir, exist_ok=True)

        # Initialise FAISS index
        if os.path.exists(self._index_path):
            self._index = faiss.read_index(self._index_path)
        else:
            self._index = faiss.IndexFlatL2(embedding_dim)

        # Initialise SQLite metadata store
        self._conn = sqlite3.connect(self._meta_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                text     TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                embedding_model TEXT NOT NULL DEFAULT 'char_hash',
                tokens   INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, text: str, metadata: dict | None = None) -> int:
        """Embed *text*, store in FAISS + SQLite, and return the document id."""
        vec = self.embedding_fn(text)
        vec = np.asarray(vec, dtype=np.float32).reshape(1, -1)

        self._index.add(vec)

        meta_json = json.dumps(metadata or {})
        now = datetime.now(timezone.utc).isoformat()
        tokens = len(text.split())

        cur = self._conn.execute(
            "INSERT INTO documents (text, metadata, tokens, created_at) VALUES (?, ?, ?, ?)",
            (text, meta_json, tokens, now),
        )
        self._conn.commit()
        doc_id = cur.lastrowid

        self._persist_index()
        return doc_id

    def add_batch(self, texts: list[str], metadatas: list[dict] | None = None) -> list[int]:
        """Bulk-add multiple documents. Returns list of doc ids."""
        if metadatas is None:
            metadatas = [{}] * len(texts)
        if len(metadatas) != len(texts):
            raise ValueError("texts and metadatas must have the same length")

        vecs = np.vstack(
            [np.asarray(self.embedding_fn(t), dtype=np.float32).reshape(1, -1) for t in texts]
        )
        self._index.add(vecs)

        now = datetime.now(timezone.utc).isoformat()
        doc_ids: list[int] = []
        for text, meta in zip(texts, metadatas):
            tokens = len(text.split())
            cur = self._conn.execute(
                "INSERT INTO documents (text, metadata, tokens, created_at) VALUES (?, ?, ?, ?)",
                (text, json.dumps(meta), tokens, now),
            )
            doc_ids.append(cur.lastrowid)
        self._conn.commit()

        self._persist_index()
        return doc_ids

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Search for the *top_k* most similar documents.

        Returns a list of dicts with keys: id, text, metadata, tokens, score.
        """
        if self._index.ntotal == 0:
            return []

        vec = np.asarray(self.embedding_fn(text), dtype=np.float32).reshape(1, -1)
        k = min(top_k, self._index.ntotal)
        distances, indices = self._index.search(vec, k)

        results: list[dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            # FAISS uses 0-based indexing; DB uses 1-based (doc_id = idx + 1)
            doc_id = int(idx) + 1
            row = self._conn.execute(
                "SELECT text, metadata, tokens FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()
            if row is None:
                continue
            results.append(
                {
                    "id": doc_id,
                    "text": row[0],
                    "metadata": json.loads(row[1]),
                    "tokens": row[2],
                    "score": float(dist),
                }
            )
        return results

    def count(self) -> int:
        """Return the number of stored documents."""
        return self._index.ntotal

    def delete(self, doc_id: int) -> bool:
        """Delete a document by id.

        Note: FAISS ``IndexFlatL2`` does not support removal, so this only
        removes the metadata row.  A future implementation could rebuild the
        index periodically.
        """
        cur = self._conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def close(self):
        """Persist index and close the database connection."""
        self._persist_index()
        self._conn.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist_index(self):
        faiss.write_index(self._index, self._index_path)
