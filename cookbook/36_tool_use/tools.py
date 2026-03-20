"""Python tools for recipe 36: Tool-Use / Function-Call.

Demonstrates registering deterministic Python functions as SPL CALL-able tools.
All computation here is pure Python — zero LLM calls, zero hallucination risk.

Load with:
    spl2 run cookbook/36_tool_use/tool_use.spl \
        --adapter ollama \
        --tools cookbook/36_tool_use/tools.py \
        sales="1200,1450,1380,1600,1750,1900"
"""

from spl2.tools import spl_tool


@spl_tool
def sum_values(csv: str) -> str:
    """Sum a comma-separated list of numbers."""
    values = [float(v.strip()) for v in csv.split(",") if v.strip()]
    return str(sum(values))


@spl_tool
def average_values(csv: str) -> str:
    """Compute the mean of a comma-separated list of numbers."""
    values = [float(v.strip()) for v in csv.split(",") if v.strip()]
    if not values:
        return "0"
    return f"{sum(values) / len(values):.2f}"


@spl_tool
def percentage_change(old: str, new: str) -> str:
    """Compute percentage change from old to new value.

    Returns a signed percentage string, e.g. "+18.42" or "-3.10".
    """
    old_f = float(old.replace(",", "").strip())
    new_f = float(new.replace(",", "").strip())
    if old_f == 0:
        return "N/A"
    change = ((new_f - old_f) / abs(old_f)) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f}"


@spl_tool
def min_value(csv: str) -> str:
    """Return the minimum value from a comma-separated list."""
    values = [float(v.strip()) for v in csv.split(",") if v.strip()]
    return str(min(values))


@spl_tool
def max_value(csv: str) -> str:
    """Return the maximum value from a comma-separated list."""
    values = [float(v.strip()) for v in csv.split(",") if v.strip()]
    return str(max(values))


@spl_tool
def format_currency(amount: str, symbol: str = "USD") -> str:
    """Format a numeric string as a currency string, e.g. 'USD 1,234.56'."""
    val = float(amount.replace(",", "").strip())
    return f"{symbol} {val:,.2f}"
