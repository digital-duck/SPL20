"""
AutoGen equivalent of bedrock_quickstart.spl

Pattern: Fan-out prompt to multiple agents.

Usage:
    pip install pyautogen
    python cookbook/38_bedrock_quickstart/autogen/bedrock_autogen.py \\
        --prompt "Explain the CAP theorem in two sentences."
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

def run(prompt: str, m1: str, m2: str, m3: str, judge_m: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    "gemma3", # Simulating with local model
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    agent_1 = ConversableAgent("Model_1", system_message=f"You are {m1}.", llm_config=llm_config, human_input_mode="NEVER")
    agent_2 = ConversableAgent("Model_2", system_message=f"You are {m2}.", llm_config=llm_config, human_input_mode="NEVER")
    agent_3 = ConversableAgent("Model_3", system_message=f"You are {m3}.", llm_config=llm_config, human_input_mode="NEVER")
    judge   = ConversableAgent("Judge",   system_message="You are a neutral evaluator.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Fan-out
    print(f"Asking {m1} ...")
    chat = agent_1.initiate_chat(agent_1, message=prompt, max_turns=1)
    ans_1 = chat.chat_history[-1]["content"]

    print(f"Asking {m2} ...")
    chat = agent_2.initiate_chat(agent_2, message=prompt, max_turns=1)
    ans_2 = chat.chat_history[-1]["content"]

    print(f"Asking {m3} ...")
    chat = agent_3.initiate_chat(agent_3, message=prompt, max_turns=1)
    ans_3 = chat.chat_history[-1]["content"]

    # Step 2: Synthesis
    print("Synthesizing comparison ...")
    comp_prompt = f"""\
Compare these responses for the prompt: "{prompt}"

=== {m1} ===
{ans_1}

=== {m2} ===
{ans_2}

=== {m3} ===
{ans_3}

Evaluation: Accuracy, Conciseness, Recommendation."""
    
    chat = judge.initiate_chat(judge, message=comp_prompt, max_turns=1)
    comparison = chat.chat_history[-1]["content"]

    _write(f"{log_dir}/comparison.md", comparison)
    print("Committed | status=complete")


@click.command()
@click.option("--prompt", default="Explain the CAP theorem in two sentences.")
@click.option("--model_1", default="anthropic.claude-sonnet-4")
@click.option("--model_2", default="anthropic.claude-haiku-4-5")
@click.option("--model_3", default="amazon.nova-pro")
@click.option("--judge_model", default="gemma3")
@click.option("--log-dir", default="cookbook/38_bedrock_quickstart/logs-autogen")
def main(prompt, model_1, model_2, model_3, judge_model, log_dir):
    """Bedrock Quickstart — AutoGen edition"""
    run(prompt, model_1, model_2, model_3, judge_model, log_dir)

if __name__ == "__main__":
    main()
