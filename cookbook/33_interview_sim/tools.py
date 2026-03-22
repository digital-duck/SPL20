"""
tools.py — Python tools for Recipe 33: Interview Simulator.

Tools:
  load_role(role_key, focus_area)         Load role definition + focus area context from roles.json.
  load_candidate(candidate_id)            Load candidate profile from candidates.json.
  list_roles()                            List all available role IDs and focus areas.
  extract_question(questions_json, n)     Pull question N from a JSON array (replaces GENERATE ask_question).
  aggregate_scores(score1, score2, score3)Compute per-dimension averages across all scored answers.
  compile_transcript(...)                 Format the complete interview as a readable transcript.

Usage:
  spl run cookbook/33_interview_sim/interview_sim.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/33_interview_sim/tools.py \\
      role_key=senior_swe focus=system_design candidate_id=alice_senior_swe difficulty=hard
"""

import json
import os
import textwrap

from spl.tools import spl_tool

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ── Helpers ────────────────────────────────────────────────────────────────

def _load_json(filename: str) -> dict:
    with open(os.path.join(_DATA_DIR, filename), encoding="utf-8") as fh:
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


# ── Tools ──────────────────────────────────────────────────────────────────

@spl_tool
def load_role(role_key: str, focus_area: str) -> str:
    """
    Load a role definition and focus area context from data/roles.json.

    Returns a structured text block with:
      - role title and level
      - focus area description and competencies
      - sample interview questions for this focus
      - signals of strong and weak answers

    Pass role_key="" to list all available role IDs.
    Pass focus_area="" to list all focus areas for a role.
    """
    data = _load_json("roles.json")
    roles = {r["id"]: r for r in data["roles"]}

    role_key = role_key.strip().lower()
    focus_area = focus_area.strip().lower().replace(" ", "_")

    if not role_key:
        lines = ["Available roles:"]
        for r in data["roles"]:
            fas = ", ".join(r["focus_areas"].keys())
            lines.append(f"  {r['id']:20s} ({r['title']}) — focus areas: {fas}")
        return "\n".join(lines)

    role = roles.get(role_key)
    if role is None:
        available = ", ".join(roles.keys())
        return f"Role '{role_key}' not found. Available: {available}"

    if not focus_area:
        lines = [f"Focus areas for '{role['title']}':"]
        for fa_id, fa in role["focus_areas"].items():
            lines.append(f"  {fa_id:30s} — {fa['description']}")
        return "\n".join(lines)

    fa = role["focus_areas"].get(focus_area)
    if fa is None:
        available = ", ".join(role["focus_areas"].keys())
        return (
            f"Focus area '{focus_area}' not found in role '{role_key}'. "
            f"Available: {available}"
        )

    lines = [
        f"ROLE: {role['title']} ({role['level']})",
        f"FOCUS AREA: {focus_area.replace('_', ' ').title()}",
        f"Description: {fa['description']}",
        "",
        "COMPETENCIES expected from a strong candidate:",
    ]
    for c in fa["competencies"]:
        lines.append(f"  - {c}")

    lines += ["", "SAMPLE QUESTIONS (select or adapt from these):"]
    for i, q in enumerate(fa["sample_questions"], 1):
        lines.append(f"  Q{i}: {q}")

    lines += ["", "SIGNALS OF A STRONG ANSWER:"]
    for s in fa["strong_answer_signals"]:
        lines.append(f"  + {s}")

    lines += ["", "SIGNALS OF A WEAK ANSWER:"]
    for s in fa["weak_answer_signals"]:
        lines.append(f"  - {s}")

    return "\n".join(lines)


