"""FAISS vector store for SPL 2.0 RAG support — backed by dd-vectordb + dd-embed.

  dd-vectordb  — vector storage and similarity search (FAISSVectorDB)
  dd-embed     — text embedding (SentenceTransformerAdapter by default)

The embedding model is locked per index (vector_config.json) so the same
model is always used for a given store — mixing models corrupts retrieval.

Install:
    pip install "dd-vectordb[faiss]" "dd-embed[sentence-transformers]"
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

_log = logging.getLogger("spl.storage.vector")

DEFAULT_EMBED_PROVIDER = "sentence_transformers"
DEFAULT_EMBED_MODEL    = "all-MiniLM-L6-v2"   # 384-dim, fast, high quality
DEFAULT_EMBED_DIM      = 384


class VectorStore:
    """dd-vectordb (FAISSVectorDB) + dd-embed backed vector store.

    Public API is identical to the previous FAISS+SQLite implementation so all
    existing callers (executor, CLI) work without changes.

    Parameters
    ----------
    storage_dir : str
        Directory for persisting the FAISS index and config file.
    embedding_model : str | None
        dd-embed model name (e.g. ``"all-MiniLM-L6-v2"``).
        If omitted, defaults to ``all-MiniLM-L6-v2``.
    embed_provider : str
        dd-embed provider name (default ``"sentence_transformers"``).
        Override to use ``"ollama"``, ``"openai"``, etc.
    embedding_dim : int
        Legacy backward-compat parameter; ignored when the store already
        exists (dimension is read from the saved index).
    embedding_fn : callable | None
        Legacy backward-compat parameter; ignored (use embed_provider).
    """

    def __init__(
        self,
        storage_dir: str = ".spl",
        embedding_model: str | None = None,
        embed_provider: str = DEFAULT_EMBED_PROVIDER,
        # Legacy params kept for backward compat — ignored when embed_provider is used
        embedding_dim: int = DEFAULT_EMBED_DIM,
        embedding_fn=None,
    ):
        os.makedirs(storage_dir, exist_ok=True)
        self.storage_dir     = storage_dir
        self._index_path     = os.path.join(storage_dir, "vectors.faiss")
        self._config_path    = os.path.join(storage_dir, "vector_config.json")
        self._embed_adapter  = None   # lazy-loaded on first embed call

        # Model locking — honour what the existing store was built with
        stored_cfg = self._load_config()
        stored_model = stored_cfg.get("embedding_model")
        if stored_model:
            if embedding_model and embedding_model != stored_model:
                _log.warning(
                    "Requested model %r but store was built with %r; "
                    "using stored model. Delete the index to switch models.",
                    embedding_model, stored_model,
                )
            self._model_name     = stored_model
            self._provider       = stored_cfg.get("embed_provider", embed_provider)
            self._embedding_dim  = int(stored_cfg.get("embedding_dim", DEFAULT_EMBED_DIM))
        else:
            self._model_name     = embedding_model or DEFAULT_EMBED_MODEL
            self._provider       = embed_provider
            self._embedding_dim  = embedding_dim

        # Load existing index or create a fresh one
        from dd_vectordb.adapters.faiss_db import FAISSVectorDB
        if os.path.exists(self._index_path):
            self._db = FAISSVectorDB.load(self._index_path)
            _log.info(
                "VectorStore loaded: provider=%s model=%s dim=%d docs=%d",
                self._provider, self._model_name,
                self._db._dimension, self._db.count(),
            )
        else:
            # Probe the actual dimension from the embedding model if unknown
            if not stored_cfg:
                self._embedding_dim = self._probe_dim()
            self._db = FAISSVectorDB(dimension=self._embedding_dim, metric="cosine")
            self._save_config()
            _log.info(
                "VectorStore created: provider=%s model=%s dim=%d",
                self._provider, self._model_name, self._embedding_dim,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, text: str, metadata: dict | None = None) -> int:
        """Embed *text*, store in the FAISS index, and return the document count."""
        from dd_vectordb.models import Document
        import hashlib
        vec = self._embed(text)
        doc_id = hashlib.sha1(text.encode()).hexdigest()[:16]
        self._db.add_documents([
            Document(id=doc_id, text=text, embedding=vec.tolist(), metadata=metadata or {})
        ])
        self._db.save(self._index_path)
        return self._db.count()

    def add_batch(self, texts: list[str], metadatas: list[dict] | None = None) -> list[int]:
        """Bulk-add multiple documents. Returns list of sequential position numbers."""
        from dd_vectordb.models import Document
        import hashlib
        if metadatas is None:
            metadatas = [{}] * len(texts)
        if len(metadatas) != len(texts):
            raise ValueError("texts and metadatas must have the same length")
        vecs = self._embed_batch(texts)
        docs = [
            Document(
                id=hashlib.sha1(t.encode()).hexdigest()[:16],
                text=t,
                embedding=vecs[i].tolist(),
                metadata=metadatas[i],
            )
            for i, t in enumerate(texts)
        ]
        self._db.add_documents(docs)
        self._db.save(self._index_path)
        total = self._db.count()
        return list(range(total - len(texts) + 1, total + 1))

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Search for the *top_k* most similar documents.

        Returns a list of dicts with keys: id, text, metadata, tokens, score.
        Scores are cosine similarities (higher = more similar).
        """
        if self._db.count() == 0:
            return []
        vec = self._embed(text)
        results = self._db.search(vec.tolist(), k=top_k)
        return [
            {
                "id":       r.document.id,
                "text":     r.document.text,
                "metadata": r.document.metadata,
                "tokens":   len(r.document.text.split()),
                "score":    r.score,
            }
            for r in results
        ]

    def count(self) -> int:
        """Return the number of stored documents."""
        return self._db.count()

    def delete(self, doc_id) -> bool:
        """Remove a document by its ID. Returns True if a document was removed."""
        removed = self._db.delete([str(doc_id)])
        if removed:
            self._db.save(self._index_path)
        return removed > 0

    def close(self):
        """Persist the index to disk."""
        self._db.save(self._index_path)

    @property
    def model_name(self) -> str:
        return self._model_name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_adapter(self):
        """Lazily initialise the dd-embed adapter."""
        if self._embed_adapter is None:
            from dd_embed import get_adapter
            self._embed_adapter = get_adapter(self._provider, model_name=self._model_name)
            _log.debug("dd-embed adapter ready: %s / %s", self._provider, self._model_name)
        return self._embed_adapter

    def _embed(self, text: str):
        """Embed a single text; returns 1-D float32 numpy array."""
        import numpy as np
        result = self._get_adapter().embed([text])
        if not result.success:
            raise RuntimeError(f"dd-embed error: {result.error}")
        vec = np.asarray(result.embeddings[0], dtype=np.float32)
        # Update stored dim if this is the first embed on a fresh store
        if self._embedding_dim != vec.shape[0]:
            self._embedding_dim = int(vec.shape[0])
            self._save_config()
        return vec

    def _embed_batch(self, texts: list[str]):
        """Embed a list of texts; returns 2-D float32 numpy array (n, dim)."""
        import numpy as np
        result = self._get_adapter().embed(texts)
        if not result.success:
            raise RuntimeError(f"dd-embed batch error: {result.error}")
        return np.asarray(result.embeddings, dtype=np.float32)

    def _probe_dim(self) -> int:
        """Embed a throwaway string to discover the model's output dimension."""
        try:
            result = self._get_adapter().embed(["probe"])
            if result.success:
                return int(result.embeddings.shape[1])
        except Exception:
            pass
        return DEFAULT_EMBED_DIM

    def _load_config(self) -> dict:
        if os.path.exists(self._config_path):
            with open(self._config_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self) -> None:
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump({
                "embedding_model": self._model_name,
                "embed_provider":  self._provider,
                "embedding_dim":   self._embedding_dim,
                "created_at":      datetime.now(timezone.utc).isoformat(),
            }, f, indent=2)
