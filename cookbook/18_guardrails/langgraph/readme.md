# Guardrails Pipeline — LangGraph Edition

Implements the same `guardrails.spl` pattern using LangGraph:
a state graph that implements a multi-gate safety pipeline including keyword
pre-screening, LLM-based input classification, deterministic PII detection and
redaction, safe generation, and final output validation.

## Setup

```bash
pip install langgraph langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/18_guardrails/langgraph/guardrails_langgraph.py \
    --user-input "My SSN is 123-45-6789, help me file taxes"
```

## Validate

Expected console output pattern:
```
Gate 1a: Keyword pre-screen ...
Gate 1b: LLM input classification ...
Gate 2: PII detection & redaction ...
Gate 3: Safe generation ...
Gate 4: Output validation ...

============================================================
STATUS: complete
RESPONSE:
[REDACTED-SSN] ...
```

Check logs in `cookbook/18_guardrails/langgraph/logs-langgraph`.

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
| `guardrails_langgraph.py` | ~180 |

Extra lines in LangGraph come from: state definition, node functions, manual integration
of the regex and keyword logic (which SPL handles via `CALL` to external tools),
and the graph wiring with conditional edges. SPL's native `EVALUATE` and `CALL`
constructs make the multi-gate logic very concise.
