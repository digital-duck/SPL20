"""
AutoGen equivalent of reflection.spl

Pattern: solve → reflect → score → (confident? commit : correct → loop)

Usage:
    pip install pyautogen
    python cookbook/16_reflection/autogen/reflection_autogen.py \\
        --problem "What are the trade-offs of microservices vs monoliths?"
"""

import click
from pathlib import Path

from autogen import ConversableAgent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(problem: str, max_refs: int, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    solver    = ConversableAgent("Solver",    system_message="Solve technical problems.", llm_config=llm_config, human_input_mode="NEVER")
    reflector = ConversableAgent("Reflector", system_message="Reflect on your own reasoning to catch errors.", llm_config=llm_config, human_input_mode="NEVER")
    judge     = ConversableAgent("Judge",     system_message="Rate confidence scores.", llm_config=llm_config, human_input_mode="NEVER")

    # Initial solve
    print("Initial solution ...")
    chat = solver.initiate_chat(solver, message=f"Solve this problem: {problem}", max_turns=1)
    answer = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/answer_0.md", answer)

    iteration = 0
    while iteration < max_refs:
        print(f"Reflection iteration {iteration} ...")
        # Reflect
        chat = reflector.initiate_chat(reflector, message=f"Reflect on this answer for '{problem}':\n{answer}", max_turns=1)
        reflection = chat.chat_history[-1]["content"]
        _write(f"{log_dir}/reflection_{iteration}.md", reflection)

        # Score
        chat = judge.initiate_chat(judge, message=f"Rate confidence (0.0-1.0) in the answer based on reflection.\nAnswer: {answer}\nReflection: {reflection}\nReply with ONLY the number.", max_turns=1)
        try:
            confidence = float(chat.chat_history[-1]["content"].strip())
        except:
            confidence = 0.5
        print(f"Confidence: {confidence}")

        if confidence > 0.85:
            print(f"Confident at iteration {iteration}")
            break

        # Correct
        print("Correcting answer ...")
        chat = solver.initiate_chat(solver, message=f"Correct this answer for '{problem}' based on reflection:\n{reflection}\nOriginal Answer:\n{answer}", max_turns=1)
        answer = chat.chat_history[-1]["content"]
        iteration += 1
        _write(f"{log_dir}/answer_{iteration}.md", answer)

    _write(f"{log_dir}/final.md", answer)
    print("Committed | status=complete")


@click.command()
@click.option("--problem", required=True, help="Problem to solve")
@click.option("--max-reflections", default=3, help="Max reflection cycles")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/16_reflection/logs-autogen", help="Log directory")
def main(problem, max_reflections, model, log_dir):
    """Reflection Agent — AutoGen edition"""
    run(problem, max_reflections, model, log_dir)

if __name__ == "__main__":
    main()
