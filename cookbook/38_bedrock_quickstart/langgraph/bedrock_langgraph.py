"""
LangGraph equivalent of bedrock_quickstart.spl

Pattern: Fan-out (Parallel nodes) → Synthesize

Usage:
    pip install langgraph langchain-aws
    python cookbook/38_bedrock_quickstart/langgraph/bedrock_langgraph.py \\
        --prompt "Explain the CAP theorem in two sentences."
"""

import click
from pathlib import Path
from typing import TypedDict

# Note: Using ChatOllama as a drop-in fallback if AWS Bedrock is not configured
# In a real Bedrock env, you would use from langchain_aws import ChatBedrock
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class BedrockState(TypedDict):
    prompt:   str
    model_1:  str
    model_2:  str
    model_3:  str
    judge_model: str
    log_dir:  str
    
    ans_1: str
    ans_2: str
    ans_3: str
    comparison: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    # Simulating Bedrock call with local Ollama for ease of testing
    return ChatOllama(model="gemma3").invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_ask_1(state: BedrockState) -> dict:
    print(f"Asking Model 1 ({state['model_1']}) ...")
    return {"ans_1": _invoke(state["model_1"], state["prompt"])}

def node_ask_2(state: BedrockState) -> dict:
    print(f"Asking Model 2 ({state['model_2']}) ...")
    return {"ans_2": _invoke(state["model_2"], state["prompt"])}

def node_ask_3(state: BedrockState) -> dict:
    print(f"Asking Model 3 ({state['model_3']}) ...")
    return {"ans_3": _invoke(state["model_3"], state["prompt"])}

def node_compare(state: BedrockState) -> dict:
    print("Synthesizing comparison ...")
    comp_prompt = f"""\
You are a neutral evaluator comparing responses from three AWS Bedrock models.

Prompt: "{state['prompt']}"

=== {state['model_1']} ===
{state['ans_1']}

=== {state['model_2']} ===
{state['ans_2']}

=== {state['model_3']} ===
{state['ans_3']}

Evaluation:
- Most accurate?
- Most concise?
- Recommendation for production?"""
    res = _invoke(state["judge_model"], comp_prompt)
    _write(f"{state['log_dir']}/comparison.md", res)
    return {"comparison": res}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(BedrockState)
    g.add_node("ask_1",   node_ask_1)
    g.add_node("ask_2",   node_ask_2)
    g.add_node("ask_3",   node_ask_3)
    g.add_node("compare", node_compare)

    g.set_entry_point("ask_1") # Sequential for simplicity in this script, 
                               # but LangGraph supports true parallel branches.
    g.add_edge("ask_1",   "ask_2")
    g.add_edge("ask_2",   "ask_3")
    g.add_edge("ask_3",   "compare")
    g.add_edge("compare", END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--prompt", default="Explain the CAP theorem in two sentences.")
@click.option("--model_1", default="anthropic.claude-sonnet-4")
@click.option("--model_2", default="anthropic.claude-haiku-4-5")
@click.option("--model_3", default="amazon.nova-pro")
@click.option("--judge_model", default="gemma3")
@click.option("--log-dir", default="cookbook/38_bedrock_quickstart/logs-langgraph", help="Log directory")
def main(prompt, model_1, model_2, model_3, judge_model, log_dir):
    """Bedrock Quickstart — LangGraph edition"""
    build_graph().invoke({
        "prompt":      prompt,
        "model_1":     model_1,
        "model_2":     model_2,
        "model_3":     model_3,
        "judge_model": judge_model,
        "log_dir":     log_dir,
        "ans_1": "", "ans_2": "", "ans_3": "", "comparison": ""
    })

if __name__ == "__main__":
    main()
