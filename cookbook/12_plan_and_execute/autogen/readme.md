# Plan and Execute — AutoGen Edition

Implements the same `plan_execute.spl` pattern using AutoGen:
Three `ConversableAgent` instances (`Planner`, `Executor`, `Validator`) are coordinated
by a Python script to manage the planning, execution, and file generation workflow.

## Setup

```bash
pip install pyautogen
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

## Run

```bash
# From SPL20/ root
python cookbook/12_plan_and_execute/autogen/plan_execute_autogen.py \
    --task "Build a simple URL shortener in Python" \
    --output-dir "cookbook/12_plan_and_execute/autogen/output"
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

Check output files in `cookbook/12_plan_and_execute/autogen/output`.
Check logs in `cookbook/12_plan_and_execute/autogen/logs-autogen`.

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
| `plan_execute_autogen.py` | ~150 |

Extra lines in AutoGen come from: agent initialization with explicit system messages,
manualCoordination of the workflow steps (which SPL handles with `WORKFLOW` and `WHILE`),
regex-based step extraction, and the implementation of the file writing logic.
SPL's native support for structured workflows and integrated tool calling results in
a more cohesive and compact implementation.
