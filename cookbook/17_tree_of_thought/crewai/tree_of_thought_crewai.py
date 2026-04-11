"""
CrewAI equivalent of tree_of_thought.spl

Multiple Agents (Researcher, Analyst, Judge, Synthesizer) collaborate on
exploring reasoning paths and producing a final solution.

Usage:
    pip install crewai langchain-ollama
    python cookbook/17_tree_of_thought/crewai/tree_of_thought_crewai.py \
        --problem "Design a sustainable urban transport system."
"""

import click
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()


# ── Main runner ───────────────────────────────────────────────────────────────

def run(problem: str, models: list, log_dir: str) -> str:
    results_map = {}
    
    # Phase 1 & 2: Explore paths (multi-model)
    for i, model in enumerate(models):
        print(f"Exploring path {i+1}/{len(models)} using {model}...")
        llm = f"ollama/{model}"
        
        researcher = Agent(
            role="Creative Researcher",
            goal=f"Provide a unique approach and develop it for the problem: {problem}",
            backstory="You are a researcher who excels at finding unconventional solutions.",
            llm=llm,
            verbose=False,
        )
        analyst = Agent(
            role="Technical Analyst",
            goal=f"Score reasoning paths based on feasibility and depth.",
            backstory="You are an analyst with a keen eye for technical detail and feasibility.",
            llm=llm,
            verbose=False,
        )

        developed_path = _run_task(
            researcher,
            description=f"Provide an initial unique approach and develop it one level deeper for: {problem}",
            expected_output="A detailed, multi-step reasoning path.",
        )
        
        score = _run_task(
            analyst,
            description=f"Score this reasoning path (1-10): {developed_path}",
            expected_output="A single numeric score from 1 to 10.",
        )
        
        results_map[model] = {"content": developed_path, "score": score}
        _write(f"{log_dir}/path_{model}.md", developed_path)

    # Base model for final steps
    base_llm = f"ollama/{models[0]}"
    
    selector = Agent(
        role="Senior Selector",
        goal="Select the best reasoning path from a set of options.",
        backstory="You are an expert at evaluating multiple approaches and picking the strongest winner.",
        llm=base_llm,
    )
    refiner = Agent(
        role="Technical Writer",
        goal="Refine a reasoning path into a polished final solution.",
        backstory="You turn rough ideas into professional, comprehensive solutions.",
        llm=base_llm,
    )
    judge = Agent(
        role="Critical Judge",
        goal="Verify if a solution is sound and complete.",
        backstory="You ensure that final outputs meet high standards of quality and correctness.",
        llm=base_llm,
    )
    synthesizer = Agent(
        role="Synthesis Specialist",
        goal="Combine insights from multiple paths into one final solution.",
        backstory="You are a master of merging disparate ideas into a cohesive whole.",
        llm=base_llm,
    )

    # Phase 4: Select best
    print("Selecting best path...")
    best_path = _run_task(
        selector,
        description=f"Review these paths and scores: {results_map}\nIdentify and output the best path's content.",
        expected_output="The content of the best reasoning path.",
    )
    
    # Phase 5: Refine
    print("Refining winning path...")
    solution = _run_task(
        refiner,
        description=f"Refine this winning path into a final solution: {best_path}",
        expected_output="A complete, polished, and comprehensive solution.",
    )
    
    # Phase 6: Verify
    print("Verifying solution...")
    verification = _run_task(
        judge,
        description=f"Is this solution sound and complete? Solution: {solution}\nReply 'sound' or provide critique.",
        expected_output="Exactly 'sound' or a brief critique.",
    )
    _write(f"{log_dir}/verification.md", verification)

    if "sound" not in verification.lower():
        print("Verification failed — synthesizing all paths...")
        solution = _run_task(
            synthesizer,
            description=f"Verification failed. Synthesize a final solution from all paths: {results_map}",
            expected_output="A comprehensive synthesized solution.",
        )

    _write(f"{log_dir}/final_solution.md", solution)
    return solution


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--problem", default="Design a sustainable urban transport system.", show_default=True)
@click.option("--models",  multiple=True, default=["gemma3", "phi4", "qwen2.5"], show_default=True)
@click.option("--log-dir", default="cookbook/17_tree_of_thought/crewai/logs-crewai", show_default=True)
def main(problem: str, models: tuple, log_dir: str):
    result = run(problem, list(models), log_dir)
    print("\n" + "=" * 60)
    print("FINAL SOLUTION:")
    print(result)

if __name__ == "__main__":
    main()
