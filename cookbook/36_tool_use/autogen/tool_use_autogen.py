"""
AutoGen equivalent of tool_use.spl

Pattern: Plain Python math → LLM narrative generation.

Usage:
    pip install pyautogen
    python cookbook/36_tool_use/autogen/tool_use_autogen.py \\
        --sales "1200,1450,1380,1600,1750,1900" --prev_total "7800"
"""

import click
import os
import sys
from pathlib import Path

from autogen import ConversableAgent

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(sales: str, prev_total: str, period: str, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    analyst = ConversableAgent("Analyst", system_message="You are a sales analyst.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Deterministic math (plain Python)
    print("Step 1: Running deterministic tools ...")
    total = sum_values(sales)
    avg = average_values(sales)
    low = min_value(sales)
    high = max_value(sales)
    growth = percentage_change(prev_total, total)
    total_fmt = format_currency(total)
    avg_fmt = format_currency(avg)

    # Step 2: Narrative
    print("Step 2: Generating narrative report ...")
    prompt = f"""\
Generate a professional sales report for the period: {period}.
Raw Sales Data: {sales}
Total Sales: {total_fmt}
Average Sales: {avg_fmt}
Lowest: {low}
Highest: {high}
Growth since previous period: {growth}

Write a concise narrative analysis."""
    
    chat = analyst.initiate_chat(analyst, message=prompt, max_turns=1)
    report = chat.chat_history[-1]["content"]

    _write(f"{log_dir}/report.md", report)
    print("Committed | status=complete")


@click.command()
@click.option("--sales", default="1200,1450,1380,1600,1750,1900", help="CSV sales values")
@click.option("--prev_total", default="7800", help="Previous period total")
@click.option("--period", default="H1 2025", help="Reporting period")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/36_tool_use/logs-autogen", help="Log directory")
def main(sales, prev_total, period, model, log_dir):
    """Tool Use — AutoGen edition"""
    run(sales, prev_total, period, model, log_dir)

if __name__ == "__main__":
    main()
