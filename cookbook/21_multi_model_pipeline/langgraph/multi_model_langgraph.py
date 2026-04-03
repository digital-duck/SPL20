"""
LangGraph equivalent of multi_model.spl

Pattern: research → analyze → write → score → (pass? commit : refine → loop)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/21_multi_model_pipeline/langgraph/multi_model_langgraph.py \\
        --topic "climate change"
"""

import click
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class MultiModelState(TypedDict):
    topic:     str
    model:     str
    log_dir:   str
    max_refs:  int
    iteration: int
    score:     float
    facts:     str
    analysis:  str
    draft:     str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_research(state: MultiModelState) -> dict:
    print("Step 1: Research ...")
    facts = _invoke(state["model"], f"Gather key facts about: {state['topic']}")
    _write(f"{state['log_dir']}/research.md", facts)
    return {"facts": facts}

def node_analyze(state: MultiModelState) -> dict:
    print("Step 2: Analysis ...")
    analysis = _invoke(state["model"], f"Analyze these facts and find the 3 most significant insights:\n{state['facts']}")
    _write(f"{state['log_dir']}/analysis.md", analysis)
    return {"analysis": analysis}

def node_write(state: MultiModelState) -> dict:
    it = state.get("iteration", 0)
    print(f"Step 3: Writing (iteration {it}) ...")
    draft = _invoke(state["model"], f"Write a clear, engaging 2-paragraph summary based on this analysis:\n{state['analysis']}")
    _write(f"{state['log_dir']}/draft_{it}.md", draft)
    return {"draft": draft, "iteration": it}

def node_score(state: MultiModelState) -> dict:
    print("Step 4: Quality score ...")
    score_str = _invoke(state["model"], f"Rate the following text on a scale of 0.0 to 1.0 for clarity, accuracy, and completeness.\nText: {state['draft']}\nReply with ONLY the average number.")
    try:
        score = float(score_str.strip())
    except:
        score = 0.5
    print(f"Quality score: {score}")
    return {"score": score}

def node_refine(state: MultiModelState) -> dict:
    print("Refining draft ...")
    return {"iteration": state["iteration"] + 1}

def node_commit(state: MultiModelState) -> dict:
    _write(f"{state['log_dir']}/final.md", state["draft"])
    print("Committed | status=complete")
    return {}


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_after_score(state: MultiModelState) -> str:
    if state["score"] > 0.7 or state["iteration"] >= state["max_refs"]:
        return "commit"
    return "refine"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(MultiModelState)
    g.add_node("research", node_research)
    g.add_node("analyze",  node_analyze)
    g.add_node("write",    node_write)
    g.add_node("score",    node_score)
    g.add_node("refine",   node_refine)
    g.add_node("commit",   node_commit)

    g.set_entry_point("research")
    g.add_edge("research", "analyze")
    g.add_edge("analyze",  "write")
    g.add_edge("write",    "score")
    g.add_conditional_edges("score", _route_after_score, {"commit": "commit", "refine": "refine"})
    g.add_edge("refine",   "write")
    g.add_edge("commit",   END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic", required=True, help="Topic for the pipeline")
@click.option("--max-iterations", default=3, help="Max quality cycles")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/21_multi_model_pipeline/logs-langgraph", help="Log directory")
def main(topic, max_iterations, model, log_dir):
    """Multi-Model Pipeline — LangGraph edition"""
    build_graph().invoke({
        "topic":     topic,
        "model":     model,
        "log_dir":   log_dir,
        "max_refs":  max_iterations,
        "iteration": 0,
        "score":     0.0,
        "facts":     "",
        "analysis":  "",
        "draft":     "",
    })

if __name__ == "__main__":
    main()
