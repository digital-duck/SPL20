"""
tools.py — Python tools for Recipe 18: Guardrails Pipeline.

Tools:
  load_test_input(input_id)       Load a pre-built test input from test_inputs.json.
  list_test_inputs()              List all available test input IDs and categories.
  detect_pii(text)                Regex-based PII detection (SSN, credit card, email, phone).
  redact_pii(text)                Regex-based PII redaction — replaces patterns with [REDACTED].
  classify_input_keywords(text)   Keyword pre-screen: flags harmful or off-topic inputs.

Usage:
  spl2 run cookbook/18_guardrails/guardrails.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/18_guardrails/tools.py \\
      input_id=pii_ssn

  spl2 run cookbook/18_guardrails/guardrails.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/18_guardrails/tools.py \\
      user_input="My SSN is 123-45-6789, help me file taxes"
"""

import json
import os
import re

from spl2.tools import spl_tool

_DATA_DIR = os.path.dirname(__file__)

# ── PII patterns ─────────────────────────────────────────────────────────────

_SSN_RE = re.compile(
    r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"
)

_CREDIT_CARD_RE = re.compile(
    r"\b(?:\d{4}[-\s]){3}\d{4}\b"
    r"|\b\d{16}\b"
)

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

_PHONE_RE = re.compile(
    r"(?:\+?1[-.\s]?)?"
    r"(?:\(\d{3}\)|\d{3})"
    r"[-.\s]\d{3}[-.\s]\d{4}\b"
)

# ── Keyword lists ─────────────────────────────────────────────────────────────

_HARMFUL_KEYWORDS = [
    "keylogger", "malware", "ransomware", "phishing", "pipe bomb", "bomb",
    "explosive", "poison", "synthesize drugs", "hack into", "steal credentials",
    "bypass security", "sql injection", "ddos", "denial of service",
    "child pornography", "child abuse", "cvv", "card skimmer",
    "install virus", "trojan horse", "zero-day exploit",
]

_OFF_TOPIC_KEYWORDS = [
    "buy stock", "stock market", "invest in", "trading advice",
    "diagnose me", "prescribe", "medical diagnosis", "what medication",
    "legal advice for my case", "represent me in court",
    "predict the lottery", "winning lottery numbers",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_test_inputs() -> dict:
    path = os.path.join(_DATA_DIR, "test_inputs.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ── Tools ─────────────────────────────────────────────────────────────────────

@spl_tool
def load_test_input(input_id: str) -> str:
    """
    Load a pre-built test input from test_inputs.json.

    Returns a structured text block with the input text, category, expected class,
    PII presence flags, and design notes.

    Pass input_id="" or "list" to see all available IDs.
    """
    data = _load_test_inputs()
    inputs = {t["id"]: t for t in data["test_inputs"]}

    input_id = input_id.strip().lower()

    if not input_id or input_id == "list":
        lines = ["Available test inputs:", ""]
        for t in data["test_inputs"]:
            pii_flag = " [PII]" if t.get("pii_present") else ""
            lines.append(
                f"  {t['id']:25s} [{t['category']:10s}]{pii_flag} — {t['notes'][:55]}..."
            )
        return "\n".join(lines)

    entry = inputs.get(input_id)
    if entry is None:
        available = ", ".join(inputs.keys())
        return f"Test input '{input_id}' not found. Available: {available}"

    pii_types = ", ".join(entry.get("pii_types", [])) or "none"
    lines = [
        f"TEST INPUT ID  : {entry['id']}",
        f"CATEGORY       : {entry['category']}",
        f"EXPECTED CLASS : {entry['expected_class']}",
        f"PII PRESENT    : {entry['pii_present']} ({pii_types})",
        f"NOTES          : {entry['notes']}",
        "",
        "INPUT TEXT:",
        f"  {entry['input']}",
    ]
    return "\n".join(lines)


@spl_tool
def list_test_inputs() -> str:
    """
    List all available test input IDs, categories, and notes from test_inputs.json.
    """
    data = _load_test_inputs()
    lines = ["Available guardrails test inputs:", ""]
    for t in data["test_inputs"]:
        pii_flag = " [PII]" if t.get("pii_present") else ""
        lines.append(f"ID       : {t['id']}{pii_flag}")
        lines.append(f"Category : {t['category']}")
        lines.append(f"Notes    : {t['notes']}")
        lines.append("")
    return "\n".join(lines)


@spl_tool
def detect_pii(text: str) -> str:
    """
    Regex-based PII detection. Checks for SSN, credit card numbers, email addresses,
    and phone numbers.

    Returns 'pii_found' if any PII pattern is detected, otherwise 'clean'.
    Also returns a JSON detail report as part of the response.

    This replaces GENERATE detect_pii() — deterministic, zero tokens.
    """
    if not text or not text.strip():
        return "clean"

    found = {}
    ssns = _SSN_RE.findall(text)
    if ssns:
        found["ssn"] = len(ssns)

    ccs = _CREDIT_CARD_RE.findall(text)
    if ccs:
        found["credit_card"] = len(ccs)

    emails = _EMAIL_RE.findall(text)
    if emails:
        found["email"] = len(emails)

    phones = _PHONE_RE.findall(text)
    if phones:
        found["phone"] = len(phones)

    if found:
        detail = json.dumps(found)
        return f"pii_found:{detail}"
    return "clean"


@spl_tool
def redact_pii(text: str) -> str:
    """
    Regex-based PII redaction. Replaces SSN, credit card numbers, email addresses,
    and phone numbers with [REDACTED].

    Returns the sanitised text with all detected PII replaced.
    This replaces GENERATE redact_pii() — deterministic, zero tokens.
    """
    if not text or not text.strip():
        return text

    text = _SSN_RE.sub("[REDACTED-SSN]", text)
    text = _CREDIT_CARD_RE.sub("[REDACTED-CC]", text)
    text = _EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED-PHONE]", text)
    return text


@spl_tool
def classify_input_keywords(text: str) -> str:
    """
    Keyword pre-screen for harmful or off-topic inputs.

    Checks the input against known harmful and off-topic keyword lists.
    Returns 'harmful', 'off_topic', or 'safe' (to pass through to LLM classification).

    This is a fast, zero-token pre-filter — the LLM classify_input step handles
    nuanced cases that keywords alone cannot catch.
    """
    if not text or not text.strip():
        return "safe"

    lower = text.lower()

    for kw in _HARMFUL_KEYWORDS:
        if kw in lower:
            return f"harmful:keyword={kw}"

    for kw in _OFF_TOPIC_KEYWORDS:
        if kw in lower:
            return f"off_topic:keyword={kw}"

    return "safe"
