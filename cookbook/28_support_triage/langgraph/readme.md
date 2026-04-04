# Support Triage — LangGraph Edition

Implements the same `support_triage.spl` pattern using LangGraph:
a state graph that extracts order numbers, looks up order context, classifies the
ticket, extracts structured details, detects urgency, and either escalates or
drafts a grounded response with a quality-check/revision loop.

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
python cookbook/28_support_triage/langgraph/support_triage_langgraph.py \
    --ticket "My account has been charged twice for order #ORD-12345"
```

## Validate

Expected console output pattern:
```
Extracting order numbers and looking up context ...
Classifying ticket ...
Extracting structured details ...
Detecting urgency ...
Drafting response ...
Checking draft quality ...
Finalizing response ...

============================================================
STATUS: drafted
RESULT:
Dear [Name], I understand you've been charged twice for order ORD-12345...
```

Check logs in `cookbook/28_support_triage/langgraph/logs-langgraph`.

## SPL equivalent

```bash
spl run cookbook/28_support_triage/support_triage.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/28_support_triage/tools.py \
    ticket="My account has been charged twice for order #ORD-12345"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `support_triage.spl` | ~100 |
| `support_triage_langgraph.py` | ~250 |

Extra lines in LangGraph come from: state definition, node functions, manual tool
integration (regex and file-based lookup), and graph wiring with conditional
edges. SPL's integrated tool system and native procedural control flow
significantly reduce the orchestration overhead for this complex pipeline.
