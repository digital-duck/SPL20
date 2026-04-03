"""
LangGraph equivalent of headline_news.spl

Pattern: headlines → expand → evaluate → (pass? format : fill_gaps → format)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/37_headline_news/langgraph/headline_news_langgraph.py \\
        --topic "artificial intelligence"
"""

import click
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class NewsState(TypedDict):
    topic:          str
    date:           str
    max_headlines:  int
    style:          str
    perspective:    str
    model:          str
    log_dir:        str
    headlines:      str
    expanded:       str
    coverage_score: float
    digest:         str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_headlines(state: NewsState) -> dict:
    print("Step 1: Generating headlines ...")
    prompt = f"Generate the top {state['max_headlines']} headlines about '{state['topic']}' as of {state['date']}. Perspective: {state['perspective']}. Output a numbered list only."
    res = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/01_headlines.md", res)
    return {"headlines": res}

def node_expand(state: NewsState) -> dict:
    print("Step 2: Expanding headlines ...")
    prompt = f"Expand each of these headlines with a 2-3 sentence factual summary. Topic: {state['topic']}. Perspective: {state['perspective']}.\n\n{state['headlines']}"
    res = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/02_expanded.md", res)
    return {"expanded": res}

def node_evaluate(state: NewsState) -> dict:
    print("Step 3: Evaluating coverage ...")
    prompt = f"Rate the coverage of these news summaries for the topic '{state['topic']}'. Perspective: {state['perspective']}. Reply with ONLY a score between 0.0 and 1.0.\n\n{state['expanded']}"
    score_str = _invoke(state["model"], prompt)
    try:
        score = float(score_str.strip())
    except:
        score = 0.5
    print(f"Coverage score: {score}")
    return {"coverage_score": score}

def node_fill_gaps(state: NewsState) -> dict:
    print("Step 4: Filling coverage gaps ...")
    prompt = f"The current news digest for '{state['topic']}' has gaps. Add 2-3 missing angles with summaries. Return the FULL updated list.\n\n{state['expanded']}"
    res = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/04_expanded_refined.md", res)
    return {"expanded": res}

def node_format(state: NewsState) -> dict:
    print("Step 5: Formatting digest ...")
    prompt = f"Format this news content into a '{state['style']}' digest for {state['topic']} on {state['date']}:\n\n{state['expanded']}"
    res = _invoke(state["model"], prompt)
    _write(f"{state['log_dir']}/final_digest.md", res)
    return {"digest": res}


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_after_eval(state: NewsState) -> str:
    if state["coverage_score"] > 0.75:
        return "format"
    return "fill_gaps"


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(NewsState)
    g.add_node("headlines", node_headlines)
    g.add_node("expand",    node_expand)
    g.add_node("evaluate",  node_evaluate)
    g.add_node("fill_gaps", node_fill_gaps)
    g.add_node("format",    node_format)

    g.set_entry_point("headlines")
    g.add_edge("headlines", "expand")
    g.add_edge("expand",    "evaluate")
    g.add_conditional_edges("evaluate", _route_after_eval, {"format": "format", "fill_gaps": "fill_gaps"})
    g.add_edge("fill_gaps", "format")
    g.add_edge("format",    END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic", required=True, help="Topic for the news digest")
@click.option("--date", default="today", help="Date for the news")
@click.option("--max-headlines", default=7, help="Max headlines to generate")
@click.option("--style", default="structured", help="Output style")
@click.option("--perspective", default="balanced", help="Coverage perspective")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/37_headline_news/logs-langgraph", help="Log directory")
def main(topic, date, max_headlines, style, perspective, model, log_dir):
    """Headline News Aggregator — LangGraph edition"""
    build_graph().invoke({
        "topic":         topic,
        "date":          date,
        "max_headlines": max_headlines,
        "style":         style,
        "perspective":   perspective,
        "model":         model,
        "log_dir":       log_dir,
        "headlines":     "",
        "expanded":      "",
        "coverage_score": 0.0,
        "digest":        "",
    })

if __name__ == "__main__":
    main()
