"""
AutoGen equivalent of code_gen.spl

Pattern: Spec → Implement → Review → (fix if needed) → Test → Assemble

Usage:
    pip install pyautogen
    python cookbook/30_code_gen/autogen/code_gen_autogen.py \\
        --spec "A function that validates an email address"
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

def _load_spec(spec_input: str) -> str:
    if os.path.isfile(spec_input):
        return Path(spec_input).read_text(encoding="utf-8")
    return spec_input


# ── Main runner ───────────────────────────────────────────────────────────────

def run(spec_input: str, language: str, framework: str, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    coder    = ConversableAgent("Coder",    system_message=f"You are a {language} developer.", llm_config=llm_config, human_input_mode="NEVER")
    reviewer = ConversableAgent("Reviewer", system_message="You are a strict code reviewer.", llm_config=llm_config, human_input_mode="NEVER")
    tester   = ConversableAgent("Tester",   system_message=f"You write unit tests using {framework}.", llm_config=llm_config, human_input_mode="NEVER")

    spec = _load_spec(spec_input)
    print(f"Spec resolved ({spec[:50]}...)")

    # Step 1: Implement
    print(f"Generating {language} implementation ...")
    chat = coder.initiate_chat(coder, message=f"Implement this spec in {language}:\n{spec}", max_turns=1)
    implementation = chat.chat_history[-1]["content"]

    # Step 2: Review
    print("Reviewing implementation ...")
    chat = reviewer.initiate_chat(reviewer, message=f"Review this {language} code against spec:\n{implementation}\nSpec:\n{spec}", max_turns=1)
    notes = chat.chat_history[-1]["content"]

    # Step 3: Fix if needed
    if any(word in notes.lower() for word in ["issue", "error", "problem"]):
        print("Issues found — fixing ...")
        chat = coder.initiate_chat(coder, message=f"Fix this code based on review:\n{implementation}\nNotes:\n{notes}", max_turns=1)
        implementation = chat.chat_history[-1]["content"]

    # Step 4: Test
    print(f"Generating {framework} tests ...")
    chat = tester.initiate_chat(tester, message=f"Write {framework} tests for this {language} code:\n{implementation}", max_turns=1)
    tests = chat.chat_history[-1]["content"]

    # Step 5: Assemble
    print("Assembling final output ...")
    final = f"### Implementation\n\n{implementation}\n\n### Unit Tests\n\n{tests}"
    _write(f"{log_dir}/final.md", final)
    print("Committed | status=complete")


@click.command()
@click.option("--spec", required=True, help="Spec text or file path")
@click.option("--language", default="Python", help="Programming language")
@click.option("--framework", default="pytest", help="Test framework")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/30_code_gen/logs-autogen", help="Log directory")
def main(spec, language, framework, model, log_dir):
    """Code Generator + Tests — AutoGen edition"""
    run(spec, language, framework, model, log_dir)

if __name__ == "__main__":
    main()
