"""
LangGraph equivalent of map_reduce.spl

Pattern: chunk_plan → [summarize_chunk] → reduce_summaries → (quality_score > 0.7? commit : improve_summary)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/13_map_reduce/langgraph/map_reduce_langgraph.py \\
        --document "$(cat cookbook/13_map_reduce/large_doc.txt)" \\
        --style "bullet points"
"""

import click
import os
from pathlib import Path
from typing import List, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts ───────────────────────────────────────────────────────────────────

SUMMARIZE_CHUNK_PROMPT = """\
Summarize the following chunk of a larger document. 
Focus on capturing the key points and essential information.

Chunk (index {chunk_index}):
{chunk}
"""

REDUCE_SUMMARIES_PROMPT = """\
Below are several summaries of different parts of a document. 
Combine them into a single, cohesive final summary.
The final summary should be in the following style: {style}

Summaries:
{summaries}
"""

QUALITY_SCORE_PROMPT = """\
Rate the quality of the following summary based on how well it captures the main points of the original document.
Provide a score between 0.0 and 1.0, where 1.0 is perfect.
Reply with ONLY the numerical score.

Summary:
{summary}

Original document (subset):
{document}
"""

IMPROVE_SUMMARY_PROMPT = """\
The following summary needs improvement. 
Please refine it to better capture the key points from the provided chunk summaries.

Current Summary:
{summary}

Source Summaries:
{summaries}
"""


# ── State ─────────────────────────────────────────────────────────────────────

class MapReduceState(TypedDict):
    document:      str
    style:         str
    model:         str
    log_dir:       str
    chunk_count:   int
    chunk_index:   int
    summaries:     List[str]
    final_summary: str
    score:         float


# ── Deterministic Tools (from tools.py) ───────────────────────────────────────

def _chunk_plan(document: str) -> int:
    words = document.split()
    if not words: return 1
    target = 800
    return max(1, (len(words) + target - 1) // target)

def _extract_chunk(document: str, idx: int, total: int) -> str:
    words = document.split()
    n = len(words)
    chunk_size = (n + total - 1) // total
    start = idx * chunk_size
    end = min(start + chunk_size, n)
    return " ".join(words[start:end])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_plan(state: MapReduceState) -> dict:
    count = _chunk_plan(state["document"])
    print(f"Plan: splitting document into {count} chunks")
    return {"chunk_count": count, "chunk_index": 0, "summaries": []}

def node_summarize(state: MapReduceState) -> dict:
    idx = state["chunk_index"]
    print(f"Map: summarizing chunk {idx}/{state['chunk_count']}")
    
    chunk = _extract_chunk(state["document"], idx, state["chunk_count"])
    _write(f"{state['log_dir']}/chunk_{idx}.md", chunk)
    
    prompt = SUMMARIZE_CHUNK_PROMPT.format(chunk_index=idx, chunk=chunk)
    summary = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/summary_{idx}.md", summary)
    
    return {
        "summaries": state["summaries"] + [summary],
        "chunk_index": idx + 1
    }

def node_reduce(state: MapReduceState) -> dict:
    print("Reduce: combining summaries")
    summaries_text = "\n\n".join(state["summaries"])
    prompt = REDUCE_SUMMARIES_PROMPT.format(style=state["style"], summaries=summaries_text)
    final = _invoke(state["model"], prompt)
    return {"final_summary": final}

def node_quality_check(state: MapReduceState) -> dict:
    print("Quality Check: scoring final summary")
    # Using a subset of doc to avoid context overflow in scoring
    doc_subset = state["document"][:4000] 
    prompt = QUALITY_SCORE_PROMPT.format(summary=state["final_summary"], document=doc_subset)
    score_str = _invoke(state["model"], prompt)
    try:
        score = float(score_str)
    except ValueError:
        score = 0.5 # fallback
    print(f"Score: {score}")
    return {"score": score}

def node_improve(state: MapReduceState) -> dict:
    print("Refine: improving summary")
    summaries_text = "\n\n".join(state["summaries"])
    prompt = IMPROVE_SUMMARY_PROMPT.format(summary=state["final_summary"], summaries=summaries_text)
    final = _invoke(state["model"], prompt)
    return {"final_summary": final}

def node_commit(state: MapReduceState) -> dict:
    print(f"Commit: saving final summary to {state['log_dir']}/final_summary.md")
    _write(f"{state['log_dir']}/final_summary.md", state["final_summary"])
    return {}


# ── Conditional Edges ─────────────────────────────────────────────────────────

def _route_map(state: MapReduceState) -> str:
    if state["chunk_index"] < state["chunk_count"]:
        return "summarize"
    return "reduce"

def _route_quality(state: MapReduceState) -> str:
    if state["score"] > 0.7:
        return "commit"
    return "improve"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(MapReduceState)
    g.add_node("plan",      node_plan)
    g.add_node("summarize", node_summarize)
    g.add_node("reduce",    node_reduce)
    g.add_node("quality",   node_quality_check)
    g.add_node("improve",   node_improve)
    g.add_node("commit",    node_commit)

    g.set_entry_point("plan")
    g.add_conditional_edges("plan", _route_map, {"summarize": "summarize", "reduce": "reduce"})
    g.add_conditional_edges("summarize", _route_map, {"summarize": "summarize", "reduce": "reduce"})
    g.add_edge("reduce",    "quality")
    g.add_conditional_edges("quality", _route_quality, {"commit": "commit", "improve": "improve"})
    g.add_edge("improve",   "commit")
    g.add_edge("commit",    END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--document", required=True, help="Document text to summarize")
@click.option("--style", default="bullet points", help="Output style")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/13_map_reduce/logs-langgraph", help="Log directory")
def main(document, style, model, log_dir):
    """Map-Reduce Summarizer — LangGraph edition"""
    build_graph().invoke({
        "document":    document,
        "style":       style,
        "model":       model,
        "log_dir":     log_dir,
        "chunk_count": 0,
        "chunk_index": 0,
        "summaries":   [],
        "final_summary": "",
        "score":       0.0,
    })

if __name__ == "__main__":
    main()
