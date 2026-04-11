"""
CrewAI equivalent of data_extraction.spl

One Extraction Specialist agent performs a schema-constrained task to extract
structured data from messy text.

Usage:
    pip install crewai langchain-ollama
    python cookbook/27_data_extraction/crewai/data_extraction_crewai.py \
        --text "Please process payment of USD 4,250.00 to Riverside Consulting (ref: PO-8821) by end of March."
"""

import click
import json
from pathlib import Path

from crewai import Agent, Crew, Process, Task


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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()


# ── Main runner ───────────────────────────────────────────────────────────────

def run(text: str, format_name: str, model: str, log_dir: str) -> dict:
    llm = f"ollama/{model}"

    extractor = Agent(
        role="Extraction Specialist",
        goal=f"Extract structured data from text according to a specific JSON schema.",
        backstory="You are an expert at parsing noisy text and converting it into valid JSON format.",
        llm=llm,
        verbose=False,
    )

    schema = SCHEMAS.get(format_name, SCHEMAS["general"])
    print(f"Extracting data using format '{format_name}' ...")
    
    res = _run_task(
        extractor,
        description=f"Extract fields from the following text based on the provided schema.\nText: {text}\n\nSchema:\n{json.dumps(schema, indent=2)}\n\nReturn only the JSON object.",
        expected_output="A valid JSON object matching the schema."
    )
    
    clean_res = res.strip()
    if clean_res.startswith("```json"):
        clean_res = clean_res[7:-3].strip()
    elif clean_res.startswith("```"):
        clean_res = clean_res[3:-3].strip()
        
    try:
        data = json.loads(clean_res)
    except:
        data = {"raw_output": res}
        
    _write(f"{log_dir}/extracted_{format_name}.json", json.dumps(data, indent=2))
    return data


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--text",    required=True, help="Text to extract structured data from")
@click.option("--format",  default="general", show_default=True,
              type=click.Choice(["general", "invoice", "contract"]))
@click.option("--model",   default="gemma3", show_default=True)
@click.option("--log-dir", default="cookbook/27_data_extraction/crewai/logs-crewai", show_default=True)
def main(text: str, format: str, model: str, log_dir: str):
    result = run(text, format, model, log_dir)
    print("\n" + "=" * 60)
    print("EXTRACTED DATA:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
