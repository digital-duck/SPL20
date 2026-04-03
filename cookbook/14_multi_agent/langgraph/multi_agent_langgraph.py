"""
LangGraph equivalent of multi_agent.spl

Pattern: Researcher → Analyst → Writer

Usage:
    pip install langgraph langchain-ollama
    python cookbook/14_multi_agent/langgraph/multi_agent_langgraph.py \\
        --topic "Impact of AI on healthcare"
"""

import click
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class MultiAgentState(TypedDict):
    topic:    str
    model:    str
    log_dir:  str
    research: str
    analysis: str
    report:   str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_researcher(state: MultiAgentState) -> dict:
    print("Agent 1: Researcher ...")
    facts = _invoke(state["model"], f"Gather key facts and sources for the topic: {state['topic']}")
    themes = _invoke(state["model"], f"Identify key themes from these facts:\n{facts}")
    research = facts + "\n\nKey Themes:\n" + themes
    _write(f"{state['log_dir']}/research.md", research)
    return {"research": research}

def node_analyst(state: MultiAgentState) -> dict:
    print("Agent 2: Analyst ...")
    trends = _invoke(state["model"], f"Analyze trends based on this research:\n{state['research']}")
    risks = _invoke(state["model"], f"Assess risks for the topic {state['topic']} based on:\n{state['research']}")
    opportunities = _invoke(state["model"], f"Find opportunities for {state['topic']} based on:\n{state['research']}")
    analysis = f"Trends:\n{trends}\n\nRisks:\n{risks}\n\nOpportunities:\n{opportunities}"
    _write(f"{state['log_dir']}/analysis.md", analysis)
    return {"analysis": analysis}

def node_writer(state: MultiAgentState) -> dict:
    print("Agent 3: Writer ...")
    draft = _invoke(state["model"], f"Draft a report on {state['topic']} using:\nResearch:\n{state['research']}\nAnalysis:\n{state['analysis']}")
    feedback = _invoke(state["model"], f"Critique this report draft:\n{draft}")
    report = _invoke(state["model"], f"Revise this report draft based on feedback:\nDraft:\n{draft}\nFeedback:\n{feedback}")
    _write(f"{state['log_dir']}/report.md", report)
    return {"report": report}

def node_commit(state: MultiAgentState) -> dict:
    _write(f"{state['log_dir']}/final.md", state["report"])
    print("Committed | status=complete")
    return {}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(MultiAgentState)
    g.add_node("researcher", node_researcher)
    g.add_node("analyst",    node_analyst)
    g.add_node("writer",     node_writer)
    g.add_node("commit",     node_commit)

    g.set_entry_point("researcher")
    g.add_edge("researcher", "analyst")
    g.add_edge("analyst",    "writer")
    g.add_edge("writer",     "commit")
    g.add_edge("commit",     END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic", required=True, help="Topic for the report")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/14_multi_agent/logs-langgraph", help="Log directory")
def main(topic, model, log_dir):
    """Multi-Agent Collaboration — LangGraph edition"""
    build_graph().invoke({
        "topic":    topic,
        "model":    model,
        "log_dir":  log_dir,
        "research": "",
        "analysis": "",
        "report":   "",
    })

if __name__ == "__main__":
    main()
