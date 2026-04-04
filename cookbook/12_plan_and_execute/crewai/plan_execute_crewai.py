"""
CrewAI equivalent of plan_execute.spl

Three Agents (Planner, Executor, Judge) with a manual workflow loop.
CrewAI Tasks are used to coordinate individual steps.

Usage:
    pip install crewai langchain-ollama
    python cookbook/12_plan_and_execute/crewai/plan_execute_crewai.py \
        --task "Build a REST API for a todo app"
"""

import argparse
import os
import re
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Helpers (mirrors tools.py logic) ──────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _write_code_files(content: str, output_dir: str) -> str:
    if not output_dir.strip():
        return "No output_dir specified — files not written"

    os.makedirs(output_dir, exist_ok=True)
    pattern = re.compile(
        r"```(?:\w+)?\n#\s*filename:\s*(\S+)\n(.*?)```",
        re.DOTALL,
    )
    files_written = []
    for match in pattern.finditer(content):
        rel_path = match.group(1).strip()
        code = match.group(2)
        filepath = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        files_written.append(rel_path)

    if not files_written:
        return "No code files found."
    return f"Written {len(files_written)} file(s): {', '.join(files_written)}"

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()

def _extract_steps(plan: str) -> list[str]:
    # Extract lines starting with a number and a dot
    steps = re.findall(r"^\d+\.\s+(.*)$", plan, re.MULTILINE)
    return steps


# ── Main runner ───────────────────────────────────────────────────────────────

def run(task_desc: str, max_steps: int, max_replans: int, model: str, output_dir: str, log_dir: str) -> str:
    llm = f"ollama/{model}"

    planner = Agent(
        role="Senior Software Architect",
        goal="Break down implementation tasks into concrete steps and list required source files.",
        backstory="You are a senior architect with a focus on clear planning and modular design.",
        llm=llm,
        verbose=False,
    )
    executor = Agent(
        role="Senior Software Engineer",
        goal="Produce design notes for implementation steps and write high-quality source code.",
        backstory="You are a senior engineer who writes clean, idiomatic, and runnable code.",
        llm=llm,
        verbose=False,
    )
    judge = Agent(
        role="Technical Judge",
        goal="Validate that design notes meaningfully address implementation steps.",
        backstory="You are a strict judge who ensures that all required design elements are present.",
        llm=llm,
        verbose=False,
    )

    # Phase 1: Plan
    print(f"Planning task: {task_desc} ...")
    plan = _run_task(
        planner,
        description=f"Create a numbered implementation plan (3-6 steps) for: {task_desc}",
        expected_output="A numbered list of concrete steps.",
    )
    _write(f"{log_dir}/plan.md", plan)
    
    steps = _extract_steps(plan)[:max_steps]
    results = ""
    replan_count = 0
    step_idx = 0
    
    # Phase 2: Execute steps
    while step_idx < len(steps):
        current_step = steps[step_idx]
        print(f"Executing step {step_idx}/{len(steps)}: {current_step[:50]}...")
        
        step_result = _run_task(
            executor,
            description=f"Produce design notes for this step: {current_step}\nCompleted so far: {results}\nInclude a list of filenames.",
            expected_output="2-3 sentence description and a list of filenames.",
        )
        
        validation = _run_task(
            judge,
            description=f"Does this design note meaningfully address the step '{current_step}'?\n\n{step_result}\n\nReply 'passed' or 'failed'.",
            expected_output="Exactly one word: 'passed' or 'failed'.",
        )
        
        if "failed" in validation.lower() and replan_count < max_replans:
            print(f"Step {step_idx} failed — replanning ...")
            plan = _run_task(
                planner,
                description=f"Re-plan starting from step {step_idx}.\nOriginal task: {task_desc}\nPlan: {plan}\nFailure details: {step_result}",
                expected_output="A new numbered plan starting from the failed step.",
            )
            steps = _extract_steps(plan)[:max_steps]
            results = ""
            step_idx = 0
            replan_count += 1
            _write(f"{log_dir}/replan_{replan_count}.md", plan)
            continue
        else:
            results += f"\n## Step {step_idx}\n" + step_result
            _write(f"{log_dir}/step_{step_idx}.md", step_result)
            step_idx += 1

    # Phase 3: Outline files
    print("Outlining files ...")
    file_outline = _run_task(
        planner,
        description=f"List all source files to create for: {task_desc}\n\nPlan results:\n{results}",
        expected_output="A numbered list of files with one-sentence descriptions.",
    )
    _write(f"{log_dir}/file_outline.md", file_outline)
    
    files = _extract_steps(file_outline)
    
    # Phase 4: Generate files
    for i, file_desc in enumerate(files):
        print(f"Generating file {i}/{len(files)}: {file_desc[:50]}...")
        file_code = _run_task(
            executor,
            description=f"Write complete code for this file.\nTask: {task_desc}\nResults: {results}\nFile: {file_desc}\nInclude '# filename: path' in code block.",
            expected_output="A single fenced code block containing complete code.",
        )
        status = _write_code_files(file_code, output_dir)
        print(f"  {status}")

    # Phase 5: Summarize
    print("Summarizing ...")
    final_report = _run_task(
        planner,
        description=f"Summarize what was built for: {task_desc}\n\nFiles:\n{file_outline}",
        expected_output="3-5 sentence description of what was built.",
    )
    _write(f"{log_dir}/final_report.md", final_report)
    
    return final_report


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Plan and Execute — CrewAI edition")
    p.add_argument("--task",         default="Build a REST API for a todo app")
    p.add_argument("--max-steps",    type=int, default=5)
    p.add_argument("--max-replans",  type=int, default=3)
    p.add_argument("--model",        default="gemma3")
    p.add_argument("--output-dir",   default="cookbook/12_plan_and_execute/crewai/output")
    p.add_argument("--log-dir",      default="cookbook/12_plan_and_execute/crewai/logs-crewai")
    args = p.parse_args()

    result = run(args.task, args.max_steps, args.max_replans, args.model, args.output_dir, args.log_dir)
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print(result)

if __name__ == "__main__":
    main()
