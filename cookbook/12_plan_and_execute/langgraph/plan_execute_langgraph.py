"""
LangGraph equivalent of plan_execute.spl

Pattern: plan → (execute_step → validate_step → (replan? → plan)) → outline_files → (generate_file) → summarize

Usage:
    pip install langgraph langchain-ollama
    python cookbook/12_plan_and_execute/langgraph/plan_execute_langgraph.py \
        --task "Build a REST API for a todo app" \
        --output-dir "cookbook/12_plan_and_execute/langgraph/output"
"""

import argparse
import os
import re
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors CREATE FUNCTION in plan_execute.spl) ────────────────────

PLAN_PROMPT = """\
You are a senior software architect. Break down this task into clear implementation steps:

Task: {task}

Output a numbered list of concrete steps (3–6 steps). Each step should be specific
and independently executable. No prose — just the numbered list.
"""

COUNT_STEPS_PROMPT = """\
Count the number of numbered steps in this plan.
Return ONLY a single integer — no explanation, no text.
If there are more than {max_steps} steps, return {max_steps}.

Plan:
{plan}
"""

EXTRACT_STEP_PROMPT = """\
Extract step number {step_index} (0-indexed) from this numbered plan and return
ONLY that step's description. No numbering prefix. No extra text.

Plan:
{plan}
"""

EXECUTE_STEP_PROMPT = """\
You are a senior software engineer planning an implementation.

Step: {current_step}
Completed so far: {prior_results}

Describe in 2-3 sentences what this step produces and list the filenames it creates.
Be brief — no code yet, just the design decision and file list.
"""

VALIDATE_STEP_PROMPT = """\
Does the following design note meaningfully address the step?
Note: this is a planning phase — expect a 2-3 sentence description and a file list, NOT code.

Step: {current_step}
Design note: {step_result}

Reply with exactly one word: "passed" or "failed".
Only reply "failed" if the design note is empty, completely off-topic, or missing a file list.
"""

REPLAN_PROMPT = """\
A step in our implementation plan failed. Create a revised plan.

Original task: {task}
Original plan: {plan}
Failed at step: {step_index}
Failure details: {step_result}

Output a new numbered plan starting from step {step_index}. Keep completed steps as-is.
"""

OUTLINE_FILES_PROMPT = """\
You are a senior software engineer. Based on the implementation plan below, list every
source file that must be created to complete the task.

Task: {task}

Implementation plan:
{results}

Output a numbered list — one file per line — with the filename and a one-sentence description.
Always include a README.md as the last item.
Example:
1. app.py - Flask application entry point, registers blueprints and starts the server
2. models.py - SQLAlchemy ORM models for Todo and User
3. README.md - Setup instructions, project layout, and example API calls

No code. No prose. Just the numbered file list.
"""

COUNT_FILES_PROMPT = """\
Count the number of numbered items in this file list.
Return ONLY a single integer — no explanation, no text.

List:
{outline}
"""

EXTRACT_FILE_PROMPT = """\
Extract item number {file_index} (0-indexed) from this numbered file list and return
ONLY that item's filename and description. No number prefix. No extra text.

List:
{outline}
"""

GENERATE_FILE_PROMPT = """\
You are a senior software engineer. Write complete, runnable code for ONE source file.

Task: {task}

Implementation plan:
{results}

File to create: {file_desc}

Output a SINGLE fenced code block. The FIRST line inside the fence MUST be a filename comment:

```python
# filename: {filename}
...complete code...
```

Requirements:
- Complete, runnable code — no placeholders, no TODOs.
- Error handling, type hints, brief inline comments.
- Only this one file — nothing else.
"""

SUMMARIZE_PROMPT = """\
In 3-5 sentences, describe what was built for this task and how to run it.

Task: {task}
Files created:
{file_outline}
"""


# ── State ────────────────────────────────────────────────────────────────────

class PlanExecuteState(TypedDict):
    task:           str
    max_steps:      int
    max_replans:    int
    model:          str
    output_dir:     str
    log_dir:        str
    
    plan:           str
    step_count:     int
    step_index:     int
    results:        str
    replan_count:   int
    
    file_outline:   str
    file_count:     int
    file_index:     int
    
    final_report:   str


# ── Helpers (mirrors tools.py logic) ──────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

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


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_plan(state: PlanExecuteState) -> dict:
    print(f"Planning task: {state['task']} ...")
    plan = _invoke(state["model"], PLAN_PROMPT.format(task=state["task"]))
    count_str = _invoke(state["model"], COUNT_STEPS_PROMPT.format(
        plan=plan, max_steps=state["max_steps"]
    ))
    try:
        count = int(re.search(r"\d+", count_str).group())
    except:
        count = state["max_steps"]
    
    _write(f"{state['log_dir']}/plan.md", plan)
    return {"plan": plan, "step_count": count, "step_index": 0, "results": ""}

