"""
tools.py — Python tools for Recipe 42: Knowledge Synthesis (RAG-Writer Pattern).

Tools:
  rag_update(content, metadata)    Add new insights to the SPL RAG vector store.
  write_file(path, content)        Write text to a file (creates parent dirs).

Usage:
  spl run cookbook/42_knowledge_synthesis/knowledge_synthesis.spl \\
      --tools cookbook/42_knowledge_synthesis/tools.py \\
      --adapter ollama \\
      raw_text="Recent advances in sparse attention reduce transformer memory..."
"""

import os

from spl.tools import spl_tool


@spl_tool
def rag_update(content: str, metadata: str = "") -> str:
    """
    Add synthesized insights to the SPL RAG vector store.

    Wraps the built-in `spl2 rag add` pipeline so workflows can write back to the
    knowledge base after extracting insights.  Returns 'success:<n_chunks>' on
    success or 'error:<message>' on failure.
    """
    try:
        from spl.code_rag import CodeRAG

        rag = CodeRAG()
        doc = f"{content}\n\n{metadata}".strip() if metadata else content
        rag.add_document(doc)
        return "success:1_chunk"
    except Exception as exc:  # noqa: BLE001
        return f"error:{exc}"


@spl_tool
def write_file(path: str, content: str) -> str:
    """
    Write text content to a file, creating parent directories if needed.

    Returns 'ok:<path>' on success or 'error:<message>' on failure.
    Pass 'NONE' as path to discard output without writing.
    """
    if not path or path.upper() == "NONE":
        return "ok:discarded"
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"ok:{path}"
    except OSError as exc:
        return f"error:{exc}"
