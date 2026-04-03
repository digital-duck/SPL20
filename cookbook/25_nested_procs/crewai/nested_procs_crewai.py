"""
CrewAI equivalent of nested_procs.spl

Pattern: Task sequence with context passing.

Usage:
    pip install crewai langchain-ollama
    python cookbook/25_nested_procs/crewai/nested_procs_crewai.py \\
        --topic "quantum computing" --audience "high school students"
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

def run(topic: str, audience: str, depth: str, model: str, log_dir: str):
    llm = f"ollama/{model}"

    educator = Agent(
        role="Expert Educator",
        goal="Explain complex topics simply.",
        backstory="You specialize in making difficult concepts accessible to any audience.",
        llm=llm,
        verbose=False,
    )

    # Step 1: Research
    task_research = Task(
        description=f"Provide a research overview for: {topic}",
        expected_output="A list of facts.",
        agent=educator,
    )
    # Step 2: Explain
    task_explain = Task(
        description=f"Explain the research for {audience} in a clear, engaging style.",
        expected_output="A base explanation.",
        agent=educator,
        context=[task_research],
    )
    # Step 3: Example
    task_example = Task(
        description=f"Create a concrete example for {topic} for {audience}.",
        expected_output="A concrete example.",
        agent=educator,
        context=[task_explain],
    )
    # Step 4: Calibrate
    task_calibrate = Task(
        description=f"Ensure the explanation is appropriate for {audience}. Simplify if needed.",
        expected_output="A calibrated explanation.",
        agent=educator,
        context=[task_explain],
    )
    # Step 5: Assemble
    task_assemble = Task(
        description=f"Assemble a final {depth} depth article on {topic} for {audience}.",
        expected_output="A final article.",
        agent=educator,
        context=[task_calibrate, task_example],
    )

    print("Running layered explainer crew ...")
    crew = Crew(
        agents=[educator],
        tasks=[task_research, task_explain, task_example, task_calibrate, task_assemble],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    article = str(result)

    _write(f"{log_dir}/final.md", article)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic to explain")
@click.option("--audience", required=True, help="Target audience")
@click.option("--depth", default="standard", help="Article depth")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/25_nested_procs/logs-crewai", help="Log directory")
def main(topic, audience, depth, model, log_dir):
    """Nested Procedures — CrewAI edition"""
    run(topic, audience, depth, model, log_dir)

if __name__ == "__main__":
    main()
