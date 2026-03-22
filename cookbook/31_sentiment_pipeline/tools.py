"""
tools.py — Python tools for Recipe 31: Sentiment Pipeline.

Tools:
  load_items(filename)            Load a reviews file by name from the reviews/ folder.
  split_items(file_content, inline_items, delimiter)
                                  Split text into a JSON array of clean item strings.
  compute_stats(sentiment_json)   Aggregate label counts, score stats, confidence from results.
  find_extremes(sentiment_json)   Locate most positive, most negative, lowest-confidence items.

Usage:
  spl run cookbook/31_sentiment_pipeline/sentiment.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/31_sentiment_pipeline/tools.py \\
      filename=product_reviews.txt \\
      domain=product_reviews
"""

import json
import math
import os

from spl.tools import spl_tool

_REVIEWS_DIR = os.path.join(os.path.dirname(__file__), "reviews")


# ── Tools ──────────────────────────────────────────────────────────────────

@spl_tool
def load_items(filename: str) -> str:
    """
    Load a reviews / items file from the reviews/ folder by filename.

    Pass just the filename, e.g. 'product_reviews.txt'.
    Returns the raw text content, or an error listing available files if not found.
    Returns an empty string if filename is blank.

    Available files: product_reviews.txt, support_tickets.txt, social_media.txt
    """
    filename = filename.strip()
    if not filename:
        return ""

    path = os.path.join(_REVIEWS_DIR, filename)
    if not os.path.isfile(path):
        available = ", ".join(sorted(os.listdir(_REVIEWS_DIR)))
        return f"File not found: '{filename}'. Available files: {available}"

    with open(path, encoding="utf-8") as fh:
        return fh.read()


@spl_tool
def split_items(file_content: str, inline_items: str, delimiter: str) -> str:
    """
    Split a block of text into a JSON array of trimmed, non-empty item strings.

    Priority: file_content is used if non-empty; otherwise inline_items is used.
    The delimiter can be '|', '\\n', ',', or any literal string.
    The literal string '\\n' (two chars) is normalised to a real newline.

    Returns a JSON array, e.g.:
      ["Great product!", "Terrible experience", "It was okay"]
    """
    # Choose source
    text = file_content.strip() if file_content.strip() else inline_items.strip()
    if not text:
        return json.dumps([])

    # Normalise escaped newline written as the two characters backslash-n
    if delimiter == "\\n":
        delimiter = "\n"

    parts = [p.strip() for p in text.split(delimiter)]
    items = [p for p in parts if p]  # drop empties

    return json.dumps(items, ensure_ascii=False)


@spl_tool
def compute_stats(sentiment_json: str) -> str:
    """
    Compute aggregate statistics over a batch of sentiment results.

    Expects a JSON array where each element has at least:
      {"label": "positive"|"negative"|"neutral"|"mixed",
       "score": <float -1..1>,
       "confidence": <float 0..1>}

    Returns a JSON object:
      {
        "total": <int>,
        "label_counts": {"positive": N, "negative": N, "neutral": N, "mixed": N},
        "label_pct":    {"positive": %, ...},
        "score": {"mean": f, "min": f, "max": f, "std_dev": f},
        "confidence": {"mean": f, "min": f, "max": f},
        "sentiment_ratio": <positive_count / max(1, negative_count)>
      }
    """
    sentiment_json = sentiment_json.strip()
    if not sentiment_json:
        return json.dumps({"error": "No sentiment results to aggregate."})

    try:
        results = json.loads(sentiment_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Could not parse sentiment results JSON."})

    if not isinstance(results, list) or not results:
        return json.dumps({"error": "Sentiment results must be a non-empty array."})

    labels = ["positive", "negative", "neutral", "mixed"]
    counts = {l: 0 for l in labels}
    scores: list[float] = []
    confidences: list[float] = []

    for item in results:
        label = (item.get("label") or "neutral").lower()
        if label in counts:
            counts[label] += 1
        else:
            counts["neutral"] += 1

        score = item.get("score")
        if isinstance(score, (int, float)):
            scores.append(float(score))

        conf = item.get("confidence")
        if isinstance(conf, (int, float)):
            confidences.append(float(conf))

    total = len(results)
    pct = {l: round(counts[l] / total * 100, 1) for l in labels}

    def _stats(vals: list[float]) -> dict:
        if not vals:
            return {"mean": 0, "min": 0, "max": 0, "std_dev": 0}
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        return {
            "mean":    round(mean, 3),
            "min":     round(min(vals), 3),
            "max":     round(max(vals), 3),
            "std_dev": round(math.sqrt(variance), 3),
        }

    pos = counts["positive"]
    neg = counts["negative"]
    ratio = round(pos / max(1, neg), 2)

    return json.dumps({
        "total":           total,
        "label_counts":    counts,
        "label_pct":       pct,
        "score":           _stats(scores),
        "confidence":      _stats(confidences),
        "sentiment_ratio": ratio,
    }, indent=2)


@spl_tool
def find_extremes(sentiment_json: str) -> str:
    """
    Identify the most noteworthy items from a batch of sentiment results.

    Finds:
      most_positive   — highest score
      most_negative   — lowest score
      lowest_confidence — least certain classification
      all_mixed       — all items labelled 'mixed'
      all_negative    — all items labelled 'negative'

    Each result entry is expected to have an 'item' field (the original text).
    Returns a JSON object with the above keys.
    """
    sentiment_json = sentiment_json.strip()
    if not sentiment_json:
        return json.dumps({"error": "No sentiment results provided."})

    try:
        results = json.loads(sentiment_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Could not parse sentiment results JSON."})

    if not isinstance(results, list) or not results:
        return json.dumps({"error": "Sentiment results must be a non-empty array."})

    scored = [r for r in results if isinstance(r.get("score"), (int, float))]
    if not scored:
        return json.dumps({"error": "No items with numeric score found."})

    most_positive = max(scored, key=lambda r: r["score"])
    most_negative = min(scored, key=lambda r: r["score"])

    conf_items = [r for r in results if isinstance(r.get("confidence"), (int, float))]
    lowest_conf = min(conf_items, key=lambda r: r["confidence"]) if conf_items else None

    mixed    = [r for r in results if (r.get("label") or "").lower() == "mixed"]
    negative = [r for r in results if (r.get("label") or "").lower() == "negative"]

    def _summarise(r: dict) -> dict:
        return {
            "item":       r.get("item", ""),
            "label":      r.get("label", ""),
            "score":      r.get("score"),
            "confidence": r.get("confidence"),
            "emotions":   r.get("emotions", []),
            "key_phrases":r.get("key_phrases", []),
        }

    return json.dumps({
        "most_positive":      _summarise(most_positive),
        "most_negative":      _summarise(most_negative),
        "lowest_confidence":  _summarise(lowest_conf) if lowest_conf else None,
        "all_mixed":          [_summarise(r) for r in mixed],
        "all_negative":       [_summarise(r) for r in negative],
        "negative_count":     len(negative),
        "mixed_count":        len(mixed),
    }, indent=2)
