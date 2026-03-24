"""text2SPL Knowledge Studio — landing page.

Run with:
    streamlit run spl/ui/streamlit/SPL_UI.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
import db
import code_rag_bridge as rag

db.init_db()

st.set_page_config(page_title="text2SPL Studio", layout="wide")

st.title("text2SPL Knowledge Studio")
st.caption("Natural language → SPL 2.0 · Interactive compiler + knowledge accumulator")

st.markdown("""
Use the sidebar to navigate:

| Page | What it does |
|---|---|
| **Text-to-SPL** | Enter a description, compile to SPL, inspect the code, and run it |
| **Review** | Browse all generated scripts and their execution history |
| **Code-RAG** | Manage the retrieval store that improves future compilations |

Every compile and every run is saved to a local SQLite database
(`data/knowledge.db`). The Code-RAG store (ChromaDB) indexes validated
(description → SPL) pairs so the compiler can retrieve semantically similar
examples at compile time — the more pairs indexed, the better the output.
""")

st.divider()

scripts    = db.get_scripts()
executions = db.get_all_executions()
success    = sum(1 for e in executions if e["return_code"] == 0)
n_rag      = rag.count() if rag.is_available() else -1

col1, col2, col3, col4 = st.columns(4)
col1.metric("Scripts generated",    len(scripts))
col2.metric("Executions recorded",  len(executions))
col3.metric("Successful runs",      success)

if n_rag >= 0:
    col4.metric("Code-RAG pairs",   n_rag)
else:
    col4.metric("Code-RAG pairs",   "n/a", help="chromadb not installed")
