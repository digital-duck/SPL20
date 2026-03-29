"""
LangGraph equivalent of chain.spl

Pattern: research → analyze → summarize (3-step sequential GENERATE pipeline)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/09_chain_of_thought/langgraph/chain_langgraph.py \\
        --topic "distributed AI inference"
    python cookbook/09_chain_of_thought/langgraph/chain_langgraph.py \\
        --topic "quantum computing" --model llama3.2
"""

import argparse
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors PROMPT blocks in chain.spl) ──────────────────────────────

RESEARCH_PROMPT = """\
You are a research expert. Research the following topic thoroughly.

Topic: {topic}

Provide key facts, current state, and important context."""

ANALYZE_PROMPT = """\
You are an analytical expert. Analyze the following research findings.

Research:
{research}

Identify patterns, implications, and key insights."""

SUMMARIZE_PROMPT = """\
You are an expert summarizer. Synthesize the following analysis into a clear summary.

Analysis:
{analysis}

Write a concise 2-3 paragraph executive summary."""


# ── State  (SPL manages @variables implicitly) ────────────────────────────────

class ChainState(TypedDict):
    topic:    str
    model:    str
    log_dir:  str
    research: str   # @research
    analysis: str   # @analysis
    summary:  str   # @summary


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes  (each mirrors one GENERATE block) ─────────────────────────────────

def node_research(state: ChainState) -> dict:
    # GENERATE research(@topic) INTO @research
    print("Step 1 | researching ...")
    research = _invoke(state["model"], RESEARCH_PROMPT.format(topic=state["topic"]))
    _write(f"{state['log_dir']}/research.md", research)
    return {"research": research}

def node_analyze(state: ChainState) -> dict:
    # GENERATE analyze(@research) INTO @analysis
    print("Step 2 | analyzing ...")
    analysis = _invoke(state["model"], ANALYZE_PROMPT.format(research=state["research"]))
    _write(f"{state['log_dir']}/analysis.md", analysis)
    return {"analysis": analysis}

def node_summarize(state: ChainState) -> dict:
    # GENERATE summarize(@analysis) INTO @summary
    print("Step 3 | summarizing ...")
    summary = _invoke(state["model"], SUMMARIZE_PROMPT.format(analysis=state["analysis"]))
    _write(f"{state['log_dir']}/summary.md", summary)
    return {"summary": summary}

def node_commit(state: ChainState) -> dict:
    # COMMIT @summary WITH status = 'complete'
    _write(f"{state['log_dir']}/final.md", state["summary"])
    print("Committed | status=complete")
    return {}


# ── Graph  (SPL: implicit sequential WORKFLOW layout) ─────────────────────────

def build_graph():
    g = StateGraph(ChainState)
    g.add_node("research",  node_research)
    g.add_node("analyze",   node_analyze)
    g.add_node("summarize", node_summarize)
    g.add_node("commit",    node_commit)

    g.set_entry_point("research")
    g.add_edge("research",  "analyze")
    g.add_edge("analyze",   "summarize")
    g.add_edge("summarize", "commit")
    g.add_edge("commit",    END)
    return g.compile()


# ── Entry point  (SPL: built into CLI — `spl run ...`) ────────────────────────

def main():
    p = argparse.ArgumentParser(description="Chain of Thought — LangGraph edition")
    p.add_argument("--topic",   required=True)
    p.add_argument("--model",   default="gemma3")
    p.add_argument("--log-dir", default="cookbook/09_chain_of_thought/langgraph/logs")
    args = p.parse_args()

    result = build_graph().invoke({
        "topic":    args.topic,
        "model":    args.model,
        "log_dir":  args.log_dir,
        "research": "",
        "analysis": "",
        "summary":  "",
    })
    print("\n" + "=" * 60)
    print(result["summary"])

if __name__ == "__main__":
    main()
