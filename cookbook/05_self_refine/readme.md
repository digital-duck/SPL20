# Recipe 05: Self-Refine

Iteratively improves an LLM output through a critique-and-refine loop.
Each iteration critiques the current draft; if the critique judges it
satisfactory the loop commits early, otherwise it generates a refined version
and continues. The loop is capped by `@max_iterations` (default 5).

## Pattern

```
draft(task)
  └─► critique(current)
        ├─ satisfactory → COMMIT (early exit)
        └─ needs work  → refined(current, feedback) → next iteration
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | TEXT | *(required)* | The writing or generation task |
| `max_iterations` | INT | `5` | Maximum refinement cycles before committing best effort |

## Usage

### Minimal — use all defaults
```bash
spl2 run cookbook/05_self_refine/self_refine.spl \
    --adapter ollama \
    task="Write a haiku about coding"
```

### Custom iteration limit
```bash
spl2 run cookbook/05_self_refine/self_refine.spl \
    --adapter ollama \
    task="Write a haiku about coding" \
    max_iterations=3
```

### With a different model
```bash
spl2 run cookbook/05_self_refine/self_refine.spl \
    --adapter ollama -m llama3.2 \
    task="Explain recursion in one paragraph" \
    max_iterations=4
```

### Via Claude Code CLI
```bash
spl2 run cookbook/05_self_refine/self_refine.spl \
    --adapter claude_cli -m claude-sonnet-4-6 \
    task="Write an executive summary of the benefits of SPL - Structured Prompt Language" \
    max_iterations=3
```

## Output status

| Status | Meaning |
|---|---|
| `complete` | Critique judged output satisfactory before hitting the limit |
| `max_iterations` | Loop ran to completion; best effort committed |
| `partial` | `MaxIterationsReached` exception caught |
| `budget_limit` | Token budget exceeded during refinement |
