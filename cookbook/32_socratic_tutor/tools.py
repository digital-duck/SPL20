"""
tools.py — Python tools for Recipe 32: Socratic Tutor.

Tools:
  load_topic(topic_id, subject)     Load structured topic context from topics/<subject>.json.
  list_topics(subject)              List all available topic IDs for a given subject.
  get_level_guidance(student_level) Return vocabulary and complexity hints for a student level.
  compile_dialogue(...)             Format the completed Socratic dialogue as readable text.

Usage:
  spl run cookbook/32_socratic_tutor/socratic_tutor.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/32_socratic_tutor/tools.py \\
      topic_id=sky_blue subject=science student_level="middle school"
"""

import json
import os
import textwrap

from spl.tools import spl_tool

_TOPICS_DIR = os.path.join(os.path.dirname(__file__), "topics")


# ── Helpers ────────────────────────────────────────────────────────────────

def _load_subject(subject: str) -> dict | None:
    """Load the JSON file for a subject. Returns None if not found."""
    path = os.path.join(_TOPICS_DIR, f"{subject.strip().lower()}.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _available_subjects() -> list[str]:
    return sorted(
        f.replace(".json", "")
        for f in os.listdir(_TOPICS_DIR)
        if f.endswith(".json")
    )


# ── Tools ──────────────────────────────────────────────────────────────────

@spl_tool
def load_topic(topic_id: str, subject: str) -> str:
    """
    Load structured context for a specific topic from topics/<subject>.json.

    Returns a formatted text block containing:
      - title, domain, recommended student levels
      - prerequisites the student should already know
      - learning objectives for this session
      - common misconceptions to watch for and correct via questions
      - key concepts the Socratic dialogue should surface
      - suggested Socratic question path

    If topic_id is blank, returns a summary of available topics for the subject.
    If subject is blank, lists all available subjects.
    """
    subject = subject.strip().lower()
    topic_id = topic_id.strip().lower()

    if not subject:
        subjects = _available_subjects()
        return f"Available subjects: {', '.join(subjects)}. Please specify a subject."

    data = _load_subject(subject)
    if data is None:
        subjects = _available_subjects()
        return (
            f"Subject '{subject}' not found. "
            f"Available subjects: {', '.join(subjects)}"
        )

    topics = data.get("topics", [])

    if not topic_id:
        summary = [f"Topics available in '{subject}':"]
        for t in topics:
            summary.append(f"  {t['id']:30s} — {t['title']}")
        return "\n".join(summary)

    # Find the specific topic
    topic = next((t for t in topics if t["id"] == topic_id), None)
    if topic is None:
        ids = [t["id"] for t in topics]
        return (
            f"Topic '{topic_id}' not found in subject '{subject}'. "
            f"Available: {', '.join(ids)}"
        )

    lines = [
        f"TOPIC: {topic['title']}",
        f"Domain: {topic.get('domain', '')}",
        f"Recommended levels: {', '.join(topic.get('recommended_levels', []))}",
        "",
        "PREREQUISITES (what the student should already know):",
    ]
    for p in topic.get("prerequisites", []):
        lines.append(f"  - {p}")

    lines += ["", "LEARNING OBJECTIVES (what we want the student to discover):"]
    for o in topic.get("learning_objectives", []):
        lines.append(f"  - {o}")

    lines += ["", "COMMON MISCONCEPTIONS (steer away from these via questions, never state directly):"]
    for m in topic.get("common_misconceptions", []):
        lines.append(f"  - {m}")

    lines += ["", f"KEY CONCEPTS to surface: {', '.join(topic.get('key_concepts', []))}"]

    lines += ["", "SUGGESTED SOCRATIC PATH (adapt freely — these are hints, not a script):"]
    for i, q in enumerate(topic.get("socratic_path", []), 1):
        lines.append(f"  Q{i}: {q}")

    return "\n".join(lines)


@spl_tool
def list_topics(subject: str) -> str:
    """
    List all topic IDs and titles available for a given subject.

    Subject must be one of: science, math, programming.
    Returns a formatted list of id → title pairs.
    """
    subject = subject.strip().lower()
    if not subject:
        subjects = _available_subjects()
        return f"Available subjects: {', '.join(subjects)}"

    data = _load_subject(subject)
    if data is None:
        subjects = _available_subjects()
        return f"Subject '{subject}' not found. Available: {', '.join(subjects)}"

    lines = [f"Topics in '{subject}':"]
    for t in data.get("topics", []):
        levels = ", ".join(t.get("recommended_levels", []))
        lines.append(f"  {t['id']:30s} [{levels}] — {t['title']}")
    return "\n".join(lines)


@spl_tool
def get_level_guidance(student_level: str) -> str:
    """
    Return vocabulary, question complexity, and scaffolding hints for a given student level.

    Supports: elementary, middle school, high school, undergraduate, graduate, expert.
    Falls back to 'high school' guidance for unrecognised levels.
    """
    level = student_level.strip().lower()

    guidance = {
        "elementary": (
            "Vocabulary: very simple words, no jargon, use analogies from everyday life (toys, food, animals).\n"
            "Questions: one short, concrete question at a time. Praise enthusiastically.\n"
            "Scaffolding: maximum hand-holding. If stuck, give a very strong hint framed as 'What if...'.\n"
            "Avoid: abstract symbols, technical terms, multi-step reasoning in a single question."
        ),
        "middle school": (
            "Vocabulary: simple but can introduce one new term per question with a clear analogy.\n"
            "Questions: concrete examples first, then generalize. Keep sentences short.\n"
            "Scaffolding: offer a visual or physical analogy when abstract concepts arise.\n"
            "Avoid: heavy mathematics, formal proofs, domain jargon without explanation."
        ),
        "high school": (
            "Vocabulary: standard academic language. Can use domain terms if briefly defined in context.\n"
            "Questions: can include two related ideas in one question. Encourage self-explanation.\n"
            "Scaffolding: redirect with 'What do you already know about X?' before giving hints.\n"
            "Avoid: graduate-level formalism; keep proofs intuitive rather than fully rigorous."
        ),
        "undergraduate": (
            "Vocabulary: full domain terminology expected. Mathematical notation is appropriate.\n"
            "Questions: can be multi-step. Challenge the student to prove or derive, not just describe.\n"
            "Scaffolding: minimal — push back on vague answers with 'Can you be more precise?'.\n"
            "Encourage: connecting this topic to other things they have studied."
        ),
        "graduate": (
            "Vocabulary: expert-level. Assume deep background knowledge.\n"
            "Questions: probe edge cases, assumptions, and limitations of standard results.\n"
            "Scaffolding: essentially none — treat as a peer discussion with Socratic probing.\n"
            "Challenge: ask them to find counterexamples, generalizations, or open problems."
        ),
        "expert": (
            "Vocabulary: cutting-edge domain language. Reference current literature is appropriate.\n"
            "Questions: explore open problems, conflicting frameworks, and novel applications.\n"
            "Scaffolding: none — the goal is collaborative exploration, not guided discovery.\n"
            "Mode: philosophical and critical — challenge foundational assumptions."
        ),
    }

    return guidance.get(level, guidance["high school"])


@spl_tool
def compile_dialogue(
    question_1: str,
    student_1: str,
    question_2: str,
    student_2: str,
    question_3: str,
    student_3: str,
    topic: str,
    understanding_score: str,
) -> str:
    """
    Format the completed Socratic dialogue as a readable text document.

    Combines three tutor questions and three student responses into a structured
    transcript with a header, turn-by-turn dialogue, and a brief closing note
    about the student's understanding score.

    This is a deterministic formatting step — no LLM needed.
    """
    try:
        score = float(understanding_score)
        score_label = (
            "strong understanding emerging" if score >= 8
            else "good progress with room to grow" if score >= 6
            else "still developing — more scaffolding recommended"
        )
    except (ValueError, TypeError):
        score = None
        score_label = "not assessed"

    divider = "─" * 60

    lines = [
        f"SOCRATIC DIALOGUE",
        f"Topic: {topic.strip()}",
        divider,
        "",
        "TUTOR:   " + _wrap(question_1.strip(), prefix="         "),
        "",
        "STUDENT: " + _wrap(student_1.strip(), prefix="         "),
        "",
        divider,
        "",
        "TUTOR:   " + _wrap(question_2.strip(), prefix="         "),
        "",
        "STUDENT: " + _wrap(student_2.strip(), prefix="         "),
        "",
        divider,
        "",
        "TUTOR:   " + _wrap(question_3.strip(), prefix="         "),
        "",
        "STUDENT: " + _wrap(student_3.strip(), prefix="         "),
        "",
        divider,
    ]

    if score is not None:
        lines += [
            f"Understanding score: {score}/10 — {score_label}",
        ]

    return "\n".join(lines)


def _wrap(text: str, prefix: str = "", width: int = 72) -> str:
    """Wrap text to width, indenting continuation lines with prefix."""
    first_line, *rest = textwrap.wrap(text, width=width - len(prefix))
    if not rest:
        return first_line
    continuation = ("\n" + prefix).join(rest)
    return first_line + "\n" + prefix + continuation
