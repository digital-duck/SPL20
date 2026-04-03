"""
LangGraph equivalent of nested_procs.spl

Pattern: research → explain_layer → make_example → calibrate_complexity → assemble

Usage:
    pip install langgraph langchain-ollama
    python cookbook/25_nested_procs/langgraph/nested_procs_langgraph.py \\
        --topic "quantum computing" --audience "high school students"
"""

import click
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class NestedState(TypedDict):
    topic:       str
    audience:    str
    depth:       str
    model:       str
    log_dir:     str
    overview:    str
    base_exp:    str
    example:     str
    calibrated:  str
    article:     str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes (Sub-procedures modeled as functions) ───────────────────────────────

def node_research(state: NestedState) -> dict:
    print("Step 1: Research overview ...")
    overview = _invoke(state["model"], f"Provide a research overview for the topic: {state['topic']}")
    return {"overview": overview}

def node_explain(state: NestedState) -> dict:
    print("Step 2: Explaining layer ...")
    base_exp = _invoke(state["model"], f"Explain this content for a {state['audience']} audience in a clear, engaging style:\n{state['overview']}")
    return {"base_exp": base_exp}

def node_example(state: NestedState) -> dict:
    print("Step 3: Creating example ...")
    example = _invoke(state["model"], f"Generate a concrete example for the concept '{state['topic']}' for a {state['audience']} audience, based on this context:\n{state['base_exp']}")
    return {"example": example}

def node_calibrate(state: NestedState) -> dict:
    print("Step 4: Calibrating complexity ...")
    level_str = _invoke(state["model"], f"Assess the reading grade level of this text (reply with only a number):\n{state['base_exp']}")
    try:
        level = int(level_str.strip())
    except:
        level = 10
    
    if level > 8:
        print(f"Reading level {level} too high, simplifying ...")
        calibrated = _invoke(state["model"], f"Simplify this text for a {state['audience']} audience:\n{state['base_exp']}")
    else:
        calibrated = state["base_exp"]
    return {"calibrated": calibrated}

def node_assemble(state: NestedState) -> dict:
    print("Step 5: Assembling article ...")
    article = _invoke(state["model"], f"Assemble a final {state['depth']} depth article on {state['topic']} for {state['audience']} using:\nExplanation: {state['calibrated']}\nExample: {state['example']}")
    _write(f"{state['log_dir']}/final.md", article)
    return {"article": article}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(NestedState)
    g.add_node("research",  node_research)
    g.add_node("explain",   node_explain)
    g.add_node("example",   node_example)
    g.add_node("calibrate", node_calibrate)
    g.add_node("assemble",  node_assemble)

    g.set_entry_point("research")
    g.add_edge("research",  "explain")
    g.add_edge("explain",   "example")
    g.add_edge("example",   "calibrate")
    g.add_edge("calibrate", "assemble")
    g.add_edge("assemble",  END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic", required=True, help="Topic to explain")
@click.option("--audience", required=True, help="Target audience")
@click.option("--depth", default="standard", help="Article depth")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/25_nested_procs/logs-langgraph", help="Log directory")
def main(topic, audience, depth, model, log_dir):
    """Nested Procedures — LangGraph edition"""
    build_graph().invoke({
        "topic":      topic,
        "audience":   audience,
        "depth":      depth,
        "model":      model,
        "log_dir":    log_dir,
        "overview":   "",
        "base_exp":   "",
        "example":    "",
        "calibrated": "",
        "article":    "",
    })

if __name__ == "__main__":
    main()
