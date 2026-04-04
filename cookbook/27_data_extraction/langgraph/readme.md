# Data Extraction — LangGraph Edition

Implements the same `data_extraction.spl` pattern using LangGraph:
a state graph that selects a JSON schema based on a format (general, invoice, contract)
and uses an LLM to extract structured fields from noisy text.

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
python cookbook/27_data_extraction/langgraph/data_extraction_langgraph.py \
    --text "Please process payment of USD 4,250.00 to Riverside Consulting (ref: PO-8821) by end of March."
```

## Validate

Expected console output pattern:
```
Extracting data using format 'general' ...

============================================================
EXTRACTED DATA:
{
  "names": [],
  "organizations": [
    "Riverside Consulting"
  ],
  "dates": [
    {
      "value": "end of March",
      "label": "payment due"
    }
  ],
  "amounts": [
    {
      "value": 4250.0,
      "currency": "USD",
      "label": "payment amount"
    }
  ],
  "references": [
    "PO-8821"
  ],
  "locations": []
}
```

Check logs in `cookbook/27_data_extraction/langgraph/logs-langgraph`.

## SPL equivalent

```bash
spl run cookbook/27_data_extraction/data_extraction.spl \
    --adapter ollama -m gemma3 \
    text="Please process payment of USD 4,250.00 to Riverside Consulting (ref: PO-8821) by end of March."
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `data_extraction.spl` | ~45 |
| `data_extraction_langgraph.py` | ~110 |

Extra lines in LangGraph come from: state definition, node function, manual JSON
schema definitions in Python (which SPL handles via `CREATE FUNCTION`), and the
boilerplate for argument parsing and graph orchestration. SPL's `GENERATE`
with its schema integration allows for much more concise data extraction.
