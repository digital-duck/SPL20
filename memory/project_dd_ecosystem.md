---
name: dd-* ecosystem
description: Digital-duck infrastructure repos that SPL20 should progressively adopt
type: project
---

The `~/projects/digital-duck/` workspace contains a set of shared `dd-*` infrastructure libraries. SPL20 should tighten its dependency on these over time rather than re-implementing the same abstractions.

**Already used in SPL20:**
- `dd-config` — config management (`spl/config.py` imports `from dd_config import Config`)
- `dd-logging` — structured logging (`cli.py` imports `from dd_logging import get_logger`)

**Strong candidates for future integration:**
- `dd-vectordb` — could replace the current FAISS-based doc-rag store (`spl/storage.py`)
- `dd-embed` — could power embeddings for both doc-rag and code-rag
- `dd-cache` — could replace the hand-rolled SQLite prompt cache (`spl/cache.py`)
- `dd-llm` — could serve as a unified adapter abstraction layer (currently `spl/adapters/`)
- `dd-db` — could back the Streamlit `knowledge.db` SQLite layer (`streamlit/db.py`)
- `dd-extract` — could power the `--dataset FILE` loader (PDF/CSV/etc extraction)

**How to apply:** When refactoring or adding features that touch these areas, prefer the `dd-*` library over writing new infrastructure. The goal is a tighter, shared ecosystem across all digital-duck projects.
