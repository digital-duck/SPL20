"""
tools.py — Python tools for Recipe 43: Prompt Self-Tuning (Meta-Programming).

Tools:
  check_quality(text)        Heuristic quality gate — returns 'pass' or 'fail:<reason>'.
  write_file(path, content)  Write text to a file (creates parent dirs).

Usage:
  spl run cookbook/43_prompt_self_tuning/prompt_self_tuning.spl \\
      --tools cookbook/43_prompt_self_tuning/tools.py \\
      --adapter ollama \\
      baseline_prompt="Summarize this technical document." \\
      failed_case="The document describes a complex quantum algorithm."
"""

import os

from spl.tools import spl_tool

# Minimum word count for a response to be considered passing quality
_MIN_WORDS = 30


@spl_tool
def check_quality(text: str) -> str:
    """
    Heuristic quality gate for generated text.

    Checks:
      - Minimum word count (>= 30 words)
      - Not a refusal / error message
      - Not mostly whitespace

    Returns 'pass' if all checks pass, or 'fail:<reason>' otherwise.
    This is a deterministic check — zero LLM tokens consumed.
    """
    if not text or not text.strip():
        return "fail:empty_response"

    words = text.split()
    if len(words) < _MIN_WORDS:
        return f"fail:too_short({len(words)}_words)"

    lower = text.lower()
    refusal_markers = [
        "i cannot", "i can't", "i'm unable", "i am unable",
        "as an ai", "i don't have", "i do not have",
        "error:", "exception:", "traceback",
    ]
    for marker in refusal_markers:
        if marker in lower:
            return f"fail:refusal_detected"

    return "pass"


@spl_tool
def write_file(path: str, content: str) -> str:
    """
    Write text content to a file, creating parent directories if needed.

    Returns 'ok:<path>' on success or 'error:<message>' on failure.
    Pass 'NONE' as path to discard output without writing.
    """
    if not path or path.upper() == "NONE":
        return "ok:discarded"
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"ok:{path}"
    except OSError as exc:
        return f"error:{exc}"
