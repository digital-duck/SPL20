"""
spl.stdlib — SPL Standard Library

Built-in tools available in every SPL workflow without --tools.
Mirrors the standard SQL function set so SQL practitioners can use
familiar names directly in CALL statements.

Categories
----------
  Type conversion   : to_int, to_float, to_text, to_bool
  String            : upper, lower, trim, ltrim, rtrim, length,
                      substr, replace, concat, instr, lpad, rpad,
                      split_part, reverse
  Pattern matching  : like, startswith, endswith, contains, regexp_match
  Numeric           : abs_val, round_val, ceil_val, floor_val,
                      mod_val, power_val, sqrt_val, sign_val, clamp
  Conditional       : coalesce, nullif, iif
  Null / empty      : isnull, nvl, isblank
  Aggregate (text)  : word_count, char_count, line_count
  JSON              : json_get, json_set, json_keys, json_length, json_pretty
  Date / time       : now_iso, date_format_val, date_diff_days
  Hashing           : md5_hash, sha256_hash
  List / split      : list_get, list_length, list_join, list_contains

All tools accept and return strings (SPL's universal scalar type).
Numeric tools accept numeric strings and return numeric strings so they
compose naturally with EVALUATE WHEN > comparisons.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import datetime
from typing import Any

from spl.tools import spl_tool

# ── Type Conversion ──────────────────────────────────────────────────────────

@spl_tool
def to_int(value: str) -> int:
    """CAST(value AS INTEGER) — convert string to integer (0 on failure)."""
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return 0


@spl_tool
def to_float(value: str) -> float:
    """CAST(value AS FLOAT) — convert string to float (0.0 on failure).
    Extracts the first numeric token, so '0.85\\n' and 'score: 0.85' both work.
    """
    if not value:
        return 0.0
    m = re.search(r"-?\d+(?:\.\d+)?", str(value).strip())
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return 0.0


@spl_tool
def to_text(value: Any) -> str:
    """CAST(value AS TEXT) — convert any value to its string representation."""
    if value is None:
        return ""
    return str(value)


@spl_tool
def to_bool(value: str) -> str:
    """CAST(value AS BOOLEAN) — returns 'true' or 'false'.
    Truthy: '1', 'true', 'yes', 'on', 't', 'y' (case-insensitive).
    """
    return "true" if str(value).strip().lower() in {"1", "true", "yes", "on", "t", "y"} else "false"


# ── String Functions ─────────────────────────────────────────────────────────

@spl_tool
def upper(value: str) -> str:
    """UPPER(value) — convert to uppercase."""
    return str(value).upper()


@spl_tool
def lower(value: str) -> str:
    """LOWER(value) — convert to lowercase."""
    return str(value).lower()


@spl_tool
def trim(value: str) -> str:
    """TRIM(value) — remove leading and trailing whitespace."""
    return str(value).strip()


@spl_tool
def ltrim(value: str) -> str:
    """LTRIM(value) — remove leading whitespace."""
    return str(value).lstrip()


@spl_tool
def rtrim(value: str) -> str:
    """RTRIM(value) — remove trailing whitespace."""
    return str(value).rstrip()


@spl_tool
def length(value: str) -> int:
    """LEN / LENGTH(value) — number of characters."""
    return len(str(value))


@spl_tool
def substr(value: str, start: str, length: str = "-1") -> str:
    """SUBSTR(value, start, length) — 1-based substring.
    If length is -1 (default), returns from start to end of string.
    """
    s = str(value)
    i = int(start) - 1          # convert 1-based to 0-based
    i = max(0, i)
    n = int(length)
    if n < 0:
        return s[i:]
    return s[i:i + n]


@spl_tool
def replace(value: str, old: str, new: str) -> str:
    """REPLACE(value, old, new) — replace all occurrences of old with new."""
    return str(value).replace(str(old), str(new))


@spl_tool
def concat(*args: str) -> str:
    """CONCAT(a, b, ...) — concatenate strings."""
    return "".join(str(a) for a in args)


@spl_tool
def instr(value: str, search: str) -> int:
    """INSTR(value, search) — 1-based index of first occurrence; 0 if not found."""
    idx = str(value).find(str(search))
    return idx + 1 if idx >= 0 else 0


@spl_tool
def lpad(value: str, width: str, fill: str = " ") -> str:
    """LPAD(value, width, fill) — left-pad string to given width."""
    return str(value).rjust(int(width), str(fill)[0] if fill else " ")


@spl_tool
def rpad(value: str, width: str, fill: str = " ") -> str:
    """RPAD(value, width, fill) — right-pad string to given width."""
    return str(value).ljust(int(width), str(fill)[0] if fill else " ")


@spl_tool
def split_part(value: str, delimiter: str, part: str) -> str:
    """SPLIT_PART(value, delimiter, part) — 1-based part after splitting on delimiter."""
    parts = str(value).split(str(delimiter))
    idx = int(part) - 1
    return parts[idx] if 0 <= idx < len(parts) else ""


@spl_tool
def reverse(value: str) -> str:
    """REVERSE(value) — reverse a string."""
    return str(value)[::-1]


# ── Pattern Matching ─────────────────────────────────────────────────────────

@spl_tool
def like(value: str, pattern: str) -> str:
    """LIKE(value, pattern) — SQL LIKE match; % = any chars, _ = any char.
    Returns 'true' or 'false'.
    """
    # Convert SQL wildcards BEFORE re.escape so they don't get escaped,
    # then escape everything else. Use placeholders to preserve intent.
    p = str(pattern)
    parts = re.split(r"(%|_)", p)
    regex = "".join(
        ".*" if tok == "%" else "." if tok == "_" else re.escape(tok)
        for tok in parts
    )
    return "true" if re.fullmatch(regex, str(value), re.IGNORECASE) else "false"


@spl_tool
def startswith(value: str, prefix: str) -> str:
    """STARTSWITH(value, prefix) — returns 'true' or 'false'."""
    return "true" if str(value).startswith(str(prefix)) else "false"


@spl_tool
def endswith(value: str, suffix: str) -> str:
    """ENDSWITH(value, suffix) — returns 'true' or 'false'."""
    return "true" if str(value).endswith(str(suffix)) else "false"


@spl_tool
def contains(value: str, substring: str) -> str:
    """CONTAINS(value, substring) — returns 'true' or 'false'."""
    return "true" if str(substring) in str(value) else "false"


@spl_tool
def regexp_match(value: str, pattern: str) -> str:
    """REGEXP_MATCH(value, pattern) — returns 'true' if pattern matches anywhere."""
    return "true" if re.search(str(pattern), str(value)) else "false"


# ── Numeric Functions ────────────────────────────────────────────────────────

@spl_tool
def abs_val(value: str) -> float:
    """ABS(value) — absolute value."""
    return abs(float(value))


@spl_tool
def round_val(value: str, decimals: str = "0") -> float:
    """ROUND(value, decimals) — round to N decimal places (default 0)."""
    return round(float(value), int(decimals))


@spl_tool
def ceil_val(value: str) -> int:
    """CEIL(value) — smallest integer >= value."""
    return math.ceil(float(value))


@spl_tool
def floor_val(value: str) -> int:
    """FLOOR(value) — largest integer <= value."""
    return math.floor(float(value))


@spl_tool
def mod_val(dividend: str, divisor: str) -> float:
    """MOD(dividend, divisor) — remainder of integer division."""
    return float(dividend) % float(divisor)


@spl_tool
def power_val(base: str, exponent: str) -> float:
    """POWER(base, exponent) — base raised to exponent."""
    return math.pow(float(base), float(exponent))


@spl_tool
def sqrt_val(value: str) -> float:
    """SQRT(value) — square root."""
    return math.sqrt(float(value))


@spl_tool
def sign_val(value: str) -> int:
    """SIGN(value) — returns -1, 0, or 1."""
    v = float(value)
    return 0 if v == 0 else (1 if v > 0 else -1)


@spl_tool
def clamp(value: str, lo: str, hi: str) -> float:
    """CLAMP(value, lo, hi) — constrain value to [lo, hi] range."""
    return max(float(lo), min(float(hi), float(value)))


# ── Conditional Functions ────────────────────────────────────────────────────

@spl_tool
def coalesce(*args: str) -> str:
    """COALESCE(a, b, ...) — return first non-null, non-empty argument."""
    for a in args:
        if a is not None and str(a).strip() != "":
            return str(a)
    return ""


@spl_tool
def nullif(value: str, compare: str) -> str:
    """NULLIF(value, compare) — return '' if value == compare, else value."""
    return "" if str(value) == str(compare) else str(value)


@spl_tool
def iif(condition: str, true_val: str, false_val: str) -> str:
    """IIF(condition, true_val, false_val) — inline if.
    Condition is true when: '1', 'true', 'yes' (case-insensitive).
    """
    truthy = str(condition).strip().lower() in {"1", "true", "yes", "t", "y"}
    return str(true_val) if truthy else str(false_val)


# ── Null / Empty Checks ──────────────────────────────────────────────────────

@spl_tool
def isnull(value: str) -> str:
    """ISNULL(value) — returns 'true' if value is None or empty string."""
    return "true" if (value is None or str(value).strip() == "") else "false"


@spl_tool
def nvl(value: str, default: str) -> str:
    """NVL(value, default) — return default if value is null/empty (Oracle-style)."""
    return str(default) if (value is None or str(value).strip() == "") else str(value)


@spl_tool
def isblank(value: str) -> str:
    """ISBLANK(value) — returns 'true' if value is empty or only whitespace."""
    return "true" if str(value).strip() == "" else "false"


# ── Text Aggregates ──────────────────────────────────────────────────────────

@spl_tool
def word_count(value: str) -> int:
    """Word count — number of whitespace-delimited tokens."""
    return len(str(value).split())


@spl_tool
def char_count(value: str) -> int:
    """Character count excluding whitespace."""
    return len(str(value).replace(" ", "").replace("\n", "").replace("\t", ""))


@spl_tool
def line_count(value: str) -> int:
    """Line count — number of newline-separated lines."""
    return len(str(value).splitlines())


# ── JSON Functions ───────────────────────────────────────────────────────────

@spl_tool
def json_get(json_str: str, key: str) -> str:
    """JSON_GET(json, key) — extract a top-level key from a JSON object string.
    Supports dot notation: 'a.b' extracts json['a']['b'].
    Returns '' if key not found or input is not valid JSON.
    """
    try:
        obj = json.loads(str(json_str))
        for part in str(key).split("."):
            if isinstance(obj, dict):
                obj = obj.get(part, "")
            else:
                return ""
        return str(obj) if obj != "" else ""
    except (json.JSONDecodeError, TypeError):
        return ""


@spl_tool
def json_set(json_str: str, key: str, value: str) -> str:
    """JSON_SET(json, key, value) — set a top-level key and return updated JSON string."""
    try:
        obj = json.loads(str(json_str)) if str(json_str).strip() else {}
    except json.JSONDecodeError:
        obj = {}
    obj[str(key)] = str(value)
    return json.dumps(obj, ensure_ascii=False)


@spl_tool
def json_keys(json_str: str) -> str:
    """JSON_KEYS(json) — return comma-separated list of top-level keys."""
    try:
        obj = json.loads(str(json_str))
        if isinstance(obj, dict):
            return ", ".join(obj.keys())
        return ""
    except (json.JSONDecodeError, TypeError):
        return ""


@spl_tool
def json_length(json_str: str) -> int:
    """JSON_LENGTH(json) — number of keys in object or items in array."""
    try:
        obj = json.loads(str(json_str))
        return len(obj)
    except (json.JSONDecodeError, TypeError):
        return 0


@spl_tool
def json_pretty(json_str: str) -> str:
    """JSON_PRETTY(json) — pretty-print JSON with 2-space indent."""
    try:
        return json.dumps(json.loads(str(json_str)), indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return str(json_str)


# ── Date / Time ──────────────────────────────────────────────────────────────

@spl_tool
def now_iso() -> str:
    """NOW() — current UTC datetime as ISO-8601 string: 'YYYY-MM-DDTHH:MM:SS'."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


