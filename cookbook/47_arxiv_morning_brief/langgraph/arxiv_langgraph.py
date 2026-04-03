"""
LangGraph equivalent of arxiv_morning_brief.spl

Pattern: urls → [process_paper] → assemble_brief

Usage:
    pip install langgraph langchain-ollama requests PyPDF2
    python cookbook/47_arxiv_morning_brief/langgraph/arxiv_langgraph.py \\
        --urls "https://arxiv.org/pdf/2501.12948"
"""

import click
import os
import sys
from pathlib import Path
from typing import List, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

# Add parent to path to import tools
sys.path.append(str(Path(__file__).parent.parent))
try:
    from tools import download_arxiv_pdf, semantic_chunk_plan, parse_urls
except ImportError:
    # Fallback if tools.py not easily importable
    def parse_urls(u): return [u]
    def download_arxiv_pdf(u): return "dummy.pdf"
    def semantic_chunk_plan(p): return ["chunk 1", "chunk 2"]


# ── State ─────────────────────────────────────────────────────────────────────

class ArxivState(TypedDict):
    urls:            List[str]
    date:            str
    model:           str
    log_dir:         str
    paper_summaries: List[str]
    current_brief:   str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_init(state: ArxivState) -> dict:
    # Simulating parse_urls from SPL
    raw_urls = state["urls"]
    if isinstance(raw_urls, str):
        urls = parse_urls(raw_urls)
    else:
        urls = raw_urls
    print(f"Init: {len(urls)} papers to process.")
    return {"urls": urls, "paper_summaries": []}

def node_process_papers(state: ArxivState) -> dict:
    summaries = []
    for url in state["urls"]:
        print(f"Processing paper: {url} ...")
        try:
            pdf_path = download_arxiv_pdf(url)
            chunks = semantic_chunk_plan(pdf_path)
            
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                print(f"  Summarizing chunk {i+1}/{len(chunks)} ...")
                s = _invoke(state["model"], f"Summarize this paper section:\n{chunk}")
                chunk_summaries.append(s)
            
            print("  Reducing chunk summaries to abstract ...")
            paper_summary = _invoke(state["model"], f"Write a 150-word abstract from these section summaries:\n" + "\n".join(chunk_summaries))
            summaries.append(paper_summary)
        except Exception as e:
            print(f"  Error processing {url}: {e}")
    
    return {"paper_summaries": summaries}

def node_assemble(state: ArxivState) -> dict:
    print("Assembling final brief ...")
    header = f"# arXiv Morning Brief - {state['date'] or 'Today'}"
    all_sums = "\n\n".join(state["paper_summaries"])
    prompt = f"Format these paper abstracts into a Markdown morning brief with a header '{header}'. Add a 'Key Themes' section at the end.\n\nAbstracts:\n{all_sums}"
    brief = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/final_brief.md", brief)
    return {"current_brief": brief}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(ArxivState)
    g.add_node("init",    node_init)
    g.add_node("process", node_process_papers)
    g.add_node("assemble", node_assemble)

    g.set_entry_point("init")
    g.add_edge("init",    "process")
    g.add_edge("process", "assemble")
    g.add_edge("assemble", END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--urls", required=True, help="Arxiv URLs (comma-separated or file)")
@click.option("--date", default="", help="Date for the brief")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/47_arxiv_morning_brief/logs-langgraph", help="Log directory")
def main(urls, date, model, log_dir):
    """arXiv Morning Brief — LangGraph edition"""
    build_graph().invoke({
        "urls":            urls.split(",") if "," in urls else [urls],
        "date":            date,
        "model":           model,
        "log_dir":         log_dir,
        "paper_summaries": [],
        "current_brief":   "",
    })

if __name__ == "__main__":
    main()
