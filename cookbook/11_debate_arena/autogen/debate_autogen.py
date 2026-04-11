"""
AutoGen equivalent of debate.spl

Three Agents — Pro, Con, and Judge.
Pro and Con converse for N rounds, then Judge evaluates the whole history.

Usage:
    pip install pyautogen
    python cookbook/11_debate_arena/autogen/debate_autogen.py --topic "AI should be open-sourced"
"""

import click
from pathlib import Path

from autogen import ConversableAgent


# ── Agent system messages (mirrors PROMPT blocks in debate.spl) ─────────────

PRO_SYSTEM = """\
You are a skilled debate champion arguing STRONGLY IN FAVOR of the motion.
Motion: "{topic}"

Write a focused, persuasive argument supporting the motion.
Directly address and counter your opponent's points.
Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""

CON_SYSTEM = """\
You are a skilled debate champion arguing STRONGLY AGAINST the motion.
Motion: "{topic}"

Write a focused, persuasive argument opposing the motion.
Directly address and counter your opponent's points.
Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""

JUDGE_SYSTEM = """\
You are an impartial debate judge evaluating the following debate.

Evaluate the debate on these criteria:
1. Strength of arguments
2. Quality of rebuttals
3. Clarity and persuasiveness

Declare a winner (PRO or CON) and explain your reasoning in 2-3 paragraphs.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, max_rounds: int, model: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # SPL: CREATE FUNCTION pro_argument(...)
    pro_agent = ConversableAgent(
        name="Pro",
        system_message=PRO_SYSTEM.format(topic=topic),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    # SPL: CREATE FUNCTION con_argument(...)
    con_agent = ConversableAgent(
        name="Con",
        system_message=CON_SYSTEM.format(topic=topic),
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    # SPL: CREATE FUNCTION judge_debate(...)
    judge_agent = ConversableAgent(
        name="Judge",
        system_message=JUDGE_SYSTEM,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    # Initiate chat — Pro starts
    # max_turns = 1 (opening) + N (rebuttals)
    # Actually, in SPL: 
    # Opening: Pro, then Con.
    # Rounds: (Pro rebuttal, Con rebuttal) x N.
    # Total turns: 2 + 2 * N.
    
    chat_history = pro_agent.initiate_chat(
        con_agent,
        message=f"Debate motion: {topic}. Please start with your opening statement.",
        max_turns=2 + 2 * max_rounds,
    )

    # Log individual messages
    # turns: 0: Pro, 1: Con, 2: Pro, 3: Con ...
    for i, msg in enumerate(chat_history.chat_history):
        name    = msg.get("name", "")
        content = msg.get("content", "")
        if i < 2:
            _write(f"{log_dir}/opening_{name.lower()}.md", content)
        else:
            round_idx = (i - 2) // 2
            _write(f"{log_dir}/round_{round_idx}_{name.lower()}.md", content)

    # Judge evaluates
    # Build a full history string for the judge
    full_history = f"Motion: {topic}\n\n"
    for msg in chat_history.chat_history:
        full_history += f"--- {msg['name']} ---\n{msg['content']}\n\n"

    print("Judge deliberating ...")
    judge_result = judge_agent.generate_reply(
        messages=[{"content": full_history, "role": "user"}]
    )
    
    verdict = str(judge_result)
    _write(f"{log_dir}/verdict.md", verdict)
    return verdict


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic",      required=True,    help="Debate topic")
@click.option("--max-rounds", default=3,        show_default=True, type=int)
@click.option("--model",      default="gemma3", show_default=True)
@click.option("--log-dir",    default="cookbook/11_debate_arena/autogen/logs-autogen", show_default=True)
def main(topic: str, max_rounds: int, model: str, log_dir: str):
    result = run(topic, max_rounds, model, log_dir)
    print("\n" + "=" * 60)
    print("VERDICT:")
    print(result)

if __name__ == "__main__":
    main()
