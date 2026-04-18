# Chain of Thought — LangGraph Edition

Implements the same `chain.spl` pattern using LangGraph:
a `StateGraph` with four nodes (`research → analyze → summarize → commit`)
connected by linear edges. No conditional routing needed — this is a
pure sequential pipeline.

## Setup

```bash
conda create -n langgraph python=3.11 -y
conda activate langgraph
pip install langgraph langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

## Run

```bash
# From SPL20/ root
python cookbook/09_chain_of_thought/langgraph/chain_langgraph.py \
    --topic "distributed AI inference"

# Custom model
python cookbook/09_chain_of_thought/langgraph/chain_langgraph.py \
    --topic "quantum computing" \
    --model llama3.2 \
    --log-dir cookbook/09_chain_of_thought/langgraph/logs
```

## Validate

Expected console output pattern:
```
Step 1 | researching ...
Step 2 | analyzing ...
Step 3 | summarizing ...
Committed | status=complete
============================================================
<final summary text>
```

Check log files written to `--log-dir`:
```
logs/research.md   ← Step 1 output
logs/analysis.md   ← Step 2 output
logs/summary.md    ← Step 3 output
logs/final.md      ← committed output
```

## SPL equivalent

```bash
spl run cookbook/09_chain_of_thought/chain.spl \
    --adapter ollama --model gemma3 \
    topic="distributed AI inference"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `chain.spl` | 14 |
| `chain_langgraph.py` | 60 |

Extra lines come from: explicit `TypedDict` state definition, node functions,
graph wiring (`add_node` / `add_edge`), and the `argparse` boilerplate that
`spl run` handles automatically. The linear graph (no conditional edges) makes
this the simplest LangGraph pattern — 4× overhead even for a pure sequential pipeline.
