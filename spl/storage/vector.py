"""FAISS + SQLite vector store for SPL 2.0 RAG support.

Stores document embeddings in a FAISS index and metadata in a SQLite database.

Embedding priority:
  1. sentence-transformers (semantic, recommended) — pip install sentence-transformers
  2. Character-level hash (fallback, no external deps, poor semantic quality)

The embedding model used is persisted in the store's config table so the same
model is always used for a given index (mixing models corrupts retrieval).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Callable

_log = logging.getLogger("spl.storage.vector")

try:
    import numpy as _numpy  # noqa: F401
    _NP_AVAILABLE = True
except ImportError:
    _NP_AVAILABLE = False

try:
    import faiss as _faiss  # noqa: F401
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False


def _np():
    """Return numpy — guaranteed non-None after VectorStore.__init__ guard."""
    import numpy
    return numpy


def _fi():
    """Return faiss — guaranteed non-None after VectorStore.__init__ guard."""
    import faiss
    return faiss

# Module-level cache: model_name → SentenceTransformer instance
_ST_MODEL_CACHE: dict[str, object] = {}

DEFAULT_ST_MODEL = "all-MiniLM-L6-v2"  # 384-dim, fast, high quality


def _load_sentence_transformer(model_name: str):
    """Load (and cache) a SentenceTransformer model, always on CPU."""
    if model_name not in _ST_MODEL_CACHE:
        import warnings
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
        _log.info("Loading sentence-transformers model: %s (device=cpu)", model_name)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _ST_MODEL_CACHE[model_name] = SentenceTransformer(model_name, device="cpu")
    return _ST_MODEL_CACHE[model_name]


def _make_st_embedding_fn(model_name: str) -> Callable[[str], object]:
    """Return an embedding function backed by a SentenceTransformer model."""
    def embed(text: str):
        model = _load_sentence_transformer(model_name)
        return model.encode(text, normalize_embeddings=True)
    return embed


def _char_hash_embedding(text: str, dim: int = 384):
    """Character-level hash embedding: deterministic fallback, no external deps."""
    np = _np()
    vec = np.zeros(dim, dtype=np.float32)
    for i, ch in enumerate(text):
        idx = (hash(ch) + i * 31) % dim
        vec[idx] += float(ord(ch))
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec


def _sentence_transformers_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _resolve_embedding(model_name: str | None, dim: int) -> tuple[Callable, str, int]:
    """Return (embedding_fn, model_label, actual_dim).

    If model_name is 'char_hash' or sentence-transformers is unavailable,
    falls back to the char-hash function.
    """
    if model_name and model_name != "char_hash" and _sentence_transformers_available():
        fn = _make_st_embedding_fn(model_name)
        # Infer dim from a test encode
        test_vec = _np().asarray(fn("test"), dtype=_np().float32)
        return fn, model_name, int(test_vec.shape[0])
    # Fallback
    if model_name and model_name != "char_hash":
        _log.warning(
            "sentence-transformers not installed; falling back to char_hash embedding. "
            "Install with: pip install sentence-transformers"
        )
    return (lambda t: _char_hash_embedding(t, dim)), "char_hash", dim


class VectorStore:
    """FAISS-backed vector store with SQLite metadata.

    Parameters
    ----------
    storage_dir : str
        Directory for persisting index and metadata files.
    embedding_model : str | None
        Sentence-transformers model name (e.g. ``"all-MiniLM-L6-v2"``).
        Pass ``"char_hash"`` to force the legacy fallback.
        Defaults to ``all-MiniLM-L6-v2`` when sentence-transformers is installed,
        otherwise falls back to char_hash automatically.
    """

    def __init__(
        self,
        storage_dir: str = ".spl",
        embedding_model: str | None = None,
        # Legacy parameter kept for backwards compat — ignored when embedding_model is set
        embedding_dim: int = 384,
        embedding_fn: Callable | None = None,
    ):
        if not _FAISS_AVAILABLE:
            raise ImportError(
                "faiss is required for VectorStore: pip install faiss-cpu"
            )
        if not _NP_AVAILABLE:
            raise ImportError(
                "numpy is required for VectorStore: pip install numpy"
            )
        self.storage_dir = storage_dir
        self._index_path = os.path.join(storage_dir, "vectors.faiss")
        self._meta_path = os.path.join(storage_dir, "vectors_meta.db")
        os.makedirs(storage_dir, exist_ok=True)

        # Initialise SQLite (schema + config table)
        self._conn = sqlite3.connect(self._meta_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                text     TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                embedding_model TEXT NOT NULL DEFAULT 'char_hash',
                tokens   INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

        # Resolve which embedding to use
        if embedding_fn is not None:
            # Caller-supplied function (legacy path)
            self.embedding_fn = embedding_fn
            self._model_name = "custom"
            self._embedding_dim = embedding_dim
        else:
            stored_model = self._get_config("embedding_model")
            if stored_model:
                # Existing store — must use the same model
                requested = embedding_model or DEFAULT_ST_MODEL
                if embedding_model and embedding_model != stored_model:
                    _log.warning(
                        "Requested model %r but store was built with %r; "
                        "using stored model. Reset the store to switch models.",
                        embedding_model, stored_model,
                    )
                self.embedding_fn, self._model_name, self._embedding_dim = \
                    _resolve_embedding(stored_model, embedding_dim)
            else:
                # New store — choose model
                requested = embedding_model or DEFAULT_ST_MODEL
                self.embedding_fn, self._model_name, self._embedding_dim = \
                    _resolve_embedding(requested, embedding_dim)
                self._set_config("embedding_model", self._model_name)

        _log.info("VectorStore embedding: %s (dim=%d)", self._model_name, self._embedding_dim)

        # Initialise FAISS index
        fi = _fi()
        if os.path.exists(self._index_path):
            self._index = fi.read_index(self._index_path)
        else:
            self._index = fi.IndexFlatIP(self._embedding_dim)  # inner-product (cosine for normalised vecs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, text: str, metadata: dict | None = None) -> int:
        """Embed *text*, store in FAISS + SQLite, and return the document id."""
        np = _np()
        vec = np.asarray(self.embedding_fn(text), dtype=np.float32).reshape(1, -1)
        self._index.add(vec)  # type: ignore[arg-type]

        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO documents (text, metadata, embedding_model, tokens, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (text, json.dumps(metadata or {}), self._model_name, len(text.split()), now),
        )
        self._conn.commit()
        self._persist_index()
        return cur.lastrowid or 0

    def add_batch(self, texts: list[str], metadatas: list[dict] | None = None) -> list[int]:
        """Bulk-add multiple documents. Returns list of doc ids."""
        if metadatas is None:
            metadatas = [{}] * len(texts)
        if len(metadatas) != len(texts):
            raise ValueError("texts and metadatas must have the same length")

        np = _np()
        vecs = np.vstack(
            [np.asarray(self.embedding_fn(t), dtype=np.float32).reshape(1, -1) for t in texts]
        )
        self._index.add(vecs)  # type: ignore[arg-type]

        now = datetime.now(timezone.utc).isoformat()
        doc_ids: list[int] = []
        for text, meta in zip(texts, metadatas):
            cur = self._conn.execute(
                "INSERT INTO documents (text, metadata, embedding_model, tokens, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (text, json.dumps(meta), self._model_name, len(text.split()), now),
            )
            doc_ids.append(int(cur.lastrowid or 0))
        self._conn.commit()
        self._persist_index()
        return doc_ids

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Search for the *top_k* most similar documents.

        Returns a list of dicts with keys: id, text, metadata, tokens, score.
        Scores are cosine similarities (higher = more similar) for sentence-transformer
        embeddings, L2 distances (lower = more similar) for char_hash.
        """
        if self._index.ntotal == 0:
            return []

        np = _np()
        vec = np.asarray(self.embedding_fn(text), dtype=np.float32).reshape(1, -1)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(vec, k)  # type: ignore[arg-type]

        results: list[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            # FAISS uses 0-based insertion order; use OFFSET for non-sequential ids.
            row = self._conn.execute(
                "SELECT id, text, metadata, tokens FROM documents ORDER BY id LIMIT 1 OFFSET ?",
                (int(idx),),
            ).fetchone()
            if row is None:
                continue
            results.append(
                {
                    "id": row[0],
                    "text": row[1],
                    "metadata": json.loads(row[2]),
                    "tokens": row[3],
                    "score": float(score),
                }
            )
        # For cosine (IndexFlatIP), higher score = better. Already sorted descending by FAISS.
        return results

    def count(self) -> int:
        """Return the number of stored documents."""
        return self._index.ntotal

    def delete(self, doc_id: int) -> bool:
        """Remove a document's metadata. Note: FAISS IndexFlatIP does not support
        in-place removal; the vector remains in the index but will be unreachable
        after the metadata row is deleted."""
        cur = self._conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def close(self):
        """Persist index and close the database connection."""
        self._persist_index()
        self._conn.close()

    @property
    def model_name(self) -> str:
        return self._model_name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _persist_index(self):
        _fi().write_index(self._index, self._index_path)

    def _get_config(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM config WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def _set_config(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
        )
        self._conn.commit()
