# RAG Query — LangGraph Edition

Implements the same `rag_query.spl` pattern using LangGraph:
a `StateGraph` with a combined index+retrieve node (deterministic) feeding
a single LLM `generate` node, then a `commit` node — mirroring SPL's
`CALL rag.query(...)` → `GENERATE answer(question)` flow.

Note: SPL's `CALL` (zero LLM tokens, deterministic) vs `GENERATE` (probabilistic)
is a language-level distinction. LangGraph has no such primitive — all nodes are
Python functions; the programmer must manually track which steps invoke the LLM.

## Setup

```bash
conda create -n langgraph python=3.11 -y
conda activate langgraph
pip install langgraph langchain-ollama langchain-community faiss-cpu
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
ollama pull nomic-embed-text
```

## Run

```bash
# From SPL20/ root
python cookbook/08_rag_query/langgraph/rag_langgraph.py \
    --doc /path/to/doc.md \
    --question "Who is Wen?"

python cookbook/08_rag_query/langgraph/rag_langgraph.py \
    --doc /path/to/doc.md \
    --question "What is Momagrid and why was it built?" \
    --model llama3.2 \
    --log-dir cookbook/08_rag_query/langgraph/logs
```

## Validate

Expected console output pattern:
```
Indexing document | /path/to/doc.md ...
Retrieving context | top_k=3 ...
Generating answer ...
Committed | status=complete
============================================================
<answer in plain prose>
```

## SPL equivalent

```bash
spl doc-rag add /path/to/doc.md
spl run cookbook/08_rag_query/rag_query.spl --adapter ollama \
    question="Who is Wen?"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `rag_query.spl` | 6 |
| `rag_langgraph.py` | 78 |

Extra lines come from: explicit `TypedDict` state, 3 node functions, graph wiring,
`_build_index` helper, `_write` helper, and `argparse` boilerplate. SPL's
`rag.query(...)` call encapsulates the entire index+retrieve pipeline in a single
declarative expression — free in SPL, requiring 10+ lines in LangGraph.
