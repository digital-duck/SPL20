"""
tools.py — Python tools for Recipe 26: Prompt A/B Test.

Tools:
  load_experiment(experiment_id)          Load a pre-built A/B experiment from experiments.json.
  list_experiments()                      List all available experiment IDs and descriptions.
  extract_score_total(score_json)         Parse a score JSON and return the numeric total.
  format_tie_result(response_a, response_b, score_a_json, score_b_json)
                                          Format a side-by-side tie report with scores.

Usage:
  spl run cookbook/26_ab_test/ab_test.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/26_ab_test/tools.py \\
      experiment_id=neural_networks
"""

import json
import os
import textwrap

from spl.tools import spl_tool

_DATA_DIR = os.path.dirname(__file__)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_experiments() -> dict:
    path = os.path.join(_DATA_DIR, "experiments.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _wrap(text: str, width: int = 76, indent: str = "  ") -> str:
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        wrapped = textwrap.fill(paragraph, width=width, subsequent_indent=indent)
        lines.append(wrapped)
    return "\n".join(lines)


# ── Tools ────────────────────────────────────────────────────────────────────

@spl_tool
def load_experiment(experiment_id: str) -> str:
    """
    Load a pre-built A/B experiment definition from experiments.json.

    Returns a structured text block with:
      - task: the shared task both variants respond to
      - prompt_a: the first prompt instruction
      - prompt_b: the second prompt instruction
      - notes: design rationale and expected outcome

    Pass experiment_id="" or "list" to see all available IDs.
    """
    data = _load_experiments()
    experiments = {e["id"]: e for e in data["experiments"]}

    experiment_id = experiment_id.strip().lower()

    if not experiment_id or experiment_id == "list":
        lines = ["Available experiments:", ""]
        for e in data["experiments"]:
            lines.append(f"  {e['id']:20s} — {e['notes'][:60]}...")
        return "\n".join(lines)

    exp = experiments.get(experiment_id)
    if exp is None:
        available = ", ".join(experiments.keys())
        return f"Experiment '{experiment_id}' not found. Available: {available}"

    lines = [
        f"EXPERIMENT: {exp['id']}",
        "",
        f"TASK:",
        f"  {_wrap(exp['task'], indent='  ')}",
        "",
        f"PROMPT A:",
        f"  {_wrap(exp['prompt_a'], indent='  ')}",
        "",
        f"PROMPT B:",
        f"  {_wrap(exp['prompt_b'], indent='  ')}",
        "",
        f"EXPECTED WINNER: {exp['expected_winner']}",
        "",
        f"NOTES:",
        f"  {_wrap(exp['notes'], indent='  ')}",
    ]
    return "\n".join(lines)


@spl_tool
def list_experiments() -> str:
    """
    List all available experiment IDs, tasks, and design notes from experiments.json.
    """
    data = _load_experiments()
    lines = ["Available A/B experiments:", ""]
    for e in data["experiments"]:
        lines.append(f"ID     : {e['id']}")
        lines.append(f"Task   : {e['task'][:80]}")
        lines.append(f"Notes  : {e['notes'][:80]}")
        lines.append("")
    return "\n".join(lines)


@spl_tool
def extract_score_total(score_json: str) -> str:
    """
    Deterministically parse a scoring rubric JSON and return the numeric total as a string.

    Expects the JSON format from scoring_rubric():
      {"clarity": N, "completeness": N, "relevance": N, "engagement": N, "total": N, "rationale": "..."}

    Returns the total score as a plain string (e.g. "32.0"), or "0" on parse failure.
    This replaces the GENERATE extract_total() LLM call — zero tokens.
    """
    score_json = score_json.strip()
    try:
        obj = json.loads(score_json)
        total = obj.get("total")
        if total is not None:
            return str(float(total))
        # Fallback: sum the four dimensions
        dims = ["clarity", "completeness", "relevance", "engagement"]
        total = sum(float(obj.get(d, 0)) for d in dims)
        return str(total)
    except (json.JSONDecodeError, ValueError, TypeError):
        return "0"


@spl_tool
def format_tie_result(
    response_a: str,
    response_b: str,
    score_a_json: str,
    score_b_json: str,
) -> str:
    """
    Format a side-by-side tie report when both variants score within the threshold.

    Returns a readable comparison with scores, per-dimension breakdown, and both responses.
    This replaces the GENERATE compare_outputs() LLM call — zero tokens.
    """
    divider = "─" * 68

    def _parse(raw: str) -> dict:
        try:
            return json.loads(raw.strip())
        except (json.JSONDecodeError, AttributeError):
            return {}

    def _dim_row(label: str, sa: dict, sb: dict) -> str:
        a_val = sa.get(label, "?")
        b_val = sb.get(label, "?")
        return f"  {label:<14} A: {a_val}/10   B: {b_val}/10"

    sa = _parse(score_a_json)
    sb = _parse(score_b_json)

    lines = [
        "TIE — Both variants scored within the threshold.",
        divider,
        "",
        "SCORES",
        _dim_row("clarity",      sa, sb),
        _dim_row("completeness", sa, sb),
        _dim_row("relevance",    sa, sb),
        _dim_row("engagement",   sa, sb),
        f"  {'total':<14} A: {sa.get('total', '?')}/40   B: {sb.get('total', '?')}/40",
        "",
        "RATIONALE A:",
        f"  {_wrap(sa.get('rationale', '(none)'), indent='  ')}",
        "",
        "RATIONALE B:",
        f"  {_wrap(sb.get('rationale', '(none)'), indent='  ')}",
        "",
        divider,
        "",
        "VARIANT A RESPONSE:",
        _wrap(response_a.strip(), indent="  "),
        "",
        divider,
        "",
        "VARIANT B RESPONSE:",
        _wrap(response_b.strip(), indent="  "),
        "",
        divider,
    ]
    return "\n".join(lines)
