# Recipe 13: Map-Reduce Summarizer

Handles documents too large for a single context window by splitting into chunks (map), summarizing each independently, then combining into a final summary (reduce).

## Pattern

```
chunk_plan(document) → N chunks
  └─► MAP: summarize_chunk(chunk_i) for i in 0..N
        └─► REDUCE: reduce_summaries(all_summaries, style)
              └─► quality_score → refine if score ≤ 0.7
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `document` | TEXT | *(required)* | Full document text to summarize |
| `style` | TEXT | *(required)* | Output style (e.g. `bullet points`, `executive brief`, `narrative`) |

## Usage

```bash
spl2 run cookbook/13_map_reduce/map_reduce.spl --adapter ollama \
    document="$(cat large_doc.txt)" \
    style="bullet points"

spl2 run cookbook/13_map_reduce/map_reduce.spl --adapter ollama \
    document="$(cat README.md)" \
    style="executive brief"

# Inline text
spl2 run cookbook/13_map_reduce/map_reduce.spl --adapter ollama \
    document="Artificial intelligence has transformed..." \
    style="narrative"
```

## Output status

| Status | Meaning |
|---|---|
| `complete` | Quality score > 0.7, committed directly |
| `refined` | Quality was low, one refinement pass applied |
| `partial` | Context too long even for chunking |
| `budget_limit` | Token budget exceeded during reduce |
