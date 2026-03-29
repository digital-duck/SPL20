# RAG Query — AutoGen Edition

Implements the same `rag_query.spl` pattern using AutoGen:
deterministic index+retrieve pipeline (plain Python / FAISS) feeds context
into a single `ConversableAgent` that generates the answer — mirroring
SPL's `CALL rag.query(...)` → `GENERATE answer(question)` flow.

Note: SPL's `CALL` (zero LLM tokens, deterministic) vs `GENERATE` (probabilistic)
is a language-level distinction. AutoGen has no such primitive — both retrieval
and generation are plain Python; the programmer must enforce the distinction manually.

## Setup

```bash
conda create -n autogen python=3.11 -y
conda activate autogen
pip install pyautogen langchain-ollama langchain-community faiss-cpu
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
python cookbook/08_rag_query/autogen/rag_autogen.py \
    --doc /path/to/doc.md \
    --question "Who is Wen?"

python cookbook/08_rag_query/autogen/rag_autogen.py \
    --doc /path/to/doc.md \
    --question "What is Momagrid and why was it built?" \
    --model llama3.2 \
    --log-dir cookbook/08_rag_query/autogen/logs
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
| `rag_autogen.py` | 66 |

Extra lines come from: `_build_index` and `_retrieve` helpers, `llm_config` dict,
proxy + assistant `ConversableAgent` instantiation, `initiate_chat` wiring,
and `argparse` boilerplate. The CALL/GENERATE distinction — free in SPL —
requires manual structuring in AutoGen.
