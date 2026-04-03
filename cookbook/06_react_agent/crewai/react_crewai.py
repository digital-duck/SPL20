"""
CrewAI equivalent of react_agent.spl

Pattern: @tool decorators wrap deterministic functions; single LLM Agent
generates the final report. CrewAI has no CALL/GENERATE distinction —
both tool calls and LLM invocations are handled by the same Agent.

Usage:
    pip install crewai langchain-ollama
    python cookbook/06_react_agent/crewai/react_crewai.py \\
        --country France --year 2023
    python cookbook/06_react_agent/crewai/react_crewai.py \\
        --country India --year 2023 --model llama3.2
"""

import click
import re
from pathlib import Path

from crewai import Agent, Crew, Task
from crewai.tools import tool
from langchain_ollama import ChatOllama


# ── Tool implementations (mirrors CALL targets in react_agent.spl) ────────────

POPULATION_DATA = {
    ("China",   2022): "1412000000", ("China",   2023): "1409670000",
    ("France",  2022): "67750000",   ("France",  2023): "68170000",
    ("USA",     2022): "333300000",  ("USA",     2023): "335900000",
    ("India",   2022): "1417000000", ("India",   2023): "1428600000",
    ("Germany", 2022): "84300000",   ("Germany", 2023): "84480000",
    ("Brazil",  2022): "215300000",  ("Brazil",  2023): "216400000",
}

@tool("search_population")
def search_population_tool(query: str) -> str:
    """Look up population for a country and year. Input format: 'CountryName YYYY'"""
    # CALL search_population — deterministic, zero LLM tokens in SPL
    parts = query.strip().rsplit(" ", 1)
    if len(parts) != 2:
        return f"Error: expected 'Country YEAR', got: {query}"
    country, year_str = parts[0].strip().title(), parts[1].strip()
    try:
        year = int(year_str)
        key = (country, year)
        val = POPULATION_DATA.get(key)
        if val is None:
            return f"Error: population not found for {country} {year}"
        return val
    except ValueError:
        return f"Error: invalid year: {year_str}"

@tool("calc_growth_rate")
def calc_growth_rate_tool(populations: str) -> str:
    """Compute year-over-year growth rate. Input format: 'POP_PREV POP_CURR'"""
    # CALL calc_growth_rate — pure Python math, zero LLM tokens in SPL
    def parse_pop(s: str) -> float:
        m = re.search(r"\b(\d[\d,]{3,})\b", s)
        if m:
            return float(m.group(1).replace(",", ""))
        m = re.search(r"\d{4,}", s)
        if m:
            return float(m.group(0))
        raise ValueError(f"Cannot parse: {s!r}")
    parts = populations.strip().split()
    if len(parts) < 2:
        return "Error: expected two population values"
    try:
        prev, curr = parse_pop(parts[0]), parse_pop(parts[1])
        if prev == 0:
            return "Error: previous population is zero"
        return f"{((curr - prev) / prev) * 100:.4f}"
    except ValueError as e:
        return f"Error: {e}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(country: str, year_curr: int, model: str, log_dir: str) -> str:
    year_prev = year_curr - 1
    # Standardize to the 'ollama/' prefix for robust local model support
    llm = f"ollama/{model}"

    analyst = Agent(
        role="Population Analyst",
        goal="Look up population data and compute growth rates, then write a report",
        backstory="Expert data analyst who retrieves population statistics and "
                  "computes growth metrics before writing concise reports.",
        tools=[search_population_tool, calc_growth_rate_tool],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Analyze population growth for {country} from {year_prev} to {year_curr}.\n\n"
            f"Steps:\n"
            f"1. Use search_population to get the {year_prev} population: '{country} {year_prev}'\n"
            f"2. Use search_population to get the {year_curr} population: '{country} {year_curr}'\n"
            f"3. Use calc_growth_rate with the two populations\n"
            f"4. Write a concise 2-3 sentence report in plain prose.\n\n"
            "If population data is unavailable, write a brief error message instead."
        ),
        expected_output="A concise 2-3 sentence population growth report in plain prose.",
        agent=analyst,
    )

    # GENERATE growth_report (via agent LLM) + COMMIT
    print(f"Running population growth analysis | {country} {year_prev}-{year_curr} ...")
    crew = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()
    report = str(result)

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
@click.option("--log-dir", default="cookbook/06_react_agent/crewai/logs", help="Log directory")
def main(country, year, model, log_dir):
    """ReAct Agent — CrewAI edition"""
    result = run(country, year, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
