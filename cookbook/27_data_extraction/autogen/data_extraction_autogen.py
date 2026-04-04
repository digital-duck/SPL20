"""
AutoGen equivalent of data_extraction.spl

One Extractor agent uses a schema-constrained prompt to extract structured
data from messy text.

Usage:
    pip install pyautogen
    python cookbook/27_data_extraction/autogen/data_extraction_autogen.py \
        --text "Please process payment of USD 4,250.00 to Riverside Consulting (ref: PO-8821) by end of March."
"""

import argparse
import json
from pathlib import Path

from autogen import ConversableAgent


# ── Schemas ───────────────────────────────────────────────────────────────────

SCHEMAS = {
    "invoice": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "vendor":         {"type": "string"},
            "amount":         {"type": "number"},
            "currency":       {"type": "string", "default": "USD"},
            "issue_date":     {"type": "string", "format": "date"},
            "due_date":       {"type": "string", "format": "date"},
            "line_items":     {"type": "array", "items": {"type": "object", "properties": {"description": {"type": "string"}, "amount": {"type": "number"}}}},
            "payment_terms":  {"type": "string"},
            "po_reference":   {"type": "string"}
        }
    },
    "contract": {
        "type": "object",
        "properties": {
            "parties":        {"type": "array", "items": {"type": "string"}},
            "effective_date": {"type": "string", "format": "date"},
            "expiry_date":    {"type": "string", "format": "date"},
            "value":          {"type": "number"},
            "currency":       {"type": "string"},
            "jurisdiction":   {"type": "string"},
            "key_obligations":{"type": "array", "items": {"type": "string"}}
        }
    },
    "general": {
        "type": "object",
        "properties": {
            "names":        {"type": "array", "items": {"type": "string"}},
            "organizations":{"type": "array", "items": {"type": "string"}},
            "dates":        {"type": "array", "items": {"type": "object", "properties": {"value": {"type": "string"}, "label": {"type": "string"}}}},
            "amounts":      {"type": "array", "items": {"type": "object", "properties": {"value": {"type": "number"}, "currency": {"type": "string"}, "label": {"type": "string"}}}},
            "references":   {"type": "array", "items": {"type": "string"}},
            "locations":    {"type": "array", "items": {"type": "string"}}
        }
    }
}


# ── Agent system messages ─────────────────────────────────────────────────────

EXTRACTOR_SYSTEM = """\
You are a data extraction specialist. Extract all relevant fields from the text and return valid JSON matching the schema exactly.
If a field is not present in the text, omit it. Return only the JSON object."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(text: str, format_name: str, model: str, log_dir: str) -> dict:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    extractor = ConversableAgent("Extractor", system_message=EXTRACTOR_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")

    schema = SCHEMAS.get(format_name, SCHEMAS["general"])
    print(f"Extracting data using format '{format_name}' ...")
    
    reply = extractor.generate_reply(messages=[{
        "content": f"Text: {text}\n\nSchema:\n{json.dumps(schema, indent=2)}",
        "role": "user"
    }])
    
    res = str(reply).strip()
    if res.startswith("```json"):
        res = res[7:-3].strip()
    elif res.startswith("```"):
        res = res[3:-3].strip()
        
    try:
        data = json.loads(res)
    except:
        data = {"raw_output": res}
        
    _write(f"{log_dir}/extracted_{format_name}.json", json.dumps(data, indent=2))
    return data


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Data Extraction — AutoGen edition")
    p.add_argument("--text",   required=True)
    p.add_argument("--format", default="general", choices=["general", "invoice", "contract"])
    p.add_argument("--model",  default="gemma3")
    p.add_argument("--log-dir", default="cookbook/27_data_extraction/autogen/logs-autogen")
    args = p.parse_args()

    result = run(args.text, args.format, args.model, args.log_dir)
    print("\n" + "=" * 60)
    print("EXTRACTED DATA:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
