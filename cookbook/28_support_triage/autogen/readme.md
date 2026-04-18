# Support Triage — AutoGen Edition

Implements the same `support_triage.spl` pattern using AutoGen:
Multiple specialized agents (Classifier, Extractor, Urgency, Drafter, Checker, Refiner)
are coordinated by a Python script alongside deterministic order lookup tools to
implement a full customer support triage and response pipeline.

## Setup

```bash
pip install pyautogen
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/28_support_triage/autogen/support_triage_autogen.py \
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

Check logs in `cookbook/28_support_triage/autogen/logs-autogen`.

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
| `support_triage_autogen.py` | ~160 |

Extra lines in AutoGen come from: agent definitions with explicit system messages,
manual coordination of the procedural steps, regex/lookup logic, and the boilerplate
for JSON parsing. SPL's native `WORKFLOW` and `GENERATE` constructs provide a
more compact and readable way to orchestrate these complex, data-grounded steps.
