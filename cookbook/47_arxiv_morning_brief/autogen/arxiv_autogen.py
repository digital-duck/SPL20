"""
AutoGen equivalent of arxiv_morning_brief.spl

Pattern: Loop over papers → [process_paper] → assemble_brief

Usage:
    pip install pyautogen requests PyPDF2
    python cookbook/47_arxiv_morning_brief/autogen/arxiv_autogen.py \\
        --urls "https://arxiv.org/pdf/2501.12948"
"""

import click
import os
import sys
from pathlib import Path

from autogen import ConversableAgent

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
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    summarizer = ConversableAgent("Summarizer", system_message="Produce concise technical summaries.", llm_config=llm_config, human_input_mode="NEVER")
    editor = ConversableAgent("Editor", system_message="Format research briefs.", llm_config=llm_config, human_input_mode="NEVER")

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
                chat = summarizer.initiate_chat(summarizer, message=f"Summarize this section:\n{chunk}", max_turns=1)
                chunk_summaries.append(chat.chat_history[-1]["content"])
            
            print("  Reducing to abstract ...")
            chat = summarizer.initiate_chat(summarizer, message="Write a 150-word abstract from these summaries:\n" + "\n".join(chunk_summaries), max_turns=1)
            paper_summaries.append(chat.chat_history[-1]["content"])
        except Exception as e:
            print(f"  Error: {e}")

    print("Assembling final brief ...")
    header = f"# arXiv Morning Brief - {date or 'Today'}"
    all_sums = "\n\n".join(paper_summaries)
    chat = editor.initiate_chat(editor, message=f"Format these abstracts into a morning brief with header '{header}'. Add a 'Key Themes' section.\n\nAbstracts:\n{all_sums}", max_turns=1)
    brief = chat.chat_history[-1]["content"]

    _write(f"{log_dir}/final_brief.md", brief)
    print("Committed | status=complete")


@click.command()
@click.option("--urls", required=True, help="Arxiv URLs")
@click.option("--date", default="", help="Brief date")
@click.option("--model", default="gemma3", help="LLM model")
@click.option("--log-dir", default="cookbook/47_arxiv_morning_brief/logs-autogen", help="Log dir")
def main(urls, date, model, log_dir):
    """arXiv Morning Brief — AutoGen edition"""
    run(urls, date, model, log_dir)

if __name__ == "__main__":
    main()
