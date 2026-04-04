# Plan and Execute — LangGraph Edition

Implements the same `plan_execute.spl` pattern using LangGraph:
a state graph that decomposes a task, executes it step-by-step with validation
and optional replanning, outlines the necessary files, generates them individually,
and provides a final summary.

## Setup

```bash
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
python cookbook/12_plan_and_execute/langgraph/plan_execute_langgraph.py \
    --task "Build a simple URL shortener in Python" \
    --output-dir "cookbook/12_plan_and_execute/langgraph/output"
```

## Validate

Expected console output pattern:
```
Planning task: Build a simple URL shortener in Python ...
Executing step 0/5 ...
Executing step 1/5 ...
...
Outlining files to generate ...
Generating file 0/3 ...
  Written 1 file(s): models.py
Generating file 1/3 ...
  Written 1 file(s): app.py
...
Generating summary report ...

============================================================
FINAL REPORT:
<summary report text>
```

Check output files in `cookbook/12_plan_and_execute/langgraph/output`.
Check logs in `cookbook/12_plan_and_execute/langgraph/logs-langgraph`.

## SPL equivalent

```bash
spl run cookbook/12_plan_and_execute/plan_execute.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/12_plan_and_execute/tools.py \
    task="Build a simple URL shortener in Python" \
    output_dir="cookbook/12_plan_and_execute/output"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `plan_execute.spl` | ~130 |
| `plan_execute_langgraph.py` | ~230 |

Extra lines in LangGraph come from: state definition, node functions for each SPL stage,
regex-based integer extraction from LLM responses, manual state management for loops
and replanning, and the implementation of the `write_code_files` tool logic.
SPL's procedural syntax and integrated tool system significantly reduce the orchestration overhead.
