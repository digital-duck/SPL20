"""
CrewAI equivalent of chain.spl

Three Agents (Researcher, Analyst, Summarizer) with sequential Tasks.
context= chaining passes each output to the next task automatically.
CrewAI has no native sequential GENERATE primitive — each LLM call
requires a new Agent + Task + Crew instantiation.

Usage:
    pip install crewai langchain-ollama
    python cookbook/09_chain_of_thought/crewai/chain_crewai.py \\
        --topic "distributed AI inference"
    python cookbook/09_chain_of_thought/crewai/chain_crewai.py \\
        --topic "quantum computing" --model llama3.2
"""

import click
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from langchain_ollama import ChatOllama


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, model: str, log_dir: str) -> str:
    llm = ChatOllama(model=model)

    # SPL: GENERATE research(@topic) INTO @research
    researcher = Agent(
        role="Researcher",
        goal="Research topics thoroughly",
        backstory="Expert researcher with broad domain knowledge and strong "
                  "fact-finding skills.",
        llm=llm,
        verbose=False,
    )
    # SPL: GENERATE analyze(@research) INTO @analysis
    analyst = Agent(
        role="Analyst",
        goal="Analyze research and extract key insights",
        backstory="Expert analyst skilled at identifying patterns, implications, "
                  "and actionable insights from research.",
        llm=llm,
        verbose=False,
    )
    # SPL: GENERATE summarize(@analysis) INTO @summary
    summarizer = Agent(
        role="Summarizer",
        goal="Synthesize analysis into clear executive summaries",
        backstory="Expert writer skilled at distilling complex analysis into "
                  "concise, readable summaries.",
        llm=llm,
        verbose=False,
    )

    task_research = Task(
        description=f"Research this topic thoroughly: {topic}\n\n"
                    "Provide key facts, current state, and important context.",
        expected_output="Comprehensive research notes covering key facts and context.",
        agent=researcher,
    )
    task_analyze = Task(
        description="Analyze the research findings. Identify patterns, "
                    "implications, and key insights.",
        expected_output="Analytical insights with identified patterns and implications.",
        agent=analyst,
        context=[task_research],   # receives @research output automatically
    )
    task_summarize = Task(
        description="Write a concise 2-3 paragraph executive summary of the analysis.",
        expected_output="Executive summary: 2-3 clear paragraphs.",
        agent=summarizer,
        context=[task_analyze],    # receives @analysis output automatically
    )

    print("Running chain of thought pipeline ...")
    crew = Crew(
        agents=[researcher, analyst, summarizer],
        tasks=[task_research, task_analyze, task_summarize],
        process=Process.sequential,
        verbose=False,
    )
    # COMMIT @summary WITH status = 'complete'
    result = crew.kickoff()
    summary = str(result)

    # Log each step's output
    if task_research.output:
        _write(f"{log_dir}/research.md", task_research.output.raw)
    if task_analyze.output:
        _write(f"{log_dir}/analysis.md", task_analyze.output.raw)
    _write(f"{log_dir}/summary.md", summary)
    _write(f"{log_dir}/final.md", summary)
    print("Done | status=complete")
    return summary


# ── Entry point  (SPL: built into CLI — `spl run ...`) ────────────────────────

@click.command()
@click.option("--topic",   required=True,    help="Topic to analyze")
@click.option("--model",   default="gemma3", show_default=True)
@click.option("--log-dir", default="cookbook/09_chain_of_thought/crewai/logs", show_default=True)
def main(topic: str, model: str, log_dir: str):
    result = run(topic, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
