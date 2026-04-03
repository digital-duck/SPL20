"""
CrewAI equivalent of code_review.spl

Pattern: Detect Lang → [Security, Performance, Style, Bug Analysis] → Synthesize

Usage:
    pip install crewai langchain-ollama
    python cookbook/15_code_review/crewai/code_review_autogen.py \\
        --code "def foo(x): return eval(x)"
"""

import click
import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _read_code(code_input: str) -> str:
    if os.path.isfile(code_input):
        return Path(code_input).read_text(encoding="utf-8")
    return code_input


# ── Main runner ───────────────────────────────────────────────────────────────

def run(code_input: str, model: str, log_dir: str):
    llm = f"ollama/{model}"
    code = _read_code(code_input)

    detector = Agent(
        role="Language Detector",
        goal="Identify the programming language of the provided code.",
        backstory="You are a polyglot programmer who can identify any language from a code snippet.",
        llm=llm,
        verbose=False,
    )
    auditor = Agent(
        role="Code Auditor",
        goal="Identify security, performance, style, and bug issues in code.",
        backstory="You are a senior developer with a keen eye for detail and best practices.",
        llm=llm,
        verbose=False,
    )
    reviewer = Agent(
        role="Synthesis Reviewer",
        goal="Create a final, structured code review report.",
        backstory="You excel at synthesizing technical findings into clear, actionable advice.",
        llm=llm,
        verbose=False,
    )

    # Step 1: Detect
    task_detect = Task(
        description=f"Identify the language of this code:\n{code[:500]}",
        expected_output="The name of the programming language.",
        agent=detector,
    )
    # Step 2: Audits
    task_security = Task(
        description=f"Perform a security audit of the code:\n{code}",
        expected_output="Security findings.",
        agent=auditor,
    )
    task_performance = Task(
        description=f"Analyze performance of the code:\n{code}",
        expected_output="Performance findings.",
        agent=auditor,
    )
    task_style = Task(
        description=f"Review style and best practices of the code:\n{code}",
        expected_output="Style findings.",
        agent=auditor,
    )
    task_bugs = Task(
        description=f"Identify potential bugs in the code:\n{code}",
        expected_output="Bug findings.",
        agent=auditor,
    )
    # Step 3: Synthesis
    task_synthesis = Task(
        description=f"Synthesize all findings into a final report for the code snippet.",
        expected_output="A final comprehensive code review report.",
        agent=reviewer,
        context=[task_security, task_performance, task_style, task_bugs],
    )

    print("Running code review crew ...")
    crew = Crew(
        agents=[detector, auditor, reviewer],
        tasks=[task_detect, task_security, task_performance, task_style, task_bugs, task_synthesis],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    review = str(result)

    _write(f"{log_dir}/final.md", review)
    print("Committed | status=complete")


@click.command()
@click.option("--code", required=True, help="Code to review or path to file")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/15_code_review/logs-crewai", help="Log directory")
def main(code, model, log_dir):
    """Automated Code Review — CrewAI edition"""
    run(code, model, log_dir)

if __name__ == "__main__":
    main()
