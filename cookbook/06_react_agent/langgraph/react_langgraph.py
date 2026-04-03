"""
LangGraph equivalent of react_agent.spl

Pattern: CALL (deterministic tools) + GENERATE (single LLM narrative) + EXCEPTION

Key contrast with SPL:
  SPL separates CALL (0 LLM tokens, deterministic) from GENERATE (probabilistic).
  LangGraph has no such distinction — all nodes are Python functions; the programmer
  must manually track which steps invoke the LLM and which do not.

Usage:
    pip install langgraph langchain-ollama
    python cookbook/06_react_agent/langgraph/react_langgraph.py \\
        --country France --year 2023
    python cookbook/06_react_agent/langgraph/react_langgraph.py \\
        --country India --year 2023 --model llama3.2
"""

import click
import re
from pathlib import Path
from typing import Any, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


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
    # CALL search_population(@country, @year) — deterministic, zero LLM tokens
    key = (country.strip().title(), int(year))
    val = POPULATION_DATA.get(key)
    if val is None:
        raise ValueError(f"Population not found: {country} {year}")
    return val

def calc_growth_rate(pop_prev: str, pop_curr: str) -> str:
    # CALL calc_growth_rate(@pop_prev, @pop_curr) — pure Python math, zero LLM tokens
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


# ── Prompt (mirrors CREATE FUNCTION growth_report in react_agent.spl) ─────────

REPORT_PROMPT = """\
Write a concise 2-3 sentence population growth report for {country}.

Data:
- {year_prev} population: {pop_prev}
- {year_curr} population: {pop_curr}
- Year-over-year growth rate: {growth_rate}%

Plain prose only. No markdown headers. Just the narrative."""

ERROR_PROMPT = "Write a brief one-sentence error message: population data for {country} could not be retrieved."


# ── State ─────────────────────────────────────────────────────────────────────

class ReactState(TypedDict):
    country:     str
    year_curr:   int
    year_prev:   int
    model:       str
    log_dir:     str
    pop_prev:    str
    pop_curr:    str
    growth_rate: str
    report:      str
    error:       str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_search(state: ReactState) -> dict:
    # CALL search_population(@country, @year_prev) INTO @pop_prev
    # CALL search_population(@country, @year_curr) INTO @pop_curr
    print(f"Fetching population | {state['country']} {state['year_prev']}-{state['year_curr']} ...")
    try:
        pop_prev = search_population(state["country"], state["year_prev"])
        pop_curr = search_population(state["country"], state["year_curr"])
        return {"pop_prev": pop_prev, "pop_curr": pop_curr, "error": ""}
    except ValueError as e:
        return {"pop_prev": "", "pop_curr": "", "error": str(e)}

def node_calc(state: ReactState) -> dict:
    # CALL calc_growth_rate(@pop_prev, @pop_curr) INTO @growth_rate
    print("Computing growth rate ...")
    growth_rate = calc_growth_rate(state["pop_prev"], state["pop_curr"])
    return {"growth_rate": growth_rate}

def node_report(state: ReactState) -> dict:
    # GENERATE growth_report(...) INTO @report
    print("Generating report ...")
    report = _invoke(state["model"], REPORT_PROMPT.format(
        country=state["country"], year_prev=state["year_prev"],
        pop_prev=state["pop_prev"], year_curr=state["year_curr"],
        pop_curr=state["pop_curr"], growth_rate=state["growth_rate"],
    ))
    _write(f"{state['log_dir']}/report.md", report)
    return {"report": report}

def node_commit(state: ReactState) -> dict:
    # COMMIT @report WITH status = 'complete'
    _write(f"{state['log_dir']}/final.md", state["report"])
    print("Committed | status=complete")
    return {}

def node_error(state: ReactState) -> dict:
    # EXCEPTION WHEN SearchFailed THEN GENERATE search_error_report → COMMIT status='error'
    print(f"Error: {state['error']}")
    report = _invoke(state["model"], ERROR_PROMPT.format(country=state["country"]))
    _write(f"{state['log_dir']}/final.md", report)
    print("Committed | status=error")
    return {"report": report}


# ── Routing (mirrors EXCEPTION WHEN SearchFailed) ─────────────────────────────

def _route_after_search(state: ReactState) -> str:
    return "error" if state["error"] else "calc"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(ReactState)
    g.add_node("search", node_search)
    g.add_node("calc",   node_calc)
    g.add_node("report", node_report)
    g.add_node("commit", node_commit)
    g.add_node("error",  node_error)

    g.set_entry_point("search")
    g.add_conditional_edges("search", _route_after_search, {"calc": "calc", "error": "error"})
    g.add_edge("calc",   "report")
    g.add_edge("report", "commit")
    g.add_edge("commit", END)
    g.add_edge("error",  END)
    return g.compile()


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--country", default="China", help="Country to analyze")
@click.option("--year", type=int, default=2023, help="Year to analyze")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/06_react_agent/langgraph/logs", help="Log directory")
def main(country, year, model, log_dir):
    """ReAct Agent — LangGraph edition"""
    result = build_graph().invoke({
        "country":     country,
        "year_curr":   year,
        "year_prev":   year - 1,
        "model":       model,
        "log_dir":     log_dir,
        "pop_prev":    "", "pop_curr":    "",
        "growth_rate": "", "report":      "", "error": "",
    })
    print("\n" + "=" * 60)
    print(result["report"])

if __name__ == "__main__":
    main()
