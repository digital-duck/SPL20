# Plan and Execute — CrewAI Edition

Implements the same `plan_execute.spl` pattern using CrewAI:
Three `Agent` instances (`Senior Software Architect`, `Senior Software Engineer`, `Technical Judge`)
collaborate on a series of `Task` objects managed by a Python-orchestrated loop
to handle planning, step-by-step execution with validation, and file generation.

## Setup

```bash
pip install crewai langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

## Run

```bash
# From SPL20/ root
python cookbook/12_plan_and_execute/crewai/plan_execute_crewai.py \
    --task "Build a simple URL shortener in Python" \
    --output-dir "cookbook/12_plan_and_execute/crewai/output"
```

## Validate

Expected console output pattern:
```
Planning task: Build a simple URL shortener in Python ...
Executing step 0/5: ...
Executing step 1/5: ...
...
Outlining files ...
Generating file 0/3: ...
  Written 1 file(s): models.py
Generating file 1/3: ...
  Written 1 file(s): app.py
...
Summarizing ...

============================================================
FINAL REPORT:
<summary report text>
```

Check output files in `cookbook/12_plan_and_execute/crewai/output`.
Check logs in `cookbook/12_plan_and_execute/crewai/logs-crewai`.

## SPL equivalent

```bash
spl run cookbook/12_plan_and_execute/plan_execute.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/12_plan_and_execute/tools.py \
    task="Build a simple URL shortener in Python" \
    output_dir="cookbook/12_plan_and_execute/output"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `plan_execute.spl` | ~130 |
| `plan_execute_crewai.py` | ~160 |

Extra lines in CrewAI come from: detailed agent and task definitions (role, goal, backstory),
manual Python-based loop and state management (since CrewAI lacks native looping syntax),
and the implementation of the `write_code_files` utility.
SPL's native `WHILE` and `EVALUATE` constructs, combined with its concise `GENERATE`
and `CALL` syntax, allow for a more streamlined representation of this complex workflow.
