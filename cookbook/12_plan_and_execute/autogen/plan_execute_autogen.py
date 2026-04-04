"""
AutoGen equivalent of plan_execute.spl

Three Agents — Planner, Executor, and Validator.
A procedural script coordinates the agents to match the SPL workflow.

Usage:
    pip install pyautogen
    python cookbook/12_plan_and_execute/autogen/plan_execute_autogen.py \
        --task "Build a REST API for a todo app"
"""

import argparse
import os
import re
from pathlib import Path

from autogen import ConversableAgent


# ── Agent system messages (mirrors PROMPT blocks in plan_execute.spl) ──────────

PLANNER_SYSTEM = """\
You are a senior software architect. Your job is to plan implementation tasks.
Break down tasks into clear,Numbered implementation steps (3-6 steps).
When outlining files, provide a numbered list with filename and a one-sentence description.
Be concise and specific."""

EXECUTOR_SYSTEM = """\
You are a senior software engineer. Your job is to execute implementation steps.
When planning a step, describe what it produces and list the filenames it creates (2-3 sentences).
When generating code, provide a SINGLE fenced code block with a '# filename: path' comment."""

VALIDATOR_SYSTEM = """\
You are a strict technical judge.
Review design notes for implementation steps.
If the notes are meaningful and include a file list, reply with exactly: passed
Otherwise, reply with: failed"""


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

def _extract_steps(plan: str) -> list[str]:
    # Extract lines starting with a number and a dot
    steps = re.findall(r"^\d+\.\s+(.*)$", plan, re.MULTILINE)
    return steps


# ── Main runner ───────────────────────────────────────────────────────────────

def run(task: str, max_steps: int, max_replans: int, model: str, output_dir: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    planner = ConversableAgent(
        name="Planner",
        system_message=PLANNER_SYSTEM,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    executor = ConversableAgent(
        name="Executor",
        system_message=EXECUTOR_SYSTEM,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    validator = ConversableAgent(
        name="Validator",
        system_message=VALIDATOR_SYSTEM,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    # Phase 1: Plan
    print(f"Planning task: {task} ...")
    plan_reply = planner.generate_reply(messages=[{"content": f"Create an implementation plan for: {task}", "role": "user"}])
    plan = str(plan_reply)
    _write(f"{log_dir}/plan.md", plan)
    
    steps = _extract_steps(plan)[:max_steps]
    results = ""
    replan_count = 0
    step_idx = 0
    
    # Phase 2: Execute steps
    while step_idx < len(steps):
        current_step = steps[step_idx]
        print(f"Executing step {step_idx}/{len(steps)}: {current_step[:50]}...")
        
        executor_reply = executor.generate_reply(messages=[{
            "content": f"Execute this step: {current_step}\nCompleted so far: {results}",
            "role": "user"
        }])
        step_result = str(executor_reply)
        
        validation_reply = validator.generate_reply(messages=[{
            "content": f"Validate this design note for step '{current_step}':\n\n{step_result}",
            "role": "user"
        }])
        validation = str(validation_reply)
        
        if "failed" in validation.lower() and replan_count < max_replans:
            print(f"Step {step_idx} failed — replanning ...")
            replan_reply = planner.generate_reply(messages=[{
                "content": f"A step failed. Re-plan starting from this step.\nTask: {task}\nPlan: {plan}\nFailed step index: {step_idx}\nFailure details: {step_result}",
                "role": "user"
            }])
            plan = str(replan_reply)
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
    outline_reply = planner.generate_reply(messages=[{
        "content": f"Based on these results, outline the source files to create for: {task}\n\nResults:\n{results}",
        "role": "user"
    }])
    file_outline = str(outline_reply)
    _write(f"{log_dir}/file_outline.md", file_outline)
    
    files = _extract_steps(file_outline) # Reusing the same extraction logic
    
    # Phase 4: Generate files
    for i, file_desc in enumerate(files):
        print(f"Generating file {i}/{len(files)}: {file_desc[:50]}...")
        file_reply = executor.generate_reply(messages=[{
            "content": f"Write complete code for this file based on the plan.\nTask: {task}\nResults: {results}\nFile: {file_desc}",
            "role": "user"
        }])
        file_code = str(file_reply)
        status = _write_code_files(file_code, output_dir)
        print(f"  {status}")

    # Phase 5: Summarize
    print("Summarizing ...")
    summary_reply = planner.generate_reply(messages=[{
        "content": f"Summarize what was built for: {task}\n\nFiles:\n{file_outline}",
        "role": "user"
    }])
    final_report = str(summary_reply)
    _write(f"{log_dir}/final_report.md", final_report)
    
    return final_report


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Plan and Execute — AutoGen edition")
    p.add_argument("--task",         default="Build a REST API for a todo app")
    p.add_argument("--max-steps",    type=int, default=5)
    p.add_argument("--max-replans",  type=int, default=3)
    p.add_argument("--model",        default="gemma3")
    p.add_argument("--output-dir",   default="cookbook/12_plan_and_execute/autogen/output")
    p.add_argument("--log-dir",      default="cookbook/12_plan_and_execute/autogen/logs-autogen")
    args = p.parse_args()

    result = run(args.task, args.max_steps, args.max_replans, args.model, args.output_dir, args.log_dir)
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print(result)

if __name__ == "__main__":
    main()
