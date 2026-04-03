"""
CrewAI equivalent of multi_model.spl

Pattern: research → analyze → write → score → (pass? commit : refine → loop)

Usage:
    pip install crewai langchain-ollama
    python cookbook/21_multi_model_pipeline/crewai/multi_model_crewai.py \\
        --topic "climate change"
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

def run(topic: str, max_iterations: int, model: str, log_dir: str):
    llm = f"ollama/{model}"

    researcher = Agent(
        role="Researcher",
        goal="Gather key facts about a topic.",
        backstory="You are a meticulous researcher who finds accurate information.",
        llm=llm,
        verbose=False,
    )
    analyst = Agent(
        role="Analyst",
        goal="Identify significant insights from research data.",
        backstory="You are a strategic thinker who connects the dots.",
        llm=llm,
        verbose=False,
    )
    writer = Agent(
        role="Writer",
        goal="Write engaging and clear summaries.",
        backstory="You are a professional communicator who synthesizes complex ideas.",
        llm=llm,
        verbose=False,
    )
    judge = Agent(
        role="Quality Reviewer",
        goal="Rate text quality (0.0-1.0) objectively.",
        backstory="You are a strict editor who demands clarity and accuracy. Reply with ONLY a score.",
        llm=llm,
        verbose=False,
    )

    # Note: Implementing the loop in Python while using CrewAI for agent tasks.

    # Step 1: Research
    print("Step 1: Research ...")
    task_research = Task(description=f"Gather key facts about: {topic}", expected_output="A list of key facts.", agent=researcher)
    facts = str(Crew(agents=[researcher], tasks=[task_research], verbose=False).kickoff())
    _write(f"{log_dir}/research.md", facts)

    # Step 2: Analysis
    print("Step 2: Analysis ...")
    task_analyze = Task(description=f"Analyze these facts and identify the 3 most significant insights:\n{facts}", expected_output="Analysis report.", agent=analyst)
    analysis = str(Crew(agents=[analyst], tasks=[task_analyze], verbose=False).kickoff())
    _write(f"{log_dir}/analysis.md", analysis)

    # Step 3: Writing loop
    iteration = 0
    while iteration < max_iterations:
        print(f"Step 3: Writing (iteration {iteration}) ...")
        task_write = Task(description=f"Write a clear, engaging 2-paragraph summary based on this analysis:\n{analysis}", expected_output="A polished summary.", agent=writer)
        draft = str(Crew(agents=[writer], tasks=[task_write], verbose=False).kickoff())
        _write(f"{log_dir}/draft_{iteration}.md", draft)

        # Step 4: Quality score
        print("Step 4: Quality score ...")
        task_score = Task(description=f"Rate the following text (0.0-1.0) for clarity and accuracy:\n{draft}", expected_output="A single numerical score.", agent=judge)
        score_str = str(Crew(agents=[judge], tasks=[task_score], verbose=False).kickoff())
        try:
            score = float(score_str.strip())
        except:
            score = 0.5
        print(f"Quality score: {score}")

        if score > 0.7:
            print(f"Quality threshold met at iteration {iteration}")
            break
        
        iteration += 1

    _write(f"{log_dir}/final.md", draft)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic for the pipeline")
@click.option("--max-iterations", default=3, help="Max quality cycles")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/21_multi_model_pipeline/logs-crewai", help="Log directory")
def main(topic, max_iterations, model, log_dir):
    """Multi-Model Pipeline — CrewAI edition"""
    run(topic, max_iterations, model, log_dir)

if __name__ == "__main__":
    main()
