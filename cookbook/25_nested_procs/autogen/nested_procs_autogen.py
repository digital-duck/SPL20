"""
AutoGen equivalent of nested_procs.spl

Pattern: Sequential orchestration of specialized prompts.

Usage:
    pip install pyautogen
    python cookbook/25_nested_procs/autogen/nested_procs_autogen.py \\
        --topic "quantum computing" --audience "high school students"
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

def run(topic: str, audience: str, depth: str, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    agent = ConversableAgent("Explainer", system_message="You are an expert educator.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Research
    print("Step 1: Research overview ...")
    chat = agent.initiate_chat(agent, message=f"Provide a research overview for: {topic}", max_turns=1)
    overview = chat.chat_history[-1]["content"]

    # Step 2: Explain
    print("Step 2: Explaining layer ...")
    chat = agent.initiate_chat(agent, message=f"Explain this for {audience} in a clear style:\n{overview}", max_turns=1)
    base_exp = chat.chat_history[-1]["content"]

    # Step 3: Example
    print("Step 3: Creating example ...")
    chat = agent.initiate_chat(agent, message=f"Create a concrete example for {topic} for {audience} given this context:\n{base_exp}", max_turns=1)
    example = chat.chat_history[-1]["content"]

    # Step 4: Calibrate
    print("Step 4: Calibrating complexity ...")
    chat = agent.initiate_chat(agent, message=f"Simplify this text for {audience} if it is too complex:\n{base_exp}", max_turns=1)
    calibrated = chat.chat_history[-1]["content"]

    # Step 5: Assemble
    print("Step 5: Assembling article ...")
    chat = agent.initiate_chat(agent, message=f"Assemble a final {depth} depth article on {topic} for {audience} using:\nExplanation: {calibrated}\nExample: {example}", max_turns=1)
    article = chat.chat_history[-1]["content"]

    _write(f"{log_dir}/final.md", article)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic to explain")
@click.option("--audience", required=True, help="Target audience")
@click.option("--depth", default="standard", help="Article depth")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/25_nested_procs/logs-autogen", help="Log directory")
def main(topic, audience, depth, model, log_dir):
    """Nested Procedures — AutoGen edition"""
    run(topic, audience, depth, model, log_dir)

if __name__ == "__main__":
    main()
