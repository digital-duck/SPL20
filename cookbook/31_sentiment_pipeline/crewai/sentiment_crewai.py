"""
CrewAI equivalent of sentiment.spl

Multiple Agents (Analyst, Trend Specialist, Report Writer) collaborate on a
batch sentiment analysis pipeline managed by a Python-orchestrated flow.

Usage:
    pip install crewai langchain-ollama
    python cookbook/31_sentiment_pipeline/crewai/sentiment_crewai.py \
        --items "Great product! | Terrible experience" --delimiter "|"
"""

import click
import json
import math
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Deterministic Tool Logic ──────────────────────────────────────────────────

def load_split_logic(filename: str, items_raw: str, delimiter: str) -> list[str]:
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

def compute_stats_logic(results: list[dict]) -> dict:
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
    return {"total": len(results), "label_counts": counts, "score": _s(scores), "confidence": _s(confs), "sentiment_ratio": round(counts["positive"] / max(1, counts["negative"]), 2)}

def find_extremes_logic(results: list[dict]) -> dict:
    if not results: return {}
    scored = [r for r in results if isinstance(r.get("score"), (int, float))]
    if not scored: return {}
    def _sum(r): return {"item": r.get("item"), "label": r.get("label"), "score": r.get("score")}
    most_pos = max(scored, key=lambda r: r["score"])
    most_neg = min(scored, key=lambda r: r["score"])
    mixed = [r for r in results if (r.get("label") or "").lower() == "mixed"]
    return {"most_positive": _sum(most_pos), "most_negative": _sum(most_neg), "mixed_count": len(mixed)}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()

def _parse_json(text: str) -> list[dict]:
    clean = text.strip()
    if clean.startswith("```json"): clean = clean[7:-3].strip()
    elif clean.startswith("```"): clean = clean[3:-3].strip()
    try: res = json.loads(clean); return res if isinstance(res, list) else []
    except: return []


# ── Main runner ───────────────────────────────────────────────────────────────

def run(filename: str, items_raw: str, delimiter: str, domain: str, model: str, log_dir: str) -> str:
    llm = f"ollama/{model}"

    analyst = Agent(
        role="Sentiment Analyst",
        goal="Perform detailed sentiment analysis on a batch of items.",
        backstory="You are a data analyst specializing in natural language processing and sentiment detection.",
        llm=llm,
        verbose=False,
    )
    specialist = Agent(
        role="Trend Specialist",
        goal="Synthesize sentiment statistics into a meaningful trend narrative.",
        backstory="You excel at finding patterns in data and explaining them in plain language.",
        llm=llm,
        verbose=False,
    )
    writer = Agent(
        role="Report Writer",
        goal="Assemble final sentiment reports based on analysis results and summaries.",
        backstory="You are a professional writer who crafts structured, data-driven reports.",
        llm=llm,
        verbose=False,
    )

    # Preprocess
    print("Loading and splitting items ...")
    item_list = load_split_logic(filename, items_raw, delimiter)

    # Batch Sentiment
    print(f"Running batch sentiment for {len(item_list)} items ...")
    schema_desc = "JSON array of objects with: item, label, score, confidence, emotions, key_phrases."
    res_str = _run_task(
        analyst,
        description=f"Analyze the sentiment of these items in the '{domain}' domain: {json.dumps(item_list)}\n\nFormat as: {schema_desc}",
        expected_output="A valid JSON array of sentiment results."
    )
    results = _parse_json(res_str)

    # Stats and Extremes
    print("Computing stats and extremes ...")
    stats = compute_stats_logic(results)
    extremes = find_extremes_logic(results)

    # Trend Narrative
    print("Generating trend narrative ...")
    trend_summary = _run_task(
        specialist,
        description=f"Summarize the sentiment trends for {domain}. Stats: {json.dumps(stats)}\nExtremes: {json.dumps(extremes)}",
        expected_output="A concise narrative of sentiment trends."
    )

    # Assemble Report
    print("Assembling full report ...")
    report = _run_task(
        writer,
        description=f"Assemble a final report. Domain: {domain}\nResults: {json.dumps(results)}\nStats: {json.dumps(stats)}\nTrend: {trend_summary}\nExtremes: {json.dumps(extremes)}",
        expected_output="A comprehensive, structured sentiment report."
    )

    _write(f"{log_dir}/report.md", report)
    return report


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--filename",  default="",        show_default=True, help="File with items (one per line)")
@click.option("--items",     default="",        show_default=True, help="Inline items (use --delimiter to split)")
@click.option("--delimiter", default="\\n",     show_default=True)
@click.option("--domain",    default="general", show_default=True)
@click.option("--model",     default="gemma3",  show_default=True)
@click.option("--log-dir",   default="cookbook/31_sentiment_pipeline/crewai/logs-crewai", show_default=True)
def main(filename: str, items: str, delimiter: str, domain: str, model: str, log_dir: str):
    result = run(filename, items, delimiter, domain, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
