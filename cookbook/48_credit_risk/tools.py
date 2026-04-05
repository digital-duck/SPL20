"""
tools.py — Python tools for Recipe 48: Credit Risk Assessment.

Tools:
  write_file(path, content)        Write text content to a file (creates parent dirs).
  extract_risk_rating(report)      Deterministically parse RISK_RATING: <level> from report.

Usage:
  spl run cookbook/48_credit_risk/assess_credit_risk.spl \\
      --adapter ollama \\
      --tools cookbook/48_credit_risk/tools.py \\
      applicant_data="$(cat cookbook/48_credit_risk/data/applicant_680.json)" \\
      credit_score=680
"""

import os
import re

from spl.tools import spl_tool


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
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"ok:{path}"
    except OSError as exc:
        return f"error:{exc}"


@spl_tool
def extract_risk_rating(report: str) -> str:
    """
    Deterministically extract the risk rating from a risk report.

    Looks for a line matching:  RISK_RATING: <low|medium|high>
    Returns one of: 'low', 'medium', 'high', or 'unknown' if not found.

    This replaces an LLM call — zero token cost.
    """
    if not report:
        return "unknown"

    match = re.search(
        r"RISK_RATING\s*:\s*(low|medium|high)",
        report,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).lower()

    # Fallback: keyword scan
    lower = report.lower()
    if "high risk" in lower or "high-risk" in lower:
        return "high"
    if "medium risk" in lower or "moderate risk" in lower:
        return "medium"
    if "low risk" in lower:
        return "low"

    return "unknown"
