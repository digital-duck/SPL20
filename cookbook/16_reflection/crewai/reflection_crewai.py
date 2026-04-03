"""
CrewAI equivalent of reflection.spl

Pattern: solve → reflect → score → (confident? commit : correct → loop)

Usage:
    pip install crewai langchain-ollama
    python cookbook/16_reflection/crewai/reflection_crewai.py \\
        --problem "What are the trade-offs of microservices vs monoliths?"
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

def run(problem: str, max_refs: int, model: str, log_dir: str):
    llm = f"ollama/{model}"

    solver = Agent(
        role="Problem Solver",
        goal="Solve technical and complex problems.",
        backstory="You are an expert who provides thorough and accurate solutions.",
        llm=llm,
        verbose=False,
    )
    reflector = Agent(
        role="Reflection Expert",
        goal="Review your own work for errors and gaps.",
        backstory="You are critical of your own reasoning and seek perfection.",
        llm=llm,
        verbose=False,
    )
    judge = Agent(
        role="Quality Judge",
        goal="Assess confidence in a solution based on reflection.",
        backstory="You are a strict judge who only approves high-quality work. Reply with ONLY a score (0.0-1.0).",
        llm=llm,
        verbose=False,
    )

    # Note: CrewAI is not built for dynamic loops of this nature natively.
    # We will implement the loop in Python while using CrewAI for the agent tasks.

    print("Initial solution ...")
    task_solve = Task(description=f"Solve this problem: {problem}", expected_output="A full solution.", agent=solver)
    answer = str(Crew(agents=[solver], tasks=[task_solve], verbose=False).kickoff())
    _write(f"{log_dir}/answer_0.md", answer)

    iteration = 0
    while iteration < max_refs:
        print(f"Reflection iteration {iteration} ...")
        
        # Reflect
        task_reflect = Task(description=f"Reflect on this answer for '{problem}':\n{answer}", expected_output="A reflection identifying gaps.", agent=reflector)
        reflection = str(Crew(agents=[reflector], tasks=[task_reflect], verbose=False).kickoff())
        _write(f"{log_dir}/reflection_{iteration}.md", reflection)

        # Score
        task_score = Task(description=f"Rate confidence (0.0-1.0) based on reflection.\nAnswer: {answer}\nReflection: {reflection}", expected_output="A score between 0.0 and 1.0.", agent=judge)
        score_str = str(Crew(agents=[judge], tasks=[task_score], verbose=False).kickoff())
        try:
            confidence = float(score_str.strip())
        except:
            confidence = 0.5
        print(f"Confidence: {confidence}")

        if confidence > 0.85:
            print(f"Confident at iteration {iteration}")
            break

        # Correct
        print("Correcting answer ...")
        task_correct = Task(description=f"Correct this answer for '{problem}' based on reflection:\n{reflection}\nOriginal Answer:\n{answer}", expected_output="An improved answer.", agent=solver)
        answer = str(Crew(agents=[solver], tasks=[task_correct], verbose=False).kickoff())
        iteration += 1
        _write(f"{log_dir}/answer_{iteration}.md", answer)

    _write(f"{log_dir}/final.md", answer)
    print("Committed | status=complete")


@click.command()
@click.option("--problem", required=True, help="Problem to solve")
@click.option("--max-reflections", default=3, help="Max reflection cycles")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/16_reflection/logs-crewai", help="Log directory")
def main(problem, max_reflections, model, log_dir):
    """Reflection Agent — CrewAI edition"""
    run(problem, max_reflections, model, log_dir)

if __name__ == "__main__":
    main()
