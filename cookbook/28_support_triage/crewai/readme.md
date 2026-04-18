# Support Triage — CrewAI Edition

Implements the same `support_triage.spl` pattern using CrewAI:
Multiple `Agent` instances (Triage Specialist, Data Extractor, Support Drafter, Quality Auditor)
collaborate on a series of `Task` objects managed by a Python-orchestrated loop
to implement a grounded support triage and response pipeline.

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
python cookbook/28_support_triage/crewai/support_triage_crewai.py \
    --ticket "My account has been charged twice for order #ORD-12345"
```

## Validate

Expected console output pattern:
```
Preprocessing ...
Classifying ...
Extracting details ...
Detecting urgency ...
Drafting response ...
Checking quality ...

============================================================
STATUS: drafted
Dear [Name], I understand you've been charged twice for order ORD-12345...
```

Check logs in `cookbook/28_support_triage/crewai/logs-crewai`.

## SPL equivalent

```bash
spl run cookbook/28_support_triage/support_triage.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/28_support_triage/tools.py \
    ticket="My account has been charged twice for order #ORD-12345"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `support_triage.spl` | ~100 |
| `support_triage_crewai.py` | ~170 |

Extra lines in CrewAI come from: detailed agent and task definitions (role, goal, backstory),
manual Python-based loop and tool coordination, and the boilerplate for kicking off
individual tasks via `Crew`. SPL's native `WORKFLOW` and `GENERATE` syntax, combined
with its integrated tool system, provide a more direct and cohesive way to express
this data-intensive support pipeline.
