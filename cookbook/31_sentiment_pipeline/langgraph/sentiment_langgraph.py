"""
LangGraph equivalent of sentiment.spl

Pattern: load_split → batch_sentiment → compute_stats → find_extremes → summarize_trends → assemble_report

Usage:
    pip install langgraph langchain-ollama
    python cookbook/31_sentiment_pipeline/langgraph/sentiment_langgraph.py \
        --items "Great product! | Terrible experience" --delimiter "|"
"""

import click
import json
import math
import os
from pathlib import Path
from typing import TypedDict, List, Dict, Optional

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors GENERATE blocks in sentiment.spl) ──────────────────────

BATCH_SENTIMENT_PROMPT = """\
Analyze the sentiment of each item in the list below.
Domain: {domain}

Items:
{item_list}

Return a JSON array of objects, one per item, matching this schema:
{schema}
"""

SUMMARIZE_TRENDS_PROMPT = """\
Summarize the sentiment trends based on the following statistics and extreme cases.
Domain: {domain}
Stats: {stats}
Extremes: {extremes}

Provide a concise narrative of the overall sentiment, notable patterns, and key takeaways.
"""

ASSEMBLE_REPORT_PROMPT = """\
Assemble a comprehensive sentiment analysis report.
Domain: {domain}
Results: {results}
Stats: {stats}
Trend Summary: {trend_summary}
Extremes: {extremes}

Structure the report with a summary, key metrics, notable examples, and detailed results.
"""


# ── State ────────────────────────────────────────────────────────────────────

class SentimentState(TypedDict):
    filename:      str
    items_raw:     str
    delimiter:     str
    domain:        str
    model:         str
    log_dir:       str
    
    item_list:     List[str]
    results:       List[dict]
    stats:         dict
    extremes:      dict
    trend_summary: str
    final_report:  str


# ── Deterministic Tool Logic (from tools.py) ──────────────────────────────────

def load_split_logic(filename: str, items_raw: str, delimiter: str) -> List[str]:
    text = ""
    if filename:
        path = Path(__file__).parent.parent / "reviews" / filename
        if path.exists():
            with open(path, encoding="utf-8") as f: text = f.read()
    if not text: text = items_raw
    if not text: return []
    
    if delimiter == "\\n": delimiter = "\n"
    parts = [p.strip() for p in text.split(delimiter)]
    return [p for p in parts if p]

def compute_stats_logic(results: List[dict]) -> dict:
    if not results: return {}
    labels = ["positive", "negative", "neutral", "mixed"]
    counts = {l: 0 for l in labels}
    scores = []; confs = []
    for item in results:
        label = (item.get("label") or "neutral").lower()
        if label in counts: counts[label] += 1
        else: counts["neutral"] += 1
        if isinstance(item.get("score"), (int, float)): scores.append(float(item["score"]))
        if isinstance(item.get("confidence"), (int, float)): confs.append(float(item["confidence"]))
    
    def _s(v):
        if not v: return {"mean": 0, "min": 0, "max": 0}
        m = sum(v)/len(v)
        return {"mean": round(m, 3), "min": round(min(v), 3), "max": round(max(v), 3)}
    
    return {
        "total": len(results),
        "label_counts": counts,
        "score": _s(scores),
        "confidence": _s(confs),
        "sentiment_ratio": round(counts["positive"] / max(1, counts["negative"]), 2)
    }

def find_extremes_logic(results: List[dict]) -> dict:
    if not results: return {}
    scored = [r for r in results if isinstance(r.get("score"), (int, float))]
    if not scored: return {}
    
    def _sum(r): return {"item": r.get("item"), "label": r.get("label"), "score": r.get("score")}
    
    most_pos = max(scored, key=lambda r: r["score"])
    most_neg = min(scored, key=lambda r: r["score"])
    mixed = [r for r in results if (r.get("label") or "").lower() == "mixed"]
    
    return {
        "most_positive": _sum(most_pos),
        "most_negative": _sum(most_neg),
        "mixed_count": len(mixed)
    }


# ── Sentiment Logic ─────────────────────────────────────────────────────────

