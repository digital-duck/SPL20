"""
LangGraph equivalent of code_review.spl

Pattern: Detect Lang → [Security, Performance, Style, Bug Analysis] → Synthesize

Usage:
    pip install langgraph langchain-ollama
    python cookbook/15_code_review/langgraph/code_review_langgraph.py \\
        --code "def foo(x): return eval(x)"
"""

import click
import os
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class ReviewState(TypedDict):
    code:        str
    language:    str
    model:       str
    log_dir:     str
    security:    str
    performance: str
    style:       str
    bugs:        str
    review:      str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _read_code(code_input: str) -> str:
    if os.path.isfile(code_input):
        return Path(code_input).read_text(encoding="utf-8")
    return code_input


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_detect(state: ReviewState) -> dict:
    code = _read_code(state["code"])
    print("Detecting language ...")
    lang = _invoke(state["model"], f"Identify the programming language of this code:\n{code[:500]}")
    return {"code": code, "language": lang}

def node_security(state: ReviewState) -> dict:
    print("Pass 1: Security audit ...")
    res = _invoke(state["model"], f"Perform a security audit of this {state['language']} code:\n{state['code']}")
    _write(f"{state['log_dir']}/security.md", res)
    return {"security": res}

def node_performance(state: ReviewState) -> dict:
    print("Pass 2: Performance review ...")
    res = _invoke(state["model"], f"Review the performance of this {state['language']} code:\n{state['code']}")
    _write(f"{state['log_dir']}/performance.md", res)
    return {"performance": res}

def node_style(state: ReviewState) -> dict:
    print("Pass 3: Style review ...")
    res = _invoke(state["model"], f"Review the style and best practices of this {state['language']} code:\n{state['code']}")
    _write(f"{state['log_dir']}/style.md", res)
    return {"style": res}

def node_bugs(state: ReviewState) -> dict:
    print("Pass 4: Bug detection ...")
    res = _invoke(state["model"], f"Find potential bugs in this {state['language']} code:\n{state['code']}")
    _write(f"{state['log_dir']}/bugs.md", res)
    return {"bugs": res}

def node_synthesize(state: ReviewState) -> dict:
    print("Synthesizing findings ...")
    prompt = (
        f"Synthesize these code review findings for {state['language']} code into a final report:\n"
        f"Security: {state['security']}\n"
        f"Performance: {state['performance']}\n"
        f"Style: {state['style']}\n"
        f"Bugs: {state['bugs']}"
    )
    review = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/review.md", review)
    return {"review": review}

def node_commit(state: ReviewState) -> dict:
    _write(f"{state['log_dir']}/final.md", state["review"])
    print("Committed | status=complete")
    return {}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(ReviewState)
    g.add_node("detect",      node_detect)
    g.add_node("security",    node_security)
    g.add_node("performance", node_performance)
    g.add_node("style",       node_style)
    g.add_node("bugs",        node_bugs)
    g.add_node("synthesize",  node_synthesize)
    g.add_node("commit",      node_commit)

    g.set_entry_point("detect")
    g.add_edge("detect",      "security")
    g.add_edge("security",    "performance")
    g.add_edge("performance", "style")
    g.add_edge("style",       "bugs")
    g.add_edge("bugs",        "synthesize")
    g.add_edge("synthesize",  "commit")
    g.add_edge("commit",      END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--code", required=True, help="Code to review or path to file")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/15_code_review/logs-langgraph", help="Log directory")
def main(code, model, log_dir):
    """Automated Code Review — LangGraph edition"""
    build_graph().invoke({
        "code":        code,
        "language":    "",
        "model":       model,
        "log_dir":     log_dir,
        "security":    "",
        "performance": "",
        "style":       "",
        "bugs":        "",
        "review":      "",
    })

if __name__ == "__main__":
    main()
