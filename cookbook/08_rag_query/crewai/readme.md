# RAG Query — CrewAI Edition

Implements the same `rag_query.spl` pattern using CrewAI:
a `@tool` decorator wraps the deterministic FAISS retrieval; a single
LLM `Agent` calls that tool and generates the answer via its ReAct loop —
mirroring SPL's `CALL rag.query(...)` → `GENERATE answer(question)` flow.

Note: SPL's `CALL` (zero LLM tokens, deterministic) vs `GENERATE` (probabilistic)
is a language-level distinction. CrewAI has no such primitive — both tool calls
and LLM reasoning are handled by the same Agent's ReAct loop uniformly.

## Setup

```bash
conda create -n crewai python=3.11 -y
conda activate crewai
pip install crewai langchain-ollama langchain-community faiss-cpu
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
python cookbook/08_rag_query/crewai/rag_crewai.py \
    --doc /path/to/doc.md \
    --question "Who is Wen?"

python cookbook/08_rag_query/crewai/rag_crewai.py \
    --doc /path/to/doc.md \
    --question "What is Momagrid and why was it built?" \
    --model llama3.2 \
    --log-dir cookbook/08_rag_query/crewai/logs
```

## Validate

Expected console output pattern:
```
Indexing document | /path/to/doc.md ...
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
| `rag_crewai.py` | 73 |

Extra lines come from: module-level `_store` + `_build_index` for index management,
`@tool` decorator with required docstring, `Agent`/`Task`/`Crew` object construction,
and `argparse` boilerplate. SPL's `rag.query(...)` is a single declarative
expression; CrewAI requires explicit tool definition, agent wiring, and task spec.
