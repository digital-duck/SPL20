"""
LangGraph equivalent of reflection.spl

Pattern: solve → reflect → score → (confident? commit : correct → loop)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/16_reflection/langgraph/reflection_langgraph.py \\
        --problem "What are the trade-offs of microservices vs monoliths?"
"""

import click
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class ReflectionState(TypedDict):
    problem:    str
    model:      str
    log_dir:    str
    max_refs:   int
    iteration:  int
    confidence: float
    answer:     str
    reflection: str
    issues:     str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_solve(state: ReflectionState) -> dict:
    print("Initial solution ...")
    answer = _invoke(state["model"], f"Solve this problem: {state['problem']}")
    _write(f"{state['log_dir']}/answer_0.md", answer)
    return {"answer": answer, "iteration": 0}

def node_reflect(state: ReflectionState) -> dict:
    print(f"Reflection iteration {state['iteration']} ...")
    ref = _invoke(state["model"], f"Reflect on this answer for the problem '{state['problem']}':\n{state['answer']}")
    _write(f"{state['log_dir']}/reflection_{state['iteration']}.md", ref)
    return {"reflection": ref}

def node_score(state: ReflectionState) -> dict:
    score_str = _invoke(state["model"], f"Rate your confidence (0.0 to 1.0) in the answer based on the reflection.\nAnswer: {state['answer']}\nReflection: {state['reflection']}\nReply with ONLY the number.")
    try:
        score = float(score_str)
    except:
        score = 0.5
    print(f"Confidence: {score}")
    return {"confidence": score}

def node_correct(state: ReflectionState) -> dict:
    print("Correcting answer ...")
    issues = _invoke(state["model"], f"Extract specific issues to fix from this reflection:\n{state['reflection']}")
    answer = _invoke(state["model"], f"Correct this answer based on the issues identified.\nAnswer: {state['answer']}\nIssues: {issues}\nProblem: {state['problem']}")
    it = state["iteration"] + 1
    _write(f"{state['log_dir']}/answer_{it}.md", answer)
    return {"answer": answer, "iteration": it, "issues": issues}

def node_commit(state: ReflectionState) -> dict:
    _write(f"{state['log_dir']}/final.md", state["answer"])
    print("Committed | status=complete")
    return {}


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_after_score(state: ReflectionState) -> str:
    if state["confidence"] > 0.85 or state["iteration"] >= state["max_refs"]:
        return "commit"
    return "correct"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(ReflectionState)
    g.add_node("solve",   node_solve)
    g.add_node("reflect", node_reflect)
    g.add_node("score",   node_score)
    g.add_node("correct", node_correct)
    g.add_node("commit",  node_commit)

    g.set_entry_point("solve")
    g.add_edge("solve",   "reflect")
    g.add_edge("reflect", "score")
    g.add_conditional_edges("score", _route_after_score, {"commit": "commit", "correct": "correct"})
    g.add_edge("correct", "reflect")
    g.add_edge("commit",  END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--problem", required=True, help="Problem to solve")
@click.option("--max-reflections", default=3, help="Max reflection cycles")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/16_reflection/logs-langgraph", help="Log directory")
def main(problem, max_reflections, model, log_dir):
    """Reflection Agent — LangGraph edition"""
    build_graph().invoke({
        "problem":    problem,
        "model":      model,
        "log_dir":    log_dir,
        "max_refs":   max_reflections,
        "iteration":  0,
        "confidence": 0.0,
        "answer":     "",
        "reflection": "",
        "issues":     "",
    })

if __name__ == "__main__":
    main()
