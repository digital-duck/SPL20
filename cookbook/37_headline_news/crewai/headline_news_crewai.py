"""
CrewAI equivalent of headline_news.spl

Pattern: headlines → expand → evaluate → (pass? format : fill_gaps → format)

Usage:
    pip install crewai langchain-ollama
    python cookbook/37_headline_news/crewai/headline_news_crewai.py \\
        --topic "artificial intelligence"
"""

import click
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, date: str, max_headlines: int, style: str, perspective: str, model: str, log_dir: str):
    llm = f"ollama/{model}"

    editor = Agent(
        role="News Editor",
        goal="Curate and evaluate a news digest.",
        backstory="You are a senior editor with an eye for coverage and balance.",
        llm=llm,
        verbose=False,
    )
    analyst = Agent(
        role="News Analyst",
        goal="Provide factual expansions of headlines.",
        backstory="You are a meticulous researcher who adds context to news.",
        llm=llm,
        verbose=False,
    )

    # Step 1: Headlines
    print("Step 1: Generating headlines ...")
    task_headlines = Task(
        description=f"Generate the top {max_headlines} headlines about '{topic}' as of {date}. Perspective: {perspective}.",
        expected_output="A numbered list of headlines.",
        agent=editor,
    )
    headlines = str(Crew(agents=[editor], tasks=[task_headlines], verbose=False).kickoff())
    _write(f"{log_dir}/01_headlines.md", headlines)

    # Step 2: Expand
    print("Step 2: Expanding headlines ...")
    task_expand = Task(
        description=f"Expand these headlines with 2-3 sentence summaries for {topic}:\n\n{headlines}",
        expected_output="Expanded headlines with summaries.",
        agent=analyst,
    )
    expanded = str(Crew(agents=[analyst], tasks=[task_expand], verbose=False).kickoff())
    _write(f"{log_dir}/02_expanded.md", expanded)

    # Step 3: Evaluate & Step 4: Fill Gaps (Manual loop in Python for CrewAI)
    print("Step 3: Evaluating coverage ...")
    task_eval = Task(
        description=f"Rate the coverage completeness (0.0-1.0) of these news summaries for '{topic}'. Reply with ONLY the number.\n\n{expanded}",
        expected_output="A single numerical score.",
        agent=editor,
    )
    score_str = str(Crew(agents=[editor], tasks=[task_eval], verbose=False).kickoff())
    try:
        score = float(score_str.strip())
    except:
        score = 0.5
    print(f"Coverage score: {score}")

    if score <= 0.75:
        print("Step 4: Filling coverage gaps ...")
        task_fill = Task(
            description=f"The current digest for '{topic}' has gaps (score: {score}). Add missing angles and return the FULL updated list.\n\n{expanded}",
            expected_output="A complete list of headlines and summaries.",
            agent=editor,
        )
        expanded = str(Crew(agents=[editor], tasks=[task_fill], verbose=False).kickoff())
        _write(f"{log_dir}/04_expanded_refined.md", expanded)

    # Step 5: Format
    print("Step 5: Formatting digest ...")
    task_format = Task(
        description=f"Format this news content into a '{style}' digest for {topic} on {date}:\n\n{expanded}",
        expected_output="A formatted news digest.",
        agent=editor,
    )
    digest = str(Crew(agents=[editor], tasks=[task_format], verbose=False).kickoff())
    _write(f"{log_dir}/final_digest.md", digest)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic for the news digest")
@click.option("--date", default="today", help="Date for the news")
@click.option("--max-headlines", default=7, help="Max headlines to generate")
@click.option("--style", default="structured", help="Output style")
@click.option("--perspective", default="balanced", help="Coverage perspective")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/37_headline_news/logs-crewai", help="Log directory")
def main(topic, date, max_headlines, style, perspective, model, log_dir):
    """Headline News Aggregator — CrewAI edition"""
    run(topic, date, max_headlines, style, perspective, model, log_dir)

if __name__ == "__main__":
    main()
