"""Python tools for recipe 06: Population Growth.

Registered via @spl_tool and loaded with:
    spl run ... --tools cookbook/06_react_agent/tools.py

CALL calc_growth_rate(@pop_prev, @pop_curr) INTO @rate
"""

from spl.tools import spl_tool


@spl_tool
def calc_growth_rate(pop_prev: str, pop_curr: str) -> str:
    """Compute year-over-year population growth rate.

    Formula: ((pop_curr - pop_prev) / pop_prev) * 100

    Args:
        pop_prev: Population in the previous year (may contain commas, spaces)
        pop_curr: Population in the current year (may contain commas, spaces)

    Returns:
        Growth rate as a string rounded to 4 decimal places, e.g. "0.8726"
    """
    def parse_pop(s: str) -> float:
        # Find the first sequence of digits (with optional commas) — the population number.
        # Using regex avoids grabbing stray digits from surrounding prose/years/decimals.
        import re
        # First try: a bare integer run (possibly comma-separated), at least 4 digits
        m = re.search(r"\b(\d[\d,]{3,})\b", s)
        if m:
            return float(m.group(1).replace(",", ""))
        # Fallback: any run of 4+ digits
        m = re.search(r"\d{4,}", s)
        if m:
            return float(m.group(0))
        raise ValueError(f"Could not parse population from: {s!r}")

    prev = parse_pop(pop_prev)
    curr = parse_pop(pop_curr)

    if prev == 0:
        raise ValueError("Previous population is zero — cannot compute growth rate")

    rate = ((curr - prev) / prev) * 100
    return f"{rate:.4f}"
