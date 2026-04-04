# Data Extraction — CrewAI Edition

Implements the same `data_extraction.spl` pattern using CrewAI:
an `Extraction Specialist` agent is assigned a `Data Extraction` task to
parse structured fields from noisy text using a provided JSON schema.

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
python cookbook/27_data_extraction/crewai/data_extraction_crewai.py \
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
  ...
}
```

Check logs in `cookbook/27_data_extraction/crewai/logs-crewai`.

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
| `data_extraction_crewai.py` | ~110 |

Extra lines in CrewAI come from: agent and task definitions (role, goal, backstory),
manual JSON schema definitions in Python (which SPL handles with `CREATE FUNCTION`),
and the boilerplate for kicking off tasks through a `Crew`. SPL's native support
for schema-constrained generation and structured workflows makes data
extraction much more straightforward and compact.