SENTIMENT_SCHEMA = """
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "item": {"type": "string"},
      "label": {"type": "string", "enum": ["positive", "negative", "neutral", "mixed"]},
      "score": {"type": "number", "minimum": -1, "maximum": 1},
      "confidence": {"type": "number", "minimum": 0, "maximum": 1},
      "emotions": {"type": "array", "items": {"type": "string"}},
      "key_phrases": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["item", "label", "score", "confidence"]
  }
}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _parse_json(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```json"): clean = clean[7:-3].strip()
    elif clean.startswith("```"): clean = clean[3:-3].strip()
    try: return json.loads(clean)
    except: return {"raw": text}


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_load_split(state: SentimentState) -> dict:
    print("Loading and splitting items ...")
    items = load_split_logic(state["filename"], state["items_raw"], state["delimiter"])
    return {"item_list": items}

def node_batch_sentiment(state: SentimentState) -> dict:
    print(f"Running batch sentiment for {len(state['item_list'])} items ...")
    res = _invoke(state["model"], BATCH_SENTIMENT_PROMPT.format(
        domain=state["domain"], item_list=json.dumps(state["item_list"]), schema=SENTIMENT_SCHEMA
    ))
    results = _parse_json(res)
    if not isinstance(results, list): results = []
    return {"results": results}

def node_compute_stats(state: SentimentState) -> dict:
    print("Computing aggregate statistics ...")
    stats = compute_stats_logic(state["results"])
    return {"stats": stats}

def node_find_extremes(state: SentimentState) -> dict:
    print("Identifying extreme cases ...")
    extremes = find_extremes_logic(state["results"])
    return {"extremes": extremes}

def node_summarize_trends(state: SentimentState) -> dict:
    print("Generating trend narrative ...")
    res = _invoke(state["model"], SUMMARIZE_TRENDS_PROMPT.format(
        domain=state["domain"], stats=json.dumps(state["stats"]), extremes=json.dumps(state["extremes"])
    ))
    return {"trend_summary": res}

def node_assemble_report(state: SentimentState) -> dict:
    print("Assembling full report ...")
    res = _invoke(state["model"], ASSEMBLE_REPORT_PROMPT.format(
        domain=state["domain"], results=json.dumps(state["results"]),
        stats=json.dumps(state["stats"]), trend_summary=state["trend_summary"],
        extremes=json.dumps(state["extremes"])
    ))
    _write(f"{state['log_dir']}/report.md", res)
    return {"final_report": res}


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(SentimentState)
    g.add_node("load",      node_load_split)
    g.add_node("sentiment", node_batch_sentiment)
    g.add_node("stats",     node_compute_stats)
    g.add_node("extremes",  node_find_extremes)
    g.add_node("trends",    node_summarize_trends)
    g.add_node("report",    node_assemble_report)

    g.set_entry_point("load")
    g.add_edge("load", "sentiment")
    g.add_edge("sentiment", "stats")
    g.add_edge("stats", "extremes")
    g.add_edge("extremes", "trends")
    g.add_edge("trends", "report")
    g.add_edge("report", END)
    
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--filename",  default="",        show_default=True, help="File with items (one per line)")
@click.option("--items",     default="",        show_default=True, help="Inline items (use --delimiter to split)")
@click.option("--delimiter", default="\\n",     show_default=True)
@click.option("--domain",    default="general", show_default=True)
@click.option("--model",     default="gemma3",  show_default=True)
@click.option("--log-dir",   default="cookbook/31_sentiment_pipeline/langgraph/logs-langgraph", show_default=True)
def main(filename: str, items: str, delimiter: str, domain: str, model: str, log_dir: str):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "filename":      filename,
        "items_raw":     items,
        "delimiter":     delimiter,
        "domain":        domain,
        "model":         model,
        "log_dir":       log_dir,
        "item_list":     [],
        "results":       [],
        "stats":         {},
        "extremes":      {},
        "trend_summary": "",
        "final_report":  "",
    })

    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print(result["final_report"])

if __name__ == "__main__":
    main()
