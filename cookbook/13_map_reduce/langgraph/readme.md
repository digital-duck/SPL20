# Map-Reduce — LangGraph Edition

Implements the same `map_reduce.spl` pattern using LangGraph:
a state graph with nodes for planning, summarizing (map), aggregating (reduce), 
quality checking, and improving.

## Setup

```bash
pip install langgraph langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/13_map_reduce/langgraph/map_reduce_langgraph.py \
    --document "$(cat cookbook/13_map_reduce/large_doc.txt)" \
    --style "bullet points"
```

## Validate

Expected console output pattern:
```
Plan: splitting document into 4 chunks
Map: summarizing chunk 0/4
Map: summarizing chunk 1/4
...
Reduce: combining summaries
Quality Check: scoring final summary
Score: 0.85
Commit: saving final summary to cookbook/13_map_reduce/logs-langgraph/final_summary.md
```

## SPL equivalent

```bash
spl run cookbook/13_map_reduce/map_reduce.spl \
    --adapter ollama -m gemma3 --tools cookbook/13_map_reduce/tools.py \
    document="$(cat cookbook/13_map_reduce/large_doc.txt)" \
    style="bullet points"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `map_reduce.spl` | ~60 |
| `map_reduce_langgraph.py` | ~130 |

Extra lines come from: explicit `TypedDict` state, node functions, graph wiring, 
prompt templates (which SPL handles via functions), and `argparse` boilerplate. 
The dynamic nature of Map-Reduce (looping over chunks) requires `conditional_edges` 
in LangGraph to mirror SPL's simple `WHILE` loop.
