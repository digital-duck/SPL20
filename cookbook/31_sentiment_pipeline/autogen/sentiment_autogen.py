"""
AutoGen equivalent of sentiment.spl

A procedural script coordinates specialized agents and deterministic tools
to implement a batch sentiment analysis pipeline.

Usage:
    pip install pyautogen
    python cookbook/31_sentiment_pipeline/autogen/sentiment_autogen.py \
        --items "Great product! | Terrible experience" --delimiter "|"
"""

import argparse
import json
import math
import re
from pathlib import Path

from autogen import ConversableAgent


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


# ── Agent system messages ─────────────────────────────────────────────────────

SENTIMENT_SCHEMA = """Return a JSON array of objects with: item, label (positive/negative/neutral/mixed), score (-1 to 1), confidence (0 to 1), emotions (list), key_phrases (list)."""
ANALYST_SYSTEM = f"You are a sentiment analyst. Analyze the sentiment of each item provided. {SENTIMENT_SCHEMA}"
SUMMARIZER_SYSTEM = "You are a trend summarizer. Provide a concise narrative of sentiment trends based on statistics and extreme cases."
ASSEMBLER_SYSTEM = "You are a report assembler. Create a comprehensive sentiment report based on analysis results, stats, and trend narratives."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _parse_json(text: str) -> list[dict]:
    clean = text.strip()
    if clean.startswith("```json"): clean = clean[7:-3].strip()
    elif clean.startswith("```"): clean = clean[3:-3].strip()
    try: res = json.loads(clean); return res if isinstance(res, list) else []
    except: return []


# ── Main runner ───────────────────────────────────────────────────────────────

def run(filename: str, items_raw: str, delimiter: str, domain: str, model: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # Agents
    analyst = ConversableAgent("Analyst", system_message=ANALYST_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")
    summarizer = ConversableAgent("Summarizer", system_message=SUMMARIZER_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")
    assembler = ConversableAgent("Assembler", system_message=ASSEMBLER_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")

    # Step 1 & 2: Load and Split
    print("Loading and splitting items ...")
    item_list = load_split_logic(filename, items_raw, delimiter)

    # Step 3: Batch Sentiment
    print(f"Running batch sentiment for {len(item_list)} items ...")
    reply = analyst.generate_reply(messages=[{"content": f"Domain: {domain}\nItems: {json.dumps(item_list)}", "role": "user"}])
    results = _parse_json(str(reply))

    # Step 4 & 5: Compute Stats and Extremes
    print("Computing stats and extremes ...")
    stats = compute_stats_logic(results)
    extremes = find_extremes_logic(results)

    # Step 6: Summarize Trends
    print("Generating trend narrative ...")
    trend_reply = summarizer.generate_reply(messages=[{"content": f"Domain: {domain}\nStats: {json.dumps(stats)}\nExtremes: {json.dumps(extremes)}", "role": "user"}])
    trend_summary = str(trend_reply)

    # Step 7: Assemble Report
    print("Assembling full report ...")
    report_reply = assembler.generate_reply(messages=[{"content": f"Domain: {domain}\nResults: {json.dumps(results)}\nStats: {json.dumps(stats)}\nTrend: {trend_summary}\nExtremes: {json.dumps(extremes)}", "role": "user"}])
    report = str(report_reply)

    _write(f"{log_dir}/report.md", report)
    return report


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Sentiment Pipeline — AutoGen edition")
    p.add_argument("--filename",  default="")
    p.add_argument("--items",     default="")
    p.add_argument("--delimiter", default="\\n")
    p.add_argument("--domain",    default="general")
    p.add_argument("--model",     default="gemma3")
    p.add_argument("--log-dir", default="cookbook/31_sentiment_pipeline/autogen/logs-autogen")
    args = p.parse_args()

    result = run(args.filename, args.items, args.delimiter, args.domain, args.model, args.log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
