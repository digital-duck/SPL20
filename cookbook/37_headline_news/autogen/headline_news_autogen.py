"""
AutoGen equivalent of headline_news.spl

Pattern: headlines → expand → evaluate → (pass? format : fill_gaps → format)

Usage:
    pip install pyautogen
    python cookbook/37_headline_news/autogen/headline_news_autogen.py \\
        --topic "artificial intelligence"
"""

import click
from pathlib import Path

from autogen import ConversableAgent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, date: str, max_headlines: int, style: str, perspective: str, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    editor = ConversableAgent("Editor", system_message="You are a news editor.", llm_config=llm_config, human_input_mode="NEVER")
    analyst = ConversableAgent("Analyst", system_message="You are a news analyst.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Headlines
    print("Step 1: Generating headlines ...")
    chat = editor.initiate_chat(editor, message=f"Generate the top {max_headlines} headlines about '{topic}' as of {date}. Perspective: {perspective}. Output a numbered list only.", max_turns=1)
    headlines = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/01_headlines.md", headlines)

    # Step 2: Expand
    print("Step 2: Expanding headlines ...")
    chat = analyst.initiate_chat(analyst, message=f"Expand these headlines with 2-3 sentence summaries for {topic} (perspective: {perspective}):\n\n{headlines}", max_turns=1)
    expanded = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/02_expanded.md", expanded)

    # Step 3: Evaluate
    print("Step 3: Evaluating coverage ...")
    chat = editor.initiate_chat(editor, message=f"Rate the coverage completeness (0.0-1.0) of these summaries for '{topic}'. Reply with ONLY the number.\n\n{expanded}", max_turns=1)
    try:
        score = float(chat.chat_history[-1]["content"].strip())
    except:
        score = 0.5
    print(f"Coverage score: {score}")

    # Step 4: Fill gaps if needed
    if score <= 0.75:
        print("Step 4: Filling coverage gaps ...")
        chat = editor.initiate_chat(editor, message=f"The digest for '{topic}' has gaps (score: {score}). Add missing angles. Return FULL list.\n\n{expanded}", max_turns=1)
        expanded = chat.chat_history[-1]["content"]
        _write(f"{log_dir}/04_expanded_refined.md", expanded)

    # Step 5: Format
    print("Step 5: Formatting digest ...")
    chat = editor.initiate_chat(editor, message=f"Format this into a '{style}' news digest for {topic} on {date}:\n\n{expanded}", max_turns=1)
    digest = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/final_digest.md", digest)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic for the news digest")
@click.option("--date", default="today", help="Date for the news")
@click.option("--max-headlines", default=7, help="Max headlines to generate")
@click.option("--style", default="structured", help="Output style")
@click.option("--perspective", default="balanced", help="Coverage perspective")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/37_headline_news/logs-autogen", help="Log directory")
def main(topic, date, max_headlines, style, perspective, model, log_dir):
    """Headline News Aggregator — AutoGen edition"""
    run(topic, date, max_headlines, style, perspective, model, log_dir)

if __name__ == "__main__":
    main()