@spl_tool
def load_candidate(candidate_id: str) -> str:
    """
    Load a candidate profile from data/candidates.json.

    Returns a structured text block with background, strong areas, weak areas,
    communication style, and typical answer gaps.

    Pass candidate_id="" to list all available candidate IDs.
    """
    data = _load_json("candidates.json")
    candidates = {c["id"]: c for c in data["candidates"]}

    candidate_id = candidate_id.strip().lower()

    if not candidate_id:
        lines = ["Available candidate profiles:"]
        for c in data["candidates"]:
            lines.append(
                f"  {c['id']:25s} — {c['name']}, {c['years_experience']}y exp, "
                f"applying for {c['role_applying']}"
            )
        return "\n".join(lines)

    cand = candidates.get(candidate_id)
    if cand is None:
        available = ", ".join(candidates.keys())
        return f"Candidate '{candidate_id}' not found. Available: {available}"

    lines = [
        f"CANDIDATE: {cand['name']}",
        f"Current title: {cand['current_title']}",
        f"Experience: {cand['years_experience']} years",
        f"Education: {cand['education']}",
        "",
        f"BACKGROUND:",
        _wrap(cand["background"], indent="  "),
        "",
        "STRONG AREAS (answer confidently and with detail here):",
    ]
    for s in cand["strong_areas"]:
        lines.append(f"  + {s}")

    lines += ["", "WEAK AREAS (show honest gaps, partial knowledge, or uncertainty here):"]
    for w in cand["weak_areas"]:
        lines.append(f"  - {w}")

    lines += ["", f"COMMUNICATION STYLE: {cand['communication_style']}"]

    lines += ["", "TYPICAL ANSWER GAPS (simulate these realistically):"]
    for g in cand["typical_gaps"]:
        lines.append(f"  ~ {g}")

    return "\n".join(lines)


@spl_tool
def list_roles() -> str:
    """
    List all available role IDs, titles, and their focus areas from data/roles.json.
    """
    data = _load_json("roles.json")
    lines = ["Available roles and focus areas:", ""]
    for r in data["roles"]:
        lines.append(f"Role ID : {r['id']}")
        lines.append(f"Title   : {r['title']} ({r['level']})")
        lines.append("Focus areas:")
        for fa_id, fa in r["focus_areas"].items():
            lines.append(f"  {fa_id:30s} — {fa['description']}")
        lines.append("")
    return "\n".join(lines)


@spl_tool
def extract_question(questions_json: str, n: str) -> str:
    """
    Deterministically extract question number N from a JSON array of questions.

    Expects the JSON to be either:
      ["Q1 text", "Q2 text", "Q3 text"]
    or:
      [{"question": "Q1 text", ...}, ...]

    N is 1-based. Returns the question text as a plain string, or an error message.
    This replaces the costly GENERATE ask_question() LLM call.
    """
    questions_json = questions_json.strip()
    try:
        idx = int(n) - 1
    except (ValueError, TypeError):
        return f"Invalid question number: '{n}'"

    try:
        questions = json.loads(questions_json)
    except json.JSONDecodeError:
        # If not valid JSON, treat as newline-separated questions
        lines = [l.strip() for l in questions_json.split("\n") if l.strip()]
        if 0 <= idx < len(lines):
            return lines[idx]
        return f"Question {n} not found. Only {len(lines)} questions available."

    if not isinstance(questions, list):
        return "Questions JSON must be an array."

    if idx < 0 or idx >= len(questions):
        return f"Question {n} not found. Only {len(questions)} questions in the set."

    item = questions[idx]
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("question", item.get("text", str(item)))
    return str(item)


