"""
tools.py — Python tools for Recipe 49: Regulatory News Monitor.

Tools:
  read_news_feed(path)             Read a news feed file; return items as JSON array.
  get_list_length(json_list)       Return the number of items in a JSON array.
  get_item(json_list, index)       Return the item at position `index` in a JSON array.
  extract_json_field(json_str, k)  Extract a top-level field from a JSON object.
  write_file(path, content)        Write text to a file (creates parent dirs).
  send_alert(message)              Log a compliance alert (mock implementation).

Usage:
  spl run cookbook/49_regulatory_news_audit/audit_news.spl \\
      --adapter ollama \\
      --tools cookbook/49_regulatory_news_audit/tools.py \\
      news_batch_path=cookbook/49_regulatory_news_audit/data/news_feed.txt
"""

import json
import logging
import os

from spl.tools import spl_tool

_log = logging.getLogger("regulatory_news_audit.tools")


@spl_tool
def read_news_feed(path: str) -> str:
    """
    Read a plain-text news feed file and return its lines as a JSON array.

    Each non-blank line becomes one element. Lines starting with 'BATCH N:' are
    stripped of the prefix so the LLM receives clean news text.

    Returns a JSON-encoded list, e.g. '["item1", "item2", ...]'.
    Returns '[]' if the file is missing or empty.
    """
    import re

    if not path or not os.path.exists(path):
        _log.warning("News feed not found: %s", path)
        return "[]"

    with open(path, encoding="utf-8") as fh:
        raw_lines = fh.readlines()

    items = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # Strip optional "BATCH N: " prefix
        cleaned = re.sub(r"^BATCH\s+\d+\s*:\s*", "", line, flags=re.IGNORECASE)
        items.append(cleaned)

    return json.dumps(items)


@spl_tool
def get_list_length(json_list: str) -> int:
    """
    Return the number of items in a JSON array string.

    Returns 0 if the input is blank, invalid JSON, or not a list.
    """
    if not json_list or not json_list.strip():
        return 0
    try:
        data = json.loads(json_list)
        if isinstance(data, list):
            return len(data)
    except (json.JSONDecodeError, ValueError):
        pass
    return 0


@spl_tool
def get_item(json_list: str, index: str) -> str:
    """
    Return the item at position `index` (0-based) from a JSON array string.

    Returns '' if the index is out of range or the input is invalid.
    """
    if not json_list:
        return ""
    try:
        data = json.loads(json_list)
        if isinstance(data, list):
            idx = int(index)
            if 0 <= idx < len(data):
                return str(data[idx])
    except (json.JSONDecodeError, ValueError, TypeError, IndexError):
        pass
    return ""


@spl_tool
def extract_json_field(json_str: str, key: str) -> str:
    """
    Extract the value of a top-level field from a JSON object string.

    Returns the field value as a string, or '' if the key is absent or
    the input is not valid JSON.  Handles markdown code fences around the JSON.
    """
    if not json_str:
        return ""

    # Strip optional markdown code fences (```json ... ```)
    import re
    cleaned = re.sub(r"^```[a-z]*\s*|\s*```$", "", json_str.strip(), flags=re.DOTALL)

    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            val = obj.get(key, "")
            return str(val) if not isinstance(val, (dict, list)) else json.dumps(val)
    except (json.JSONDecodeError, ValueError):
        pass
    return ""


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


@spl_tool
def send_alert(message: str) -> str:
    """
    Send a compliance alert (mock implementation — logs to stderr and returns
    a confirmation string).

    Replace with an email/Slack/PagerDuty call in production.
    Returns 'alert_sent' on success.
    """
    _log.error("COMPLIANCE ALERT: %s", message[:200])
    print(f"\n*** COMPLIANCE ALERT ***\n{message[:500]}\n{'*' * 24}\n")
    return "alert_sent"
