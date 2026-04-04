# Data Extraction — AutoGen Edition

Implements the same `data_extraction.spl` pattern using AutoGen:
an `Extractor` agent is provided with a JSON schema and noisy text, and tasked
with extracting structured fields in a single turn.

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
python cookbook/27_data_extraction/autogen/data_extraction_autogen.py \
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

Check logs in `cookbook/27_data_extraction/autogen/logs-autogen`.

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
| `data_extraction_autogen.py` | ~100 |

Extra lines in AutoGen come from: manual JSON schema definitions in Python
(which SPL handles with `CREATE FUNCTION`), agent initialization with explicit
system messages, and the boilerplate for argument parsing. SPL's native
support for structured functions and integrated generation makes data
extraction much more concise.
