# Guardrails Pipeline — CrewAI Edition

Implements the same `guardrails.spl` pattern using CrewAI:
Multiple `Agent` instances (Safety Auditor, Helpful Assistant, Output Validator)
collaborate on `Task` objects managed by a Python-orchestrated workflow to
implement a multi-gate safety pipeline.

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
python cookbook/18_guardrails/crewai/guardrails_crewai.py \
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

Check logs in `cookbook/18_guardrails/crewai/logs-crewai`.

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
| `guardrails_crewai.py` | ~140 |

Extra lines in CrewAI come from: agent definitions (role, goal, backstory), manual
coordination of the gate logic via Python (since CrewAI lacks native branching/gate
constructs), and the implementation of deterministic PII/keyword logic. SPL's
native `EVALUATE` and `CALL` syntax, combined with its built-in tool system,
provides a more streamlined way to orchestrate these safety gates.
