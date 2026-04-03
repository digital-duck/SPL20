"""
AutoGen equivalent of code_review.spl

Pattern: Detect Lang → [Security, Performance, Style, Bug Analysis] → Synthesize

Usage:
    pip install pyautogen
    python cookbook/15_code_review/autogen/code_review_autogen.py \\
        --code "def foo(x): return eval(x)"
"""

import click
import os
from pathlib import Path

from autogen import ConversableAgent


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
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    code = _read_code(code_input)
    
    detector = ConversableAgent("Detector", system_message="Identify the programming language.", llm_config=llm_config, human_input_mode="NEVER")
    auditor  = ConversableAgent("Auditor",  system_message="Perform code audits (security, perf, style, bugs).", llm_config=llm_config, human_input_mode="NEVER")
    reviewer = ConversableAgent("Reviewer", system_message="Synthesize findings into a final report.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Detect
    print("Detecting language ...")
    chat = detector.initiate_chat(detector, message=f"Identify language:\n{code[:500]}", max_turns=1)
    language = chat.chat_history[-1]["content"]

    # Step 2: Parallel Audits (Sequential in this script for parity)
    print("Pass 1: Security audit ...")
    chat = auditor.initiate_chat(auditor, message=f"Security audit of {language} code:\n{code}", max_turns=1)
    security = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/security.md", security)

    print("Pass 2: Performance review ...")
    chat = auditor.initiate_chat(auditor, message=f"Performance review of {language} code:\n{code}", max_turns=1)
    performance = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/performance.md", performance)

    print("Pass 3: Style review ...")
    chat = auditor.initiate_chat(auditor, message=f"Style review of {language} code:\n{code}", max_turns=1)
    style = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/style.md", style)

    print("Pass 4: Bug detection ...")
    chat = auditor.initiate_chat(auditor, message=f"Bug detection for {language} code:\n{code}", max_turns=1)
    bugs = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/bugs.md", bugs)

    # Step 3: Synthesize
    print("Synthesizing findings ...")
    prompt = f"Synthesize these findings:\nSecurity: {security}\nPerformance: {performance}\nStyle: {style}\nBugs: {bugs}"
    chat = reviewer.initiate_chat(reviewer, message=prompt, max_turns=1)
    review = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/review.md", review)
    _write(f"{log_dir}/final.md", review)
    
    print("Committed | status=complete")


@click.command()
@click.option("--code", required=True, help="Code to review or path to file")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/15_code_review/logs-autogen", help="Log directory")
def main(code, model, log_dir):
    """Automated Code Review — AutoGen edition"""
    run(code, model, log_dir)

if __name__ == "__main__":
    main()
