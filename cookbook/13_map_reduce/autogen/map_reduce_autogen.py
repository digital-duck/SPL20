"""
AutoGen equivalent of map_reduce.spl

Pattern: chunk_plan → [Summarizer] → Aggregator → (Critic > 0.7? commit : Improver)

Usage:
    pip install pyautogen
    python cookbook/13_map_reduce/autogen/map_reduce_autogen.py \\
        --document "$(cat cookbook/13_map_reduce/large_doc.txt)" \\
        --style "bullet points"
"""

import click
from pathlib import Path
from typing import List

from autogen import ConversableAgent


# ── System Messages ──────────────────────────────────────────────────────────

SUMMARIZER_SYSTEM = """\
You are a precise summarizer. 
Given a chunk of text, produce a concise summary of its key points.
Output only the summary content."""

AGGREGATOR_SYSTEM = """\
You are an expert editor.
Given multiple summaries of different parts of a document, 
combine them into a single cohesive final summary in the requested style.
Output only the final summary."""

CRITIC_SYSTEM = """\
You are a quality control agent.
Rate the provided summary (0.0 to 1.0) based on how well it captures the original context.
Reply with ONLY the numerical score."""

IMPROVER_SYSTEM = """\
You are an expert writer.
Refine the provided summary to better reflect the source material.
Output only the improved version."""


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

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(document: str, style: str, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    summarizer = ConversableAgent("Summarizer", system_message=SUMMARIZER_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")
    aggregator = ConversableAgent("Aggregator", system_message=AGGREGATOR_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")
    critic     = ConversableAgent("Critic",     system_message=CRITIC_SYSTEM,     llm_config=llm_config, human_input_mode="NEVER")
    improver   = ConversableAgent("Improver",   system_message=IMPROVER_SYSTEM,   llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Plan
    chunk_count = _chunk_plan(document)
    print(f"Plan: {chunk_count} chunks")

    # Step 2: Map
    summaries = []
    for i in range(chunk_count):
        print(f"Map: Chunk {i}/{chunk_count}")
        chunk = _extract_chunk(document, i, chunk_count)
        _write(f"{log_dir}/chunk_{i}.md", chunk)
        
        # In AutoGen, we initiate a brief chat to get the result
        chat = summarizer.initiate_chat(summarizer, message=chunk, max_turns=1)
        summary = chat.chat_history[-1]["content"]
        summaries.append(summary)
        _write(f"{log_dir}/summary_{i}.md", summary)

    # Step 3: Reduce
    print("Reduce: Aggregating...")
    summaries_text = "\n\n".join(summaries)
    chat = aggregator.initiate_chat(aggregator, message=f"Style: {style}\n\nSummaries:\n{summaries_text}", max_turns=1)
    final_summary = chat.chat_history[-1]["content"]

    # Step 4: Quality Check
    print("Quality Check: Scoring...")
    doc_subset = document[:4000]
    chat = critic.initiate_chat(critic, message=f"Summary:\n{final_summary}\n\nOriginal:\n{doc_subset}", max_turns=1)
    try:
        score = float(chat.chat_history[-1]["content"].strip())
    except:
        score = 0.5
    print(f"Score: {score}")

    if score <= 0.7:
        print("Refine: Improving...")
        chat = improver.initiate_chat(improver, message=f"Summary:\n{final_summary}\n\nSource:\n{summaries_text}", max_turns=1)
        final_summary = chat.chat_history[-1]["content"]

    _write(f"{log_dir}/final_summary.md", final_summary)
    print(f"Done. Saved to {log_dir}/final_summary.md")


@click.command()
@click.option("--document", required=True, help="Document text to summarize")
@click.option("--style", default="bullet points", help="Output style")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/13_map_reduce/logs-autogen", help="Log directory")
def main(document, style, model, log_dir):
    """Map-Reduce Summarizer — AutoGen edition"""
    run(document, style, model, log_dir)

if __name__ == "__main__":
    main()
