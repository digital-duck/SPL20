"""
LangGraph equivalent of tool_use.spl

Pattern: Deterministic tools (Python) → LLM Narrative

Usage:
    pip install langgraph langchain-ollama
    python cookbook/36_tool_use/langgraph/tool_use_langgraph.py \\
        --sales "1200,1450,1380,1600,1750,1900" --prev_total "7800"
"""

import click
import os
import sys
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

# Add parent to path to import tools
sys.path.append(str(Path(__file__).parent.parent))
try:
    from tools import sum_values, average_values, min_value, max_value, percentage_change, format_currency
except ImportError:
    def sum_values(c): return "0"
    def average_values(c): return "0"
    def min_value(c): return "0"
    def max_value(c): return "0"
    def percentage_change(o, n): return "0"
    def format_currency(a): return "0"


# ── State ─────────────────────────────────────────────────────────────────────

class SalesState(TypedDict):
    sales:      str
    prev_total: str
    period:     str
    model:      str
    log_dir:    str
    
    total:  str
    avg:    str
    low:    str
    high:   str
    growth: str
    report: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_math(state: SalesState) -> dict:
    print("Step 1: Running deterministic tools ...")
    total = sum_values(state["sales"])
    avg = average_values(state["sales"])
    low = min_value(state["sales"])
    high = max_value(state["sales"])
    growth = percentage_change(state["prev_total"], total)
    total_fmt = format_currency(total)
    avg_fmt = format_currency(avg)
    
    return {
        "total": total_fmt,
        "avg":   avg_fmt,
        "low":   low,
        "high":  high,
        "growth": growth
    }

def node_report(state: SalesState) -> dict:
    print("Step 2: Generating narrative report ...")
    prompt = f"""\
Generate a professional sales report for the period: {state['period']}.
Raw Sales Data: {state['sales']}
Total Sales: {state['total']}
Average Sales: {state['avg']}
Lowest: {state['low']}
Highest: {state['high']}
Growth since previous period: {state['growth']}

Write a concise narrative analysis."""
    report = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/report.md", report)
    return {"report": report}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(SalesState)
    g.add_node("math",   node_math)
    g.add_node("report", node_report)

    g.set_entry_point("math")
    g.add_edge("math",   "report")
    g.add_edge("report", END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--sales", default="1200,1450,1380,1600,1750,1900", help="CSV sales values")
@click.option("--prev_total", default="7800", help="Previous period total")
@click.option("--period", default="H1 2025", help="Reporting period")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/36_tool_use/logs-langgraph", help="Log directory")
def main(sales, prev_total, period, model, log_dir):
    """Tool Use — LangGraph edition"""
    build_graph().invoke({
        "sales":      sales,
        "prev_total": prev_total,
        "period":     period,
        "model":      model,
        "log_dir":    log_dir,
        "total": "", "avg": "", "low": "", "high": "", "growth": "", "report": ""
    })

if __name__ == "__main__":
    main()
