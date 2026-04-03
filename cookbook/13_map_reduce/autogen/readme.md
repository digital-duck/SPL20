# Map-Reduce — AutoGen Edition

Implements the same `map_reduce.spl` pattern using AutoGen (pyautogen):
a set of `ConversableAgent`s (Summarizer, Aggregator, Critic, Improver) 
orchestrated by a manual Python loop.

## Setup

```bash
pip install pyautogen
```

Requires Ollama running locally with OpenAI-compatible endpoint:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/13_map_reduce/autogen/map_reduce_autogen.py \
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
Done. Saved to cookbook/13_map_reduce/logs-autogen/final_summary.md
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
| `map_reduce_autogen.py` | ~110 |

Extra lines come from: explicit agent construction with `llm_config`, 
explicit orchestration of `initiate_chat` per chunk, and 
manual extraction of the final message from the chat history. 
AutoGen is optimized for multi-agent conversations; for structured workflows 
like Map-Reduce, much of the orchestration must be handled in plain Python.
