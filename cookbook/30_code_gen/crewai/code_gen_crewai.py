"""
CrewAI equivalent of code_gen.spl

Pattern: Spec → Implement → Review → (fix if needed) → Test → Assemble

Usage:
    pip install crewai langchain-ollama
    python cookbook/30_code_gen/crewai/code_gen_crewai.py \\
        --spec "A function that validates an email address"
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

def _load_spec(spec_input: str) -> str:
    if os.path.isfile(spec_input):
        return Path(spec_input).read_text(encoding="utf-8")
    return spec_input


# ── Main runner ───────────────────────────────────────────────────────────────

def run(spec_input: str, language: str, framework: str, model: str, log_dir: str):
    llm = f"ollama/{model}"
    spec = _load_spec(spec_input)

    coder = Agent(
        role=f"{language} Developer",
        goal=f"Implement high-quality {language} code.",
        backstory=f"You are an expert {language} engineer who writes clean, idiomatic code.",
        llm=llm,
        verbose=False,
    )
    reviewer = Agent(
        role="Code Reviewer",
        goal="Identify any bugs or spec violations in the code.",
        backstory="You are a meticulous reviewer with an eye for edge cases.",
        llm=llm,
        verbose=False,
    )
    tester = Agent(
        role="QA Engineer",
        goal=f"Generate unit tests using {framework}.",
        backstory="You specialize in comprehensive test coverage and reliability.",
        llm=llm,
        verbose=False,
    )

    # Step 1: Implement
    task_implement = Task(
        description=f"Implement the following spec in {language}:\n{spec}",
        expected_output=f"{language} implementation code.",
        agent=coder,
    )
    # Step 2: Review
    task_review = Task(
        description=f"Review the generated code against the spec: {spec}",
        expected_output="Review notes identifying any issues.",
        agent=reviewer,
        context=[task_implement],
    )
    # Step 3: Test
    task_test = Task(
        description=f"Generate {framework} unit tests for the implementation.",
        expected_output=f"{framework} test code.",
        agent=tester,
        context=[task_implement, task_review],
    )

    print("Running code gen crew ...")
    crew = Crew(
        agents=[coder, reviewer, tester],
        tasks=[task_implement, task_review, task_test],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    
    # Assembly (in CrewAI, we can combine the task results)
    final = f"### Implementation\n\n{task_implement.output.raw}\n\n### Unit Tests\n\n{task_test.output.raw}"
    _write(f"{log_dir}/final.md", final)
    print("Committed | status=complete")


@click.command()
@click.option("--spec", required=True, help="Spec text or file path")
@click.option("--language", default="Python", help="Programming language")
@click.option("--framework", default="pytest", help="Test framework")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/30_code_gen/logs-crewai", help="Log directory")
def main(spec, language, framework, model, log_dir):
    """Code Generator + Tests — CrewAI edition"""
    run(spec, language, framework, model, log_dir)

if __name__ == "__main__":
    main()
