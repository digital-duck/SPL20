"""Code-RAG store for text2SPL generation — backed by dd-vectordb + dd-embed.

  dd-vectordb  — vector storage via ChromaVectorDB (persistent Chroma collection)
  dd-embed     — description embedding (SentenceTransformerAdapter, all-MiniLM-L6-v2)

Indexes (description, SPL source) pairs so that text2SPL can retrieve
semantically similar examples at compile time.

Sources of pairs:
  - Cookbook recipes (indexed once via `spl code-rag index`)
  - Every validated `spl text2spl` invocation (auto-captured when enabled)

Install:
    pip install "dd-vectordb[chroma]" "dd-embed[sentence-transformers]"

Usage:
    store = CodeRAGStore()
    store.index_recipes(cookbook_dir="./cookbook", catalog="./cookbook/cookbook_catalog.json")
    examples = store.retrieve("summarize a PDF and store the result", top_k=4)
    store.add_pair("translate email to French", spl_source, metadata={"source": "user"})
    store.export_jsonl(".spl/code_rag/training_data.jsonl")
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

_log = logging.getLogger("spl.code_rag")

_EMBED_PROVIDER = "sentence_transformers"
_EMBED_MODEL    = "all-MiniLM-L6-v2"


class CodeRAGStore:
    """dd-vectordb (ChromaVectorDB) + dd-embed backed store for (description, SPL source) pairs.

    Parameters
    ----------
    storage_dir : str
        Directory for the persistent Chroma database.
    collection_name : str
        Chroma collection name. Separate collections allow per-project isolation.
    """

    COLLECTION_NAME = "spl_code_rag"

    def __init__(
        self,
        storage_dir: str = ".spl/code_rag",
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        from dd_vectordb.adapters.chroma_db import ChromaVectorDB
        from dd_embed import get_adapter

        Path(storage_dir).mkdir(parents=True, exist_ok=True)
        self._db = ChromaVectorDB(
            collection_name=collection_name,
            persist_directory=storage_dir,
            metric="cosine",
        )
        self._embedder = get_adapter(_EMBED_PROVIDER, model_name=_EMBED_MODEL)
        _log.debug("CodeRAGStore ready: %s  docs=%d", storage_dir, self._db.count())

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_recipes(
        self,
        cookbook_dir: str = "./cookbook",
        catalog_path: str | None = None,
    ) -> int:
        """Index all cookbook recipes from the catalog.

        Each recipe contributes one (description, SPL source) pair.
        Recipes without a readable .spl file are skipped.
        Returns the number of pairs newly added (duplicates are skipped).
        """
        from dd_vectordb.models import Document

        cookbook = Path(cookbook_dir)
        catalog_path = catalog_path or str(cookbook / "cookbook_catalog.json")

        with open(catalog_path, encoding="utf-8") as f:
            catalog = json.load(f)

        to_add: list[Document] = []
        for recipe in catalog.get("recipes", []):
            rid         = recipe.get("id", "??")
            name        = recipe.get("name", "")
            description = recipe.get("description", "")
            category    = recipe.get("category", "")
            recipe_dir  = recipe.get("dir", "")

            if not description or not recipe_dir:
                continue

            spl_files = list((cookbook / recipe_dir).glob("*.spl"))
            if not spl_files:
                _log.debug("Recipe %s (%s): no .spl file found, skipping", rid, name)
                continue

            doc_id = f"cookbook_{rid}"
            if self._exists(doc_id):
                _log.debug("Recipe %s already indexed, skipping", rid)
                continue

            spl_source = spl_files[0].read_text(encoding="utf-8").strip()
            embedding  = self._embed(description)
            to_add.append(Document(
                id=doc_id,
                text=description,
                embedding=embedding,
                metadata={
                    "spl_source": spl_source,
                    "name":       name,
                    "category":   category,
                    "source":     "cookbook",
                    "recipe_id":  rid,
                    "indexed_at": _now(),
                },
            ))

        if to_add:
            self._db.add_documents(to_add)

        _log.info("index_recipes: added %d new pairs (total=%d)", len(to_add), self._db.count())
        return len(to_add)

    def add_pair(
        self,
        description: str,
        spl_source: str,
        metadata: dict | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Add a validated (description, SPL source) pair.

        Called automatically after each successful `spl text2spl` invocation
        when auto_capture is enabled. Returns the doc_id used.
        """
        from dd_vectordb.models import Document

        if not description.strip() or not spl_source.strip():
            raise ValueError("Both description and spl_source must be non-empty")

        if doc_id is None:
            doc_id = "user_" + hashlib.sha1(description.encode()).hexdigest()[:12]

        meta = {
            "spl_source": spl_source.strip(),
            "source":     "user",
            "indexed_at": _now(),
        }
        if metadata:
            meta.update(metadata)

        embedding = self._embed(description)
        self._db.add_documents([
            Document(id=doc_id, text=description, embedding=embedding, metadata=meta)
        ])
        _log.debug("add_pair: %s (id=%s)", description[:60], doc_id)
        return doc_id

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, description: str, top_k: int = 4) -> list[dict]:
        """Retrieve the top-k most similar (description, SPL) pairs.

        Returns a list of dicts with keys:
            description, spl_source, name, category, source, score
        """
        if self._db.count() == 0:
            return []

        embedding = self._embed(description)
        results   = self._db.search(embedding, k=min(top_k, self._db.count()))
        return [
            {
                "description": r.document.text,
                "spl_source":  r.document.metadata.get("spl_source", ""),
                "name":        r.document.metadata.get("name", ""),
                "category":    r.document.metadata.get("category", ""),
                "source":      r.document.metadata.get("source", ""),
                "score":       r.score,
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # Inspection & export
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the total number of indexed pairs."""
        return self._db.count()

    def export_jsonl(self, output_path: str) -> int:
        """Export all pairs as JSONL for fine-tuning.

        Each line: {"description": "...", "spl_source": "...", "name": "...", ...}
        Returns the number of records exported.
        """
        # Access the underlying Chroma collection to retrieve all documents
        raw = self._db._collection.get(include=["documents", "metadatas"])
        docs      = raw.get("documents") or []
        metadatas = raw.get("metadatas") or []

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for doc, meta in zip(docs, metadatas):
                record = {
                    "description": doc,
                    "spl_source":  meta.get("spl_source", ""),
                    "name":        meta.get("name", ""),
                    "category":    meta.get("category", ""),
                    "source":      meta.get("source", ""),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        _log.info("Exported %d pairs to %s", len(docs), output_path)
        return len(docs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        """Embed a single text; returns a flat list of floats."""
        result = self._embedder.embed([text])
        if not result.success:
            raise RuntimeError(f"dd-embed error: {result.error}")
        return result.embeddings[0].tolist()

    def _exists(self, doc_id: str) -> bool:
        results = self._db.get_by_ids([doc_id])
        return results[0] is not None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
