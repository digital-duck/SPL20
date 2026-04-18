# Map-Reduce — CrewAI Edition

Implements the same `map_reduce.spl` pattern using CrewAI:
a set of `Agent`s (Summarizer, Editor, Quality Control, Professional Writer)
orchestrated by a manual Python loop.

## Setup

```bash
pip install crewai langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/13_map_reduce/crewai/map_reduce_crewai.py \
    --document "$(cat cookbook/13_map_reduce/large_doc.txt)" \
    --style "bullet points"
```

## Validate

Expected console output pattern:
```
Plan: 4 chunks
Map: Chunk 0/4
...
Reduce: Aggregating...
Quality Check: Scoring...
Score: 0.8
Done. Saved to cookbook/13_map_reduce/logs-crewai/final_summary.md
```

## SPL equivalent

```bash
spl run cookbook/13_map_reduce/map_reduce.spl \
    --adapter ollama --model gemma3 --tools cookbook/13_map_reduce/tools.py \
    document="$(cat cookbook/13_map_reduce/large_doc.txt)" \
    style="bullet points"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `map_reduce.spl` | ~60 |
| `map_reduce_crewai.py` | ~120 |

Extra lines come from: Agent and Task construction, `Crew` instance creation 
per iteration (CrewAI is generally designed for static crews of tasks), 
explicit Python loops, and verbose boilerplate. SPL's `WHILE` loop is a much 
more natural way to handle the dynamic number of chunks in Map-Reduce.