@spl_tool
def aggregate_scores(score1_json: str, score2_json: str, score3_json: str) -> str:
    """
    Compute per-dimension averages and an overall total across three scored answers.

    Expects each score JSON to match the evaluation_rubric() schema:
      {"accuracy": N, "depth": N, "communication": N, "experience": N, "total": N, "feedback": "..."}

    Returns a JSON object:
      {
        "per_question": [score1, score2, score3],
        "averages": {"accuracy": f, "depth": f, "communication": f, "experience": f},
        "overall_total": f,
        "highest_score": {"question": N, "total": f},
        "lowest_score":  {"question": N, "total": f},
        "verdict": "strong hire" | "hire" | "lean hire" | "no hire"
      }
    """
    scores = []
    for i, raw in enumerate([score1_json, score2_json, score3_json], 1):
        raw = raw.strip()
        try:
            obj = json.loads(raw)
            obj["_q"] = i
            scores.append(obj)
        except (json.JSONDecodeError, AttributeError):
            scores.append({"_q": i, "accuracy": 5, "depth": 5,
                           "communication": 5, "experience": 5,
                           "total": 20, "feedback": "(parse error)"})

    dims = ["accuracy", "depth", "communication", "experience"]
    averages = {}
    for d in dims:
        vals = [s.get(d, 5) for s in scores]
        averages[d] = round(sum(vals) / len(vals), 1)

    totals = [s.get("total", sum(s.get(d, 5) for d in dims)) for s in scores]
    overall = round(sum(totals) / len(totals), 1)

    # Verdict based on overall average (max 40 per question)
    pct = overall / 40.0
    if pct >= 0.85:
        verdict = "strong hire"
    elif pct >= 0.70:
        verdict = "hire"
    elif pct >= 0.55:
        verdict = "lean hire"
    else:
        verdict = "no hire"

    best = max(range(len(totals)), key=lambda i: totals[i])
    worst = min(range(len(totals)), key=lambda i: totals[i])

    return json.dumps({
        "per_question": [
            {k: v for k, v in s.items() if not k.startswith("_")}
            for s in scores
        ],
        "averages": averages,
        "overall_total": overall,
        "max_possible": 40,
        "highest_scoring_question": {"question": best + 1, "total": totals[best]},
        "lowest_scoring_question":  {"question": worst + 1, "total": totals[worst]},
        "verdict": verdict,
    }, indent=2)


@spl_tool
def compile_transcript(
    q1: str, a1: str, score1_json: str,
    q2: str, a2: str, score2_json: str,
    q3: str, a3: str, score3_json: str,
    role: str,
    focus: str,
) -> str:
    """
    Format the complete interview as a readable text transcript.

    Each Q&A turn includes the question, the candidate's answer, and a brief
    score summary pulled deterministically from the score JSON.
    No LLM cost — this is a pure formatting step.
    """
    divider = "─" * 68

    def _score_summary(raw: str, q_num: int) -> str:
        try:
            s = json.loads(raw.strip())
            dims = f"Accuracy {s.get('accuracy','?')}/10  Depth {s.get('depth','?')}/10  " \
                   f"Comm {s.get('communication','?')}/10  Exp {s.get('experience','?')}/10  " \
                   f"→ Total {s.get('total','?')}/40"
            feedback = s.get("feedback", "")
            return f"[Q{q_num} SCORE] {dims}\n         {_wrap(feedback, indent='         ')}"
        except (json.JSONDecodeError, AttributeError):
            return f"[Q{q_num} SCORE] (score unavailable)"

    lines = [
        "INTERVIEW TRANSCRIPT",
        f"Role : {role.strip()}",
        f"Focus: {focus.strip()}",
        divider,
        "",
        "QUESTION 1",
        f"Interviewer: {_wrap(q1.strip(), indent='             ')}",
        "",
        f"Candidate:   {_wrap(a1.strip(), indent='             ')}",
        "",
        _score_summary(score1_json, 1),
        "",
        divider,
        "",
        "QUESTION 2",
        f"Interviewer: {_wrap(q2.strip(), indent='             ')}",
        "",
        f"Candidate:   {_wrap(a2.strip(), indent='             ')}",
        "",
        _score_summary(score2_json, 2),
        "",
        divider,
        "",
        "QUESTION 3",
        f"Interviewer: {_wrap(q3.strip(), indent='             ')}",
        "",
        f"Candidate:   {_wrap(a3.strip(), indent='             ')}",
        "",
        _score_summary(score3_json, 3),
        "",
        divider,
    ]
    return "\n".join(lines)