def node_execute_step(state: PlanExecuteState) -> dict:
    idx = state["step_index"]
    print(f"Executing step {idx}/{state['step_count']} ...")
    current_step = _invoke(state["model"], EXTRACT_STEP_PROMPT.format(
        plan=state["plan"], step_index=idx
    ))
    step_result = _invoke(state["model"], EXECUTE_STEP_PROMPT.format(
        current_step=current_step, prior_results=state["results"]
    ))
    
    validation = _invoke(state["model"], VALIDATE_STEP_PROMPT.format(
        current_step=current_step, step_result=step_result
    ))
    
    if "failed" in validation.lower() and state["replan_count"] < state["max_replans"]:
        # We need to replan
        print(f"Step {idx} failed — replanning ...")
        new_plan = _invoke(state["model"], REPLAN_PROMPT.format(
            task=state["task"], plan=state["plan"],
            step_index=idx, step_result=step_result
        ))
        count_str = _invoke(state["model"], COUNT_STEPS_PROMPT.format(
            plan=new_plan, max_steps=state["max_steps"]
        ))
        try:
            count = int(re.search(r"\d+", count_str).group())
        except:
            count = state["max_steps"]
        
        _write(f"{state['log_dir']}/replan_{state['replan_count']}.md", new_plan)
        return {
            "plan": new_plan,
            "step_count": count,
            "step_index": 0,
            "results": "",
            "replan_count": state["replan_count"] + 1
        }
    else:
        # Passed or max replans reached
        new_results = state["results"] + f"\n## Step {idx}\n" + step_result
        _write(f"{state['log_dir']}/step_{idx}.md", step_result)
        return {"results": new_results, "step_index": idx + 1}

def node_outline_files(state: PlanExecuteState) -> dict:
    print("Outlining files to generate ...")
    outline = _invoke(state["model"], OUTLINE_FILES_PROMPT.format(
        task=state["task"], results=state["results"]
    ))
    count_str = _invoke(state["model"], COUNT_FILES_PROMPT.format(outline=outline))
    try:
        count = int(re.search(r"\d+", count_str).group())
    except:
        count = 1
    
    _write(f"{state['log_dir']}/file_outline.md", outline)
    return {"file_outline": outline, "file_count": count, "file_index": 0}

def node_generate_file(state: PlanExecuteState) -> dict:
    idx = state["file_index"]
    print(f"Generating file {idx}/{state['file_count']} ...")
    file_desc = _invoke(state["model"], EXTRACT_FILE_PROMPT.format(
        outline=state["file_outline"], file_index=idx
    ))
    
    # Simple heuristic to get a filename for the prompt template if needed,
    # though the prompt asks the LLM to provide it.
    filename = file_desc.split("-")[0].strip()
    
    file_code = _invoke(state["model"], GENERATE_FILE_PROMPT.format(
        task=state["task"], results=state["results"], 
        file_desc=file_desc, filename=filename
    ))
    
    status = _write_code_files(file_code, state["output_dir"])
    print(f"  {status}")
    
    return {"file_index": idx + 1}

def node_summarize(state: PlanExecuteState) -> dict:
    print("Generating summary report ...")
    report = _invoke(state["model"], SUMMARIZE_PROMPT.format(
        task=state["task"], file_outline=state["file_outline"]
    ))
    _write(f"{state['log_dir']}/final_report.md", report)
    return {"final_report": report}


# ── Routing ──────────────────────────────────────────────────────────────────

def _route_steps(state: PlanExecuteState) -> str:
    if state["step_index"] < state["step_count"]:
        return "execute"
    return "outline"

def _route_files(state: PlanExecuteState) -> str:
    if state["file_index"] < state["file_count"]:
        return "generate"
    return "summarize"


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(PlanExecuteState)
    g.add_node("plan",          node_plan)
    g.add_node("execute_step",   node_execute_step)
    g.add_node("outline_files", node_outline_files)
    g.add_node("generate_file", node_generate_file)
    g.add_node("summarize",     node_summarize)

    g.set_entry_point("plan")
    g.add_edge("plan", "execute_step")
    
    # Note: node_execute_step handles the replan internally for state updates,
    # but we need to route back to it.
    g.add_conditional_edges("execute_step", _route_steps, {
        "execute": "execute_step",
        "outline": "outline_files"
    })
    
    g.add_edge("outline_files", "generate_file")
    g.add_conditional_edges("generate_file", _route_files, {
        "generate": "generate_file",
        "summarize": "summarize"
    })
    
    g.add_edge("summarize", END)
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Plan and Execute — LangGraph edition")
    p.add_argument("--task",         default="Build a REST API for a todo app")
    p.add_argument("--max-steps",    type=int, default=5)
    p.add_argument("--max-replans",  type=int, default=3)
    p.add_argument("--model",        default="gemma3")
    p.add_argument("--output-dir",   default="cookbook/12_plan_and_execute/langgraph/output")
    p.add_argument("--log-dir",      default="cookbook/12_plan_and_execute/langgraph/logs-langgraph")
    args = p.parse_args()

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "task":           args.task,
        "max_steps":      args.max_steps,
        "max_replans":    args.max_replans,
        "model":          args.model,
        "output_dir":     args.output_dir,
        "log_dir":        args.log_dir,
        "plan":           "",
        "step_count":     0,
        "step_index":     0,
        "results":        "",
        "replan_count":   0,
        "file_outline":   "",
        "file_count":     0,
        "file_index":     0,
        "final_report":   "",
    })

    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print(result["final_report"])

if __name__ == "__main__":
    main()
