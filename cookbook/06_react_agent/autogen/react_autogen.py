"""
AutoGen equivalent of react_agent.spl

Pattern: deterministic tool calls (plain Python) + single LLM GENERATE + EXCEPTION

AutoGen's function_map wires Python functions as callable tools. However,
there is no language-level distinction between deterministic CALL and
probabilistic GENERATE — both are just Python. The programmer must enforce
this discipline manually.

Usage:
    pip install pyautogen
    python cookbook/06_react_agent/autogen/react_autogen.py \\
        --country France --year 2023
    python cookbook/06_react_agent/autogen/react_autogen.py \\
        --country India --year 2023 --model llama3.2
"""

import click
import re
from pathlib import Path

from autogen import ConversableAgent


# ── Tool implementations (mirrors CALL targets in react_agent.spl) ────────────

POPULATION_DATA = {
    ("China",   2022): "1412000000", ("China",   2023): "1409670000",
    ("France",  2022): "67750000",   ("France",  2023): "68170000",
    ("USA",     2022): "333300000",  ("USA",     2023): "335900000",
    ("India",   2022): "1417000000", ("India",   2023): "1428600000",
    ("Germany", 2022): "84300000",   ("Germany", 2023): "84480000",
    ("Brazil",  2022): "215300000",  ("Brazil",  2023): "216400000",
}

def search_population(country: str, year: int) -> str:
    # CALL search_population — deterministic, zero LLM tokens
    key = (country.strip().title(), int(year))
    val = POPULATION_DATA.get(key)
    if val is None:
        raise ValueError(f"Population not found: {country} {year}")
    return val

def calc_growth_rate(pop_prev: str, pop_curr: str) -> str:
    # CALL calc_growth_rate — pure Python math, zero LLM tokens
    def parse_pop(s: str) -> float:
        m = re.search(r"\b(\d[\d,]{3,})\b", s)
        if m:
            return float(m.group(1).replace(",", ""))
        m = re.search(r"\d{4,}", s)
        if m:
            return float(m.group(0))
        raise ValueError(f"Could not parse population from: {s!r}")
    prev = parse_pop(pop_prev)
    curr = parse_pop(pop_curr)
    if prev == 0:
        raise ValueError("Previous population is zero")
    return f"{((curr - prev) / prev) * 100:.4f}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(country: str, year_curr: int, model: str, log_dir: str) -> str:
    year_prev = year_curr - 1
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # EXCEPTION WHEN SearchFailed — explicit try/except (no language primitive)
    try:
        # CALL search_population(@country, @year_prev) INTO @pop_prev
        print(f"Fetching population | {country} {year_prev}-{year_curr} ...")
        pop_prev = search_population(country, year_prev)
        pop_curr = search_population(country, year_curr)
    except ValueError as e:
        # EXCEPTION WHEN SearchFailed THEN GENERATE search_error_report
        proxy = ConversableAgent("proxy", llm_config=False, human_input_mode="NEVER")
        reporter = ConversableAgent("Reporter", llm_config=llm_config, human_input_mode="NEVER", max_consecutive_auto_reply=1)
        r = proxy.initiate_chat(reporter, message=f"Write a brief one-sentence error: population data for {country} could not be retrieved.", max_turns=1)
        report = r.chat_history[-1]["content"]
        _write(f"{log_dir}/final.md", report)
        print("Committed | status=error")
        return report

    # CALL calc_growth_rate(@pop_prev, @pop_curr) INTO @growth_rate
    print("Computing growth rate ...")
    growth_rate = calc_growth_rate(pop_prev, pop_curr)

    # GENERATE growth_report(...) INTO @report — single LLM call
    print("Generating report ...")
    proxy = ConversableAgent("proxy", llm_config=False, human_input_mode="NEVER")
    reporter = ConversableAgent(
        "Reporter",
        system_message="You write concise population growth reports in plain prose.",
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
    )
    message = (
        f"Write a concise 2-3 sentence population growth report for {country}.\n\n"
        f"Data:\n- {year_prev} population: {pop_prev}\n"
        f"- {year_curr} population: {pop_curr}\n"
        f"- Year-over-year growth rate: {growth_rate}%\n\n"
        "Plain prose only. No markdown headers."
    )
    result = proxy.initiate_chat(reporter, message=message, max_turns=1)
    report = result.chat_history[-1]["content"]

    # COMMIT @report WITH status = 'complete'
    _write(f"{log_dir}/report.md", report)
    _write(f"{log_dir}/final.md", report)
    print("Committed | status=complete")
    return report


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--country", default="China", help="Country to analyze")
@click.option("--year", type=int, default=2023, help="Year to analyze")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/06_react_agent/autogen/logs", help="Log directory")
def main(country, year, model, log_dir):
    """ReAct Agent — AutoGen edition"""
    result = run(country, year, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
