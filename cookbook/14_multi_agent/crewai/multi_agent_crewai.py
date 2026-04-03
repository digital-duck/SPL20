"""
CrewAI equivalent of multi_agent.spl

Pattern: Researcher → Analyst → Writer (Sequential process)

Usage:
    pip install crewai langchain-ollama
    python cookbook/14_multi_agent/crewai/multi_agent_crewai.py \\
        --topic "Impact of AI on healthcare"
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

def run(topic: str, model: str, log_dir: str):
    llm = f"ollama/{model}"

    researcher = Agent(
        role="Researcher",
        goal="Gather key facts and sources.",
        backstory="You are a skilled researcher who excels at finding key information and themes.",
        llm=llm,
        verbose=False,
    )
    analyst = Agent(
        role="Analyst",
        goal="Identify trends, risks, and opportunities.",
        backstory="You are a brilliant analyst who identifies key patterns and strategic insights.",
        llm=llm,
        verbose=False,
    )
    writer = Agent(
        role="Writer",
        goal="Produce a polished final report.",
        backstory="You are an expert writer who can synthesize complex information into a smooth narrative.",
        llm=llm,
        verbose=False,
    )

    # Step 1: Research
    task_research = Task(
        description=f"Gather research for the topic: {topic}",
        expected_output="A list of facts and key themes.",
        agent=researcher,
    )
    # Step 2: Analysis
    task_analysis = Task(
        description=f"Analyze the research provided for the topic: {topic}",
        expected_output="A list of trends, risks, and opportunities.",
        agent=analyst,
    )
    # Step 3: Writing
    task_writing = Task(
        description=f"Write a polished report on {topic} based on the research and analysis.",
        expected_output="A final high-quality report.",
        agent=writer,
    )

    print("Running multi-agent crew ...")
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[task_research, task_analysis, task_writing],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    report = str(result)

    _write(f"{log_dir}/final.md", report)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic for the report")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/14_multi_agent/logs-crewai", help="Log directory")
def main(topic, model, log_dir):
    """Multi-Agent Collaboration — CrewAI edition"""
    run(topic, model, log_dir)

if __name__ == "__main__":
    main()
