"""
tools.py — Python tools for Recipe 29: Meeting Notes → Action Items.

Tools:
  load_transcript(filename)           Load a transcript file by name from the transcripts/ folder.
  extract_speakers(text)              Regex-extract all speaker names from "Speaker: ..." lines.
  normalize_dates(json_str)           Replace relative date phrases with ISO dates (today = run date).
  validate_ownership(json_str)        Flag high-priority action items that have no assigned owner.

Usage:
  spl2 run cookbook/29_meeting_actions/meeting_actions.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/29_meeting_actions/tools.py \\
      filename=sprint_planning.txt \\
      output_format=markdown
"""

import json
import os
import re
from datetime import date, timedelta

from spl2.tools import spl_tool

_TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "transcripts")


# ── Helpers ────────────────────────────────────────────────────────────────

def _today() -> date:
    return date.today()


def _next_weekday(weekday: int) -> date:
    """Return the next occurrence of weekday (0=Mon … 6=Sun), today counts if it matches."""
    today = _today()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def _resolve_date_phrase(phrase: str) -> str | None:
    """
    Convert a common relative date phrase to an ISO-8601 date string.
    Returns None if the phrase is not recognised.
    """
    phrase = phrase.strip().lower()
    today = _today()
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    if phrase in ("today",):
        return today.isoformat()
    if phrase in ("tomorrow",):
        return (today + timedelta(days=1)).isoformat()
    if phrase in ("end of day", "eod"):
        return today.isoformat()
    if phrase in ("this week", "end of week", "eow"):
        return _next_weekday(4).isoformat()   # Friday
    if phrase in ("next week",):
        return (today + timedelta(days=7)).isoformat()
    if phrase in ("end of sprint", "end of this sprint"):
        # Assume 2-week sprint; next Friday + 1 week
        return (_next_weekday(4) + timedelta(days=7)).isoformat()
    if phrase in ("next sprint",):
        return (today + timedelta(weeks=2)).isoformat()
    if phrase in ("end of month",):
        next_month = date(today.year, today.month % 12 + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        return (next_month - timedelta(days=1)).isoformat()

    # "next monday" / "this friday" / bare weekday name
    for name, idx in weekdays.items():
        if phrase == name or phrase == f"this {name}":
            return _next_weekday(idx).isoformat()
        if phrase == f"next {name}":
            base = _next_weekday(idx)
            # "next X" always means at least 7 days away
            if (base - today).days < 7:
                base += timedelta(days=7)
            return base.isoformat()

    # "by wednesday", "by end of day thursday", "before friday"
    for prep in ("by ", "before ", "by end of day "):
        if phrase.startswith(prep):
            return _resolve_date_phrase(phrase[len(prep):])

    return None


# ── Tools ──────────────────────────────────────────────────────────────────

@spl_tool
def load_transcript(filename: str) -> str:
    """
    Load a meeting transcript from the transcripts/ folder.

    Pass just the filename, e.g. 'sprint_planning.txt'.
    Returns the full transcript text, or an error message if the file is not found.

    Available transcripts: sprint_planning.txt, design_review.txt, standup.txt
    """
    filename = filename.strip()
    if not filename:
        return ""

    path = os.path.join(_TRANSCRIPTS_DIR, filename)
    if not os.path.isfile(path):
        available = ", ".join(sorted(os.listdir(_TRANSCRIPTS_DIR)))
        return f"File not found: '{filename}'. Available transcripts: {available}"

    with open(path, encoding="utf-8") as fh:
        return fh.read()


@spl_tool
def extract_speakers(text: str) -> str:
    """
    Extract all unique speaker names from a meeting transcript.

    Recognises lines in the format "Speaker: text" or "Speaker (Role): text".
    Also picks up names from the header "Attendees:" line.

    Returns a comma-separated list of unique speaker names, e.g.:
      "Alice, Bob, Carol, Dave, Eve"
    """
    speakers: list[str] = []
    seen: set[str] = set()

    # "Attendees: Alice (PM), Bob (Backend), ..."
    for m in re.finditer(r'Attendees?:\s*(.+)', text, re.IGNORECASE):
        for part in m.group(1).split(","):
            name = re.sub(r'\s*\(.*?\)', '', part).strip()
            if name and name not in seen:
                seen.add(name)
                speakers.append(name)

    # "Speaker: ..." or "Speaker (Role): ..."
    for m in re.finditer(r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*(?:\([^)]*\))?:', text, re.MULTILINE):
        name = m.group(1).strip()
        if name not in seen and name.lower() not in {"date", "attendees", "facilitator", "format"}:
            seen.add(name)
            speakers.append(name)

    return ", ".join(speakers) if speakers else "Unknown"


@spl_tool
def normalize_dates(json_str: str) -> str:
    """
    Walk every action item's 'due_date' field and replace relative phrases
    (e.g. 'Friday', 'next Wednesday', 'end of sprint') with ISO-8601 dates.

    Unrecognised phrases are left as-is so the LLM's wording is preserved.
    Returns the updated JSON string.
    """
    json_str = json_str.strip()
    if not json_str:
        return json_str

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return json_str  # not parseable JSON — return unchanged

    items = data.get("action_items", [])
    for item in items:
        raw = item.get("due_date", "")
        if raw:
            resolved = _resolve_date_phrase(raw)
            if resolved:
                item["due_date"] = resolved

    return json.dumps(data, indent=2)


@spl_tool
def validate_ownership(json_str: str) -> str:
    """
    Inspect extracted action items and flag any that are high-priority but lack a clear owner.

    Returns a plain-text validation report, e.g.:
      "2 issue(s) found:
       - [HIGH] 'Provision screen reader VM' has no owner assigned.
       - [HIGH] 'Set up on-call rotation' has no owner assigned."

    Returns "All high-priority items have owners." if no issues are found.
    """
    json_str = json_str.strip()
    if not json_str:
        return "No action items to validate."

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return "Could not parse action items JSON for validation."

    issues: list[str] = []
    no_owner_values = {"", "tbd", "unknown", "unassigned", "n/a", "none"}

    for item in data.get("action_items", []):
        priority = (item.get("priority") or "").lower()
        owner = (item.get("owner") or "").strip().lower()
        task = item.get("task", "(unnamed task)")

        if priority == "high" and owner in no_owner_values:
            issues.append(f"- [HIGH] '{task}' has no owner assigned.")

    if not issues:
        return "All high-priority items have owners."

    header = f"{len(issues)} high-priority item(s) without an owner:\n"
    return header + "\n".join(issues)
