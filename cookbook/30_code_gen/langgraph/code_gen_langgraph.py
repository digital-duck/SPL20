"""
LangGraph equivalent of code_gen.spl

Pattern: Spec → Implement → Review → (fix if needed) → Test → Assemble

Usage:
    pip install langgraph langchain-ollama
    python cookbook/30_code_gen/langgraph/code_gen_langgraph.py \\
        --spec "A function that validates an email address"
"""

import click
import os
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class CodeGenState(TypedDict):
    spec:           str
    language:       str
    framework:      str
    model:          str
    log_dir:        str
    implementation: str
    review_notes:   str
    tests:          str
    final_output:   str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _load_spec(spec_input: str) -> str:
    if os.path.isfile(spec_input):
        return Path(spec_input).read_text(encoding="utf-8")
    return spec_input


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_init(state: CodeGenState) -> dict:
    spec = _load_spec(state["spec"])
    print(f"Spec resolved ({spec[:50]}...)")
    return {"spec": spec}

def node_implement(state: CodeGenState) -> dict:
    print(f"Generating {state['language']} implementation ...")
    prompt = f"Implement the following specification in {state['language']}:\n{state['spec']}"
    res = _invoke(state["model"], prompt)
    return {"implementation": res}

def node_review(state: CodeGenState) -> dict:
    print("Reviewing implementation ...")
    prompt = f"Review this {state['language']} implementation against the spec.\nSpec: {state['spec']}\nCode: {state['implementation']}\nIdentify any issues."
    res = _invoke(state["model"], prompt)
    return {"review_notes": res}

def node_fix(state: CodeGenState) -> dict:
    if any(word in state["review_notes"].lower() for word in ["issue", "error", "problem"]):
        print("Issues found — fixing implementation ...")
        prompt = f"Fix the following {state['language']} code based on the review notes.\nCode: {state['implementation']}\nNotes: {state['review_notes']}"
        res = _invoke(state["model"], prompt)
        return {"implementation": res}
    print("No issues found, skipping fix.")
    return {}

def node_test(state: CodeGenState) -> dict:
    print(f"Generating {state['framework']} tests ...")
    prompt = f"Generate unit tests for this {state['language']} implementation using the {state['framework']} framework.\nCode: {state['implementation']}\nSpec: {state['spec']}"
    res = _invoke(state["model"], prompt)
    return {"tests": res}

def node_assemble(state: CodeGenState) -> dict:
    print("Assembling final output ...")
    final = f"### Implementation\n\n{state['implementation']}\n\n### Unit Tests\n\n{state['tests']}"
    _write(f"{state['log_dir']}/final.md", final)
    return {"final_output": final}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(CodeGenState)
    g.add_node("init",      node_init)
    g.add_node("implement", node_implement)
    g.add_node("review",    node_review)
    g.add_node("fix",       node_fix)
    g.add_node("test",      node_test)
    g.add_node("assemble",  node_assemble)

    g.set_entry_point("init")
    g.add_edge("init",      "implement")
    g.add_edge("implement", "review")
    g.add_edge("review",    "fix")
    g.add_edge("fix",       "test")
    g.add_edge("test",      "assemble")
    g.add_edge("assemble",  END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--spec", required=True, help="Spec text or file path")
@click.option("--language", default="Python", help="Programming language")
@click.option("--framework", default="pytest", help="Test framework")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/30_code_gen/logs-langgraph", help="Log directory")
def main(spec, language, framework, model, log_dir):
    """Code Generator + Tests — LangGraph edition"""
    build_graph().invoke({
        "spec":           spec,
        "language":       language,
        "framework":      framework,
        "model":          model,
        "log_dir":        log_dir,
        "implementation": "",
        "review_notes":   "",
        "tests":          "",
        "final_output":   "",
    })

if __name__ == "__main__":
    main()
