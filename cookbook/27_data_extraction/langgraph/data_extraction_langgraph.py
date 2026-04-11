"""
LangGraph equivalent of data_extraction.spl

Pattern: select_schema → extract_data (one node)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/27_data_extraction/langgraph/data_extraction_langgraph.py \
        --text "Please process payment of USD 4,250.00 to Riverside Consulting (ref: PO-8821) by end of March."
"""

import click
import json
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Schemas (mirrors extraction_schema in data_extraction.spl) ───────────────

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


# ── Prompts ───────────────────────────────────────────────────────────────────

EXTRACT_PROMPT = """\
You are a data extraction specialist. Extract all relevant fields from the text and return valid JSON matching the schema exactly.
If a field is not present in the text, omit it. Return only the JSON object.

Text: {text}

Schema:
{schema}
"""


# ── State ────────────────────────────────────────────────────────────────────

class ExtractionState(TypedDict):
    text:          str
    format:        str
    model:         str
    log_dir:       str
    extracted_data: dict


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_extract(state: ExtractionState) -> dict:
    print(f"Extracting data using format '{state['format']}' ...")
    schema = SCHEMAS.get(state["format"], SCHEMAS["general"])
    res = _invoke(state["model"], EXTRACT_PROMPT.format(text=state["text"], schema=json.dumps(schema, indent=2)))
    
    # Simple JSON cleaning if the model adds markdown fences
    clean_res = res.strip()
    if clean_res.startswith("```json"):
        clean_res = clean_res[7:-3].strip()
    elif clean_res.startswith("```"):
        clean_res = clean_res[3:-3].strip()
        
    try:
        data = json.loads(clean_res)
    except:
        print("Warning: Model returned invalid JSON. Returning raw string.")
        data = {"raw_output": res}
        
    _write(f"{state['log_dir']}/extracted_{state['format']}.json", json.dumps(data, indent=2))
    return {"extracted_data": data}


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(ExtractionState)
    g.add_node("extract", node_extract)
    g.set_entry_point("extract")
    g.add_edge("extract", END)
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--text",    required=True, help="Text to extract structured data from")
@click.option("--format",  default="general", show_default=True,
              type=click.Choice(["general", "invoice", "contract"]))
@click.option("--model",   default="gemma3", show_default=True)
@click.option("--log-dir", default="cookbook/27_data_extraction/langgraph/logs-langgraph", show_default=True)
def main(text: str, format: str, model: str, log_dir: str):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "text":           text,
        "format":         format,
        "model":          model,
        "log_dir":        log_dir,
        "extracted_data": {},
    })

    print("\n" + "=" * 60)
    print("EXTRACTED DATA:")
    print(json.dumps(result["extracted_data"], indent=2))

if __name__ == "__main__":
    main()
