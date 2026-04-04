"""
LangGraph equivalent of tree_of_thought.spl

Pattern: initial_approach + develop → evaluate_path → (repeat for N models) → select_best → refine → verify → (synthesize if needed)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/17_tree_of_thought/langgraph/tree_of_thought_langgraph.py \
        --problem "Design a sustainable urban transport system."
"""

import argparse
import re
from pathlib import Path
from typing import TypedDict, List, Dict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors CREATE FUNCTION in tree_of_thought.spl) ────────────────

INITIAL_APPROACH_PROMPT = """\
Provide an initial high-level approach or reasoning path for the following problem:
{problem}

Focus on a unique perspective or specialized methodology.
"""

DEVELOP_PROMPT = """\
Take the following initial approach and develop it one level deeper, adding specific steps and technical details:
Approach: {path}
Problem: {problem}
"""

EVALUATE_PATH_PROMPT = """\
Score the following reasoning path on a scale of 1-10 based on its feasibility and depth.
Problem: {problem}
Path: {path}

Output only the numeric score.
"""

SELECT_BEST_PROMPT = """\
Review the following developed reasoning paths and their scores provided in a JSON-like format:
{results_map}

Problem: {problem}

Identify the path with the best reasoning and provide the content of that path as the output.
"""

REFINE_SOLUTION_PROMPT = """\
Refine the following reasoning path into a complete, polished solution for the problem.
Problem: {problem}
Path: {path}
"""

VERIFY_PROMPT = """\
Verify if the following solution is sound and fully addresses the problem.
Problem: {problem}
Solution: {solution}

Output 'sound' if it is correct, otherwise provide a brief critique.
"""

SYNTHESIZE_ALL_PROMPT = """\
Synthesize insights from all the following reasoning paths to create a comprehensive final solution.
Problem: {problem}
Paths: {results_map}
"""


# ── State ────────────────────────────────────────────────────────────────────

class TOTState(TypedDict):
    problem:       str
    models:        List[str]
    current_model_idx: int
    log_dir:       str
    
    results:       Dict[str, Dict[str, str]] # model -> {content, score}
    best_path:     str
    solution:      str
    verification:  str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_explore_path(state: TOTState) -> dict:
    idx = state["current_model_idx"]
    model = state["models"][idx]
    problem = state["problem"]
    
    print(f"Exploring path {idx + 1}/{len(state['models'])} using {model}...")
    
    init_path = _invoke(model, INITIAL_APPROACH_PROMPT.format(problem=problem))
    developed_path = _invoke(model, DEVELOP_PROMPT.format(path=init_path, problem=problem))
    score_str = _invoke(model, EVALUATE_PATH_PROMPT.format(path=developed_path, problem=problem))
    
    _write(f"{state['log_dir']}/path_{model}.md", developed_path)
    
    new_results = state["results"].copy()
    new_results[model] = {
        "content": developed_path,
        "score": score_str
    }
    
    return {
        "results": new_results,
        "current_model_idx": idx + 1
    }

def node_select_best(state: TOTState) -> dict:
    print("Selecting best path ...")
    best_path = _invoke(state["models"][0], SELECT_BEST_PROMPT.format(
        results_map=str(state["results"]),
        problem=state["problem"]
    ))
    return {"best_path": best_path}

def node_refine(state: TOTState) -> dict:
    print("Refining winning path ...")
    solution = _invoke(state["models"][0], REFINE_SOLUTION_PROMPT.format(
        path=state["best_path"],
        problem=state["problem"]
    ))
    return {"solution": solution}

def node_verify(state: TOTState) -> dict:
    print("Verifying solution ...")
    verification = _invoke(state["models"][0], VERIFY_PROMPT.format(
        solution=state["solution"],
        problem=state["problem"]
    ))
    _write(f"{state['log_dir']}/verification.md", verification)
    return {"verification": verification}

def node_synthesize(state: TOTState) -> dict:
    print("Verification failed — synthesizing all paths ...")
    solution = _invoke(state["models"][0], SYNTHESIZE_ALL_PROMPT.format(
        results_map=str(state["results"]),
        problem=state["problem"]
    ))
    _write(f"{state['log_dir']}/final_solution.md", solution)
    return {"solution": solution}

def node_finalize(state: TOTState) -> dict:
    _write(f"{state['log_dir']}/final_solution.md", state["solution"])
    return {}


# ── Routing ──────────────────────────────────────────────────────────────────

def _route_exploration(state: TOTState) -> str:
    if state["current_model_idx"] < len(state["models"]):
        return "explore"
    return "select"

def _route_verification(state: TOTState) -> str:
    if "sound" in state["verification"].lower():
        return "finalize"
    return "synthesize"


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(TOTState)
    g.add_node("explore",    node_explore_path)
    g.add_node("select",     node_select_best)
    g.add_node("refine",     node_refine)
    g.add_node("verify",     node_verify)
    g.add_node("synthesize", node_synthesize)
    g.add_node("finalize",   node_finalize)

    g.set_entry_point("explore")
    
    g.add_conditional_edges("explore", _route_exploration, {
        "explore": "explore",
        "select": "select"
    })
    
    g.add_edge("select", "refine")
    g.add_edge("refine", "verify")
    
    g.add_conditional_edges("verify", _route_verification, {
        "finalize": "finalize",
        "synthesize": "synthesize"
    })
    
    g.add_edge("synthesize", "finalize")
    g.add_edge("finalize", END)
    
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Tree of Thought — LangGraph edition")
    p.add_argument("--problem",   default="Design a sustainable urban transport system.")
    p.add_argument("--models",    nargs="+", default=["gemma3", "phi4", "qwen2.5"])
    p.add_argument("--log-dir",   default="cookbook/17_tree_of_thought/langgraph/logs-langgraph")
    args = p.parse_args()

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "problem":           args.problem,
        "models":            args.models,
        "current_model_idx": 0,
        "log_dir":           args.log_dir,
        "results":           {},
        "best_path":         "",
        "solution":          "",
        "verification":      "",
    })

    print("\n" + "=" * 60)
    print("FINAL SOLUTION:")
    print(result["solution"])

if __name__ == "__main__":
    main()
