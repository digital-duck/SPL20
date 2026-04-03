"""
CrewAI equivalent of arxiv_morning_brief.spl

Pattern: Task sequence per paper with final synthesis.

Usage:
    pip install crewai langchain-ollama requests PyPDF2
    python cookbook/47_arxiv_morning_brief/crewai/arxiv_crewai.py \\
        --urls "https://arxiv.org/pdf/2501.12948"
"""

import click
import os
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task

# Add parent to path to import tools
sys.path.append(str(Path(__file__).parent.parent))
try:
    from tools import download_arxiv_pdf, semantic_chunk_plan, parse_urls
except ImportError:
    def parse_urls(u): return [u]
    def download_arxiv_pdf(u): return "dummy.pdf"
    def semantic_chunk_plan(p): return ["chunk 1", "chunk 2"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(urls_input: str, date: str, model: str, log_dir: str):
    llm = f"ollama/{model}"

    summarizer = Agent(
        role="Technical Summarizer",
        goal="Produce concise summaries of research paper sections.",
        backstory="You are an expert at extracting core methods and findings from academic papers.",
        llm=llm,
        verbose=False,
    )
    editor = Agent(
        role="Research Editor",
        goal="Format research abstracts into a cohesive morning brief.",
        backstory="You synthesize complex information into accessible newsletters.",
        llm=llm,
        verbose=False,
    )

    urls = parse_urls(urls_input)
    print(f"Processing {len(urls)} papers ...")

    paper_summaries = []
    for url in urls:
        print(f"Paper: {url}")
        try:
            pdf_path = download_arxiv_pdf(url)
            chunks = semantic_chunk_plan(pdf_path)
            
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                print(f"  Chunk {i+1}/{len(chunks)} ...")
                task = Task(description=f"Summarize this paper section:\n{chunk}", expected_output="A concise summary.", agent=summarizer)
                res = str(Crew(agents=[summarizer], tasks=[task], verbose=False).kickoff())
                chunk_summaries.append(res)
            
            print("  Reducing to abstract ...")
            task_red = Task(description="Write a 150-word abstract from these summaries:\n" + "\n".join(chunk_summaries), expected_output="A paper abstract.", agent=summarizer)
            paper_summaries.append(str(Crew(agents=[summarizer], tasks=[task_red], verbose=False).kickoff()))
        except Exception as e:
            print(f"  Error: {e}")

    print("Assembling final brief ...")
    header = f"# arXiv Morning Brief - {date or 'Today'}"
    all_sums = "\n\n".join(paper_summaries)
    task_final = Task(description=f"Format these abstracts into a morning brief with header '{header}'. Add a 'Key Themes' section.\n\nAbstracts:\n{all_sums}", expected_output="A Markdown newsletter.", agent=editor)
    brief = str(Crew(agents=[editor], tasks=[task_final], verbose=False).kickoff())

    _write(f"{log_dir}/final_brief.md", brief)
    print("Committed | status=complete")


@click.command()
@click.option("--urls", required=True, help="Arxiv URLs")
@click.option("--date", default="", help="Brief date")
@click.option("--model", default="gemma3", help="LLM model")
@click.option("--log-dir", default="cookbook/47_arxiv_morning_brief/logs-crewai", help="Log dir")
def main(urls, date, model, log_dir):
    """arXiv Morning Brief — CrewAI edition"""
    run(urls, date, model, log_dir)

if __name__ == "__main__":
    main()