@spl_tool
def date_format_val(iso_date: str, fmt: str) -> str:
    """DATE_FORMAT(date, format) — reformat an ISO date string using strftime format.
    Example: date_format_val('2026-03-23', '%B %d, %Y') → 'March 23, 2026'
    """
    for parse_fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(str(iso_date).strip(), parse_fmt)
            return dt.strftime(str(fmt))
        except ValueError:
            continue
    return str(iso_date)


@spl_tool
def date_diff_days(date_a: str, date_b: str) -> int:
    """DATEDIFF(date_a, date_b) — number of days between two ISO dates (a - b)."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            a = datetime.datetime.strptime(str(date_a).strip(), fmt)
            b = datetime.datetime.strptime(str(date_b).strip(), fmt)
            return (a - b).days
        except ValueError:
            continue
    return 0


# ── Hashing ──────────────────────────────────────────────────────────────────

@spl_tool
def md5_hash(value: str) -> str:
    """MD5(value) — MD5 hex digest (useful for deduplication keys)."""
    return hashlib.md5(str(value).encode()).hexdigest()


@spl_tool
def sha256_hash(value: str) -> str:
    """SHA256(value) — SHA-256 hex digest."""
    return hashlib.sha256(str(value).encode()).hexdigest()


# ── List / Array Helpers ─────────────────────────────────────────────────────

@spl_tool
def list_get(value: str, index: str, delimiter: str = ",") -> str:
    """LIST_GET(value, index, delimiter) — 1-based element from delimited list."""
    parts = str(value).split(str(delimiter))
    idx = int(index) - 1
    return parts[idx].strip() if 0 <= idx < len(parts) else ""


@spl_tool
def list_length(value: str, delimiter: str = ",") -> int:
    """LIST_LENGTH(value, delimiter) — number of elements in delimited list."""
    return len(str(value).split(str(delimiter)))


@spl_tool
def list_join(value: str, old_delim: str, new_delim: str) -> str:
    """LIST_JOIN(value, old_delim, new_delim) — re-join list with a new delimiter."""
    parts = [p.strip() for p in str(value).split(str(old_delim))]
    return str(new_delim).join(parts)


@spl_tool
def list_contains(value: str, item: str, delimiter: str = ",") -> str:
    """LIST_CONTAINS(value, item, delimiter) — 'true' if item is in delimited list."""
    parts = [p.strip() for p in str(value).split(str(delimiter))]
    return "true" if str(item).strip() in parts else "false"
