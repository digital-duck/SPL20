"""
tools.py — Python tools for Recipe 28: Customer Support Triage.

Tools:
  extract_order_numbers(text)       Regex-extract ORD-##### references from ticket text.
  lookup_order(order_numbers)       Fetch full order record(s) from orders.json by order ID.

Usage:
  spl run cookbook/28_support_triage/support_triage.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/28_support_triage/tools.py \\
      ticket="My account has been charged twice for order #ORD-12345"
"""

import json
import os
import re

from spl.tools import spl_tool

_ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.json")


def _load_orders() -> list[dict]:
    with open(_ORDERS_FILE, encoding="utf-8") as fh:
        return json.load(fh)


@spl_tool
def extract_order_numbers(text: str) -> str:
    """
    Extract order numbers from a support ticket.

    Recognises these patterns (case-insensitive):
      ORD-12345          explicit prefixed ID
      ORDER-12345        alternative prefix
      #12345             hash + digits
      order #12345       natural-language reference
      order number 12345 natural-language reference

    Returns a comma-separated list of normalised IDs (e.g. 'ORD-12345, ORD-67890')
    or an empty string if none are found.
    """
    patterns = [
        r'\bORD-(\d{5,})\b',
        r'\bORDER-(\d{5,})\b',
        r'#(\d{5,})\b',
        r'\border\s+(?:number\s+)?#?(\d{5,})\b',
    ]
    found: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            oid = f"ORD-{m.group(1)}"
            if oid not in seen:
                seen.add(oid)
                found.append(oid)
    return ", ".join(found)


@spl_tool
def lookup_order(order_numbers: str) -> str:
    """
    Look up one or more order IDs (comma-separated) in orders.json.

    Returns a JSON object with full order record(s) under the key "orders_found".
    Unknown IDs are listed under "orders_not_found".
    If order_numbers is blank, returns a short message so the LLM knows no order
    was referenced and should respond based on the ticket text alone.
    """
    order_numbers = order_numbers.strip()
    if not order_numbers:
        return "No order number found in this ticket."

    orders = _load_orders()
    index = {o["order_id"].upper(): o for o in orders}

    found: list[dict] = []
    missing: list[str] = []

    for raw in order_numbers.split(","):
        oid = raw.strip().upper()
        if oid in index:
            found.append(index[oid])
        else:
            missing.append(oid)

    if not found:
        ids = ", ".join(missing)
        return (
            f"Order(s) not found in system: {ids}. "
            "The customer may have misquoted the order number. "
            "Ask the customer to confirm the order ID."
        )

    payload: dict = {"orders_found": found}
    if missing:
        payload["orders_not_found"] = missing

    return json.dumps(payload, indent=2, default=str)
