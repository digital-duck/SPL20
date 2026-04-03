"""
CrewAI equivalent of map_reduce.spl

Pattern: chunk_plan → [Summarizer Agent] → Aggregator Agent → (Critic Agent > 0.7? commit : Improver Agent)

Usage:
    pip install crewai langchain-ollama
    python cookbook/13_map_reduce/crewai/map_reduce_crewai.py \\
        --document "$(cat cookbook/13_map_reduce/large_doc.txt)" \\
        --style "bullet points"
"""

import click
from pathlib import Path
from typing import List

from crewai import Agent, Crew, Process, Task
from langchain_ollama import ChatOllama


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

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()


# ── Main runner ───────────────────────────────────────────────────────────────

def run(document: str, style: str, model: str, log_dir: str):
    # For CrewAI, using the 'ollama/' prefix with the model name is the most 
    # robust way to handle local models and avoid Pydantic validation issues.
    llm = f"ollama/{model}"

    summarizer = Agent(
        role="Summarizer",
        goal="Produce concise summaries of document chunks.",
        backstory="You are a precise summarizer who captures essential info accurately.",
        llm=llm,
        verbose=False,
    )
    aggregator = Agent(
        role="Editor",
        goal="Combine multiple summaries into a single cohesive final summary.",
        backstory="You are an expert editor who can synthesize diverse points into a smooth narrative.",
        llm=llm,
        verbose=False,
    )
    critic = Agent(
        role="Quality Control",
        goal="Rate summary quality (0.0 to 1.0).",
        backstory="You are a strict judge. Reply with ONLY a numerical score between 0.0 and 1.0.",
        llm=llm,
        verbose=False,
    )
    improver = Agent(
        role="Professional Writer",
        goal="Refine summaries based on source material.",
        backstory="You excel at polishing content to make it more comprehensive and clear.",
        llm=llm,
        verbose=False,
    )

    # Step 1: Plan
    chunk_count = _chunk_plan(document)
    print(f"Plan: {chunk_count} chunks")

    # Step 2: Map
    summaries = []
    for i in range(chunk_count):
        print(f"Map: Chunk {i}/{chunk_count}")
        chunk = _extract_chunk(document, i, chunk_count)
        _write(f"{log_dir}/chunk_{i}.md", chunk)
        
        summary = _run_task(
            summarizer,
            description=f"Summarize this chunk of text:\n\n{chunk}",
            expected_output="A concise summary of the key points.",
        )
        summaries.append(summary)
        _write(f"{log_dir}/summary_{i}.md", summary)

    # Step 3: Reduce
    print("Reduce: Aggregating...")
    summaries_text = "\n\n".join(summaries)
    final_summary = _run_task(
        aggregator,
        description=f"Combine these summaries into a final version in style '{style}':\n\n{summaries_text}",
        expected_output=f"A cohesive final summary in {style} style.",
    )

    # Step 4: Quality Check
    print("Quality Check: Scoring...")
    doc_subset = document[:4000]
    score_str = _run_task(
        critic,
        description=f"Rate this summary (0.0-1.0) against the original:\nSummary:\n{final_summary}\n\nOriginal:\n{doc_subset}",
        expected_output="A single numerical score between 0.0 and 1.0.",
    )
    try:
        score = float(score_str)
    except:
        score = 0.5
    print(f"Score: {score}")

    if score <= 0.7:
        print("Refine: Improving...")
        final_summary = _run_task(
            improver,
            description=f"Improve this summary to better reflect the source summaries:\nSummary:\n{final_summary}\n\nSource:\n{summaries_text}",
            expected_output="A refined and improved final summary.",
        )

    _write(f"{log_dir}/final_summary.md", final_summary)
    print(f"Done. Saved to {log_dir}/final_summary.md")


@click.command()
@click.option("--document", required=True, help="Document text to summarize")
@click.option("--style", default="bullet points", help="Output style")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/13_map_reduce/logs-crewai", help="Log directory")
def main(document, style, model, log_dir):
    """Map-Reduce Summarizer — CrewAI edition"""
    run(document, style, model, log_dir)

if __name__ == "__main__":
    main()
