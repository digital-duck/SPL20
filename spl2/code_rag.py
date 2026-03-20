"""Code-RAG store for text2SPL generation.

Indexes (description, SPL source) pairs in a ChromaDB collection so that
text2SPL can retrieve semantically similar examples at compile time instead
of relying on a small set of hand-written examples.

Sources of pairs:
  - Cookbook recipes (indexed once via `spl2 code-rag index`)
  - Every validated `spl2 compile` invocation (auto-captured when enabled)

Usage:
    store = CodeRAGStore()
    store.index_recipes(cookbook_dir="./cookbook", catalog="./cookbook/cookbook_catalog.json")
    examples = store.retrieve("summarize a PDF and store the result", top_k=4)
    store.add_pair("translate email to French", spl_source, metadata={"source": "user"})
    store.export_jsonl(".spl/code_rag/training_data.jsonl")
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

_log = logging.getLogger("spl2.code_rag")

try:
    import chromadb
    from chromadb.config import Settings
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False


def _require_chroma() -> None:
    if not _CHROMA_AVAILABLE:
        raise ImportError(
            "chromadb is required for Code-RAG: pip install chromadb"
        )


class CodeRAGStore:
    """ChromaDB-backed store for (description, SPL source) pairs.

    Parameters
    ----------
    storage_dir : str
        Directory for the ChromaDB persistent database.
    collection_name : str
        ChromaDB collection name. Separate collections allow future
        isolation (e.g. per-project or per-language-version).
    """

    COLLECTION_NAME = "spl_code_rag"

    def __init__(
        self,
        storage_dir: str = ".spl/code_rag",
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        _require_chroma()
        Path(storage_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=storage_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._col = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        _log.debug("CodeRAGStore ready: %s  docs=%d", storage_dir, self._col.count())

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
        cookbook = Path(cookbook_dir)
        catalog_path = catalog_path or str(cookbook / "cookbook_catalog.json")

        with open(catalog_path, encoding="utf-8") as f:
            catalog = json.load(f)

        added = 0
        for recipe in catalog.get("recipes", []):
            rid = recipe.get("id", "??")
            name = recipe.get("name", "")
            description = recipe.get("description", "")
            category = recipe.get("category", "")
            recipe_dir = recipe.get("dir", "")

            if not description or not recipe_dir:
                continue

            # Find the .spl file in the recipe directory
            spl_files = list((cookbook / recipe_dir).glob("*.spl"))
            if not spl_files:
                _log.debug("Recipe %s (%s): no .spl file found, skipping", rid, name)
                continue

            spl_source = spl_files[0].read_text(encoding="utf-8").strip()
            doc_id = f"cookbook_{rid}"

            if self._exists(doc_id):
                _log.debug("Recipe %s already indexed, skipping", rid)
                continue

            self._col.add(
                ids=[doc_id],
                documents=[description],
                metadatas=[{
                    "spl_source": spl_source,
                    "name": name,
                    "category": category,
                    "source": "cookbook",
                    "recipe_id": rid,
                    "indexed_at": _now(),
                }],
            )
            added += 1
            _log.debug("Indexed recipe %s: %s", rid, name)

        _log.info("index_recipes: added %d new pairs (total=%d)", added, self._col.count())
        return added

    def add_pair(
        self,
        description: str,
        spl_source: str,
        metadata: dict | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Add a validated (description, SPL source) pair to the store.

        Called automatically after each successful `spl2 compile` invocation
        when auto_capture is enabled.

        Returns the doc_id used.
        """
        if not description.strip() or not spl_source.strip():
            raise ValueError("Both description and spl_source must be non-empty")

        meta = {
            "spl_source": spl_source.strip(),
            "source": "user",
            "indexed_at": _now(),
        }
        if metadata:
            meta.update(metadata)

        # Generate a stable ID from description hash if not provided
        if doc_id is None:
            import hashlib
            doc_id = "user_" + hashlib.sha1(description.encode()).hexdigest()[:12]

        # Upsert: overwrite if same description was captured before
        self._col.upsert(
            ids=[doc_id],
            documents=[description],
            metadatas=[meta],
        )
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
        if self._col.count() == 0:
            return []

        k = min(top_k, self._col.count())
        results = self._col.query(
            query_texts=[description],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        docs      = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metadatas, distances):
            hits.append({
                "description": doc,
                "spl_source":  meta.get("spl_source", ""),
                "name":        meta.get("name", ""),
                "category":    meta.get("category", ""),
                "source":      meta.get("source", ""),
                "score":       float(dist),   # cosine distance (lower = more similar)
            })

        return hits

    # ------------------------------------------------------------------
    # Inspection & export
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the total number of indexed pairs."""
        return self._col.count()

    def export_jsonl(self, output_path: str) -> int:
        """Export all pairs as JSONL for fine-tuning.

        Each line is a JSON object: {"description": "...", "spl_source": "..."}
        Returns the number of records exported.
        """
        results = self._col.get(include=["documents", "metadatas"])
        docs      = results.get("documents") or []
        metadatas = results.get("metadatas") or []

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        with out.open("w", encoding="utf-8") as f:
            for doc, meta in zip(docs, metadatas):
                record = {
                    "description": doc,
                    "spl_source": meta.get("spl_source", ""),
                    "name": meta.get("name", ""),
                    "category": meta.get("category", ""),
                    "source": meta.get("source", ""),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        _log.info("Exported %d pairs to %s", len(docs), output_path)
        return len(docs)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _exists(self, doc_id: str) -> bool:
        result = self._col.get(ids=[doc_id], include=[])
        return len(result.get("ids", [])) > 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
