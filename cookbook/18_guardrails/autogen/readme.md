# Guardrails Pipeline — AutoGen Edition

Implements the same `guardrails.spl` pattern using AutoGen:
Multiple agents (Classifier, Helper, Validator) are coordinated by a Python script
alongside deterministic keyword and PII filters to implement a multi-gate safety pipeline.

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
python cookbook/18_guardrails/autogen/guardrails_autogen.py \
    --user-input "My SSN is 123-45-6789, help me file taxes"
```

## Validate

Expected console output pattern:
```
Gate 1a: Keyword pre-screen ...
Gate 1b: LLM input classification ...
Gate 2: PII redaction ...
Gate 3: Safe generation ...
Gate 4: Output validation ...

============================================================
RESPONSE:
[REDACTED-SSN] ...
```

Check logs in `cookbook/18_guardrails/autogen/logs-autogen`.

## SPL equivalent

```bash
spl run cookbook/18_guardrails/guardrails.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/18_guardrails/tools.py \
    user_input="My SSN is 123-45-6789, help me file taxes"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `guardrails.spl` | ~75 |
| `guardrails_autogen.py` | ~130 |

Extra lines in AutoGen come from: agent definitions with explicit system messages,
manual coordination of the gate logic (which SPL handles with `WORKFLOW` and `EVALUATE`),
and the implementation of the deterministic PII/keyword filters. SPL's integrated
`EVALUATE` and `CALL` syntax allow for a much more direct and compact implementation
of the safety pipeline.
