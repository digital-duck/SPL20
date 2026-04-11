"""
LangGraph equivalent of debate.spl

Pattern: pro_opening → con_opening → (pro_rebuttal → con_rebuttal) x N rounds → judge

Usage:
    pip install langgraph langchain-ollama
    python cookbook/11_debate_arena/langgraph/debate_langgraph.py --topic "AI should be open-sourced"
"""

import click
from pathlib import Path
from typing import TypedDict, Annotated
import operator

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors CREATE FUNCTION in debate.spl) ─────────────────────────

PRO_PROMPT = """\
You are a skilled debate champion arguing STRONGLY IN FAVOR of the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument supporting the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side.
"""

CON_PROMPT = """\
You are a skilled debate champion arguing STRONGLY AGAINST the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument opposing the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side.
"""

JUDGE_PROMPT = """\
You are an impartial debate judge evaluating the following debate.

Motion: "{topic}"

--- PRO SIDE (arguing IN FAVOR) ---
{pro_history}

--- CON SIDE (arguing AGAINST) ---
{con_history}

Evaluate the debate on these criteria:
1. Strength of arguments
2. Quality of rebuttals
3. Clarity and persuasiveness

Declare a winner (PRO or CON) and explain your reasoning in 2-3 paragraphs.
"""


# ── State ────────────────────────────────────────────────────────────────────

class DebateState(TypedDict):
    topic:       str
    max_rounds:  int
    model:       str
    log_dir:     str
    pro_history: str
    con_history: str
    last_arg:    str
    round:       int
    verdict:     str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_pro_opening(state: DebateState) -> dict:
    print(f"[{state['round']}] Pro opening ...")
    arg = _invoke(state["model"], PRO_PROMPT.format(topic=state["topic"], previous="opening statement"))
    _write(f"{state['log_dir']}/opening_pro.md", arg)
    return {"pro_history": arg, "last_arg": arg}

def node_con_opening(state: DebateState) -> dict:
    print(f"[{state['round']}] Con opening ...")
    arg = _invoke(state["model"], CON_PROMPT.format(topic=state["topic"], previous="opening statement"))
    _write(f"{state['log_dir']}/opening_con.md", arg)
    # We update con_history but also keep last_arg for Pro's next move
    return {"con_history": arg, "last_arg": arg}

def node_pro_rebuttal(state: DebateState) -> dict:
    r = state["round"]
    print(f"[{r}] Pro rebuttal ...")
    # Pro rebuts Con's latest point (which is in state['last_arg'] from Con's turn)
    arg = _invoke(state["model"], PRO_PROMPT.format(topic=state["topic"], previous=state["last_arg"]))
    _write(f"{state['log_dir']}/round_{r}_pro.md", arg)
    return {
        "pro_history": state["pro_history"] + "\n---\n" + arg,
        "last_arg": arg
    }

def node_con_rebuttal(state: DebateState) -> dict:
    r = state["round"]
    print(f"[{r}] Con rebuttal ...")
    # Con rebuts Pro's latest point (which is in state['last_arg'] from Pro's turn)
    arg = _invoke(state["model"], CON_PROMPT.format(topic=state["topic"], previous=state["last_arg"]))
    _write(f"{state['log_dir']}/round_{r}_con.md", arg)
    return {
        "con_history": state["con_history"] + "\n---\n" + arg,
        "last_arg": arg,
        "round": r + 1
    }

def node_judge(state: DebateState) -> dict:
    print("Judge deliberating ...")
    verdict = _invoke(state["model"], JUDGE_PROMPT.format(
        topic=state["topic"],
        pro_history=state["pro_history"],
        con_history=state["con_history"]
    ))
    _write(f"{state['log_dir']}/verdict.md", verdict)
    return {"verdict": verdict}


# ── Routing ──────────────────────────────────────────────────────────────────

def _route(state: DebateState) -> str:
    if state["round"] >= state["max_rounds"]:
        return "judge"
    return "pro_rebuttal"


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(DebateState)
    g.add_node("pro_opening",  node_pro_opening)
    g.add_node("con_opening",  node_con_opening)
    g.add_node("pro_rebuttal", node_pro_rebuttal)
    g.add_node("con_rebuttal", node_con_rebuttal)
    g.add_node("judge",        node_judge)

    g.set_entry_point("pro_opening")
    g.add_edge("pro_opening", "con_opening")
    g.add_conditional_edges("con_opening", _route, {"pro_rebuttal": "pro_rebuttal", "judge": "judge"})
    g.add_edge("pro_rebuttal", "con_rebuttal")
    g.add_conditional_edges("con_rebuttal", _route, {"pro_rebuttal": "pro_rebuttal", "judge": "judge"})
    g.add_edge("judge", END)
    
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic",      required=True,    help="Debate topic")
@click.option("--max-rounds", default=3,        show_default=True, type=int)
@click.option("--model",      default="gemma3", show_default=True)
@click.option("--log-dir",    default="cookbook/11_debate_arena/langgraph/logs-langgraph", show_default=True)
def main(topic: str, max_rounds: int, model: str, log_dir: str):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "topic":       topic,
        "max_rounds":  max_rounds,
        "model":       model,
        "log_dir":     log_dir,
        "pro_history": "",
        "con_history": "",
        "last_arg":    "",
        "round":       0,
        "verdict":     "",
    })

    print("\n" + "=" * 60)
    print("VERDICT:")
    print(result["verdict"])

if __name__ == "__main__":
    main()
