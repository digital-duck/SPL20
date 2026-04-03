"""
AutoGen equivalent of multi_agent.spl

Pattern: Researcher → Analyst → Writer (Sequential chat)

Usage:
    pip install pyautogen
    python cookbook/14_multi_agent/autogen/multi_agent_autogen.py \\
        --topic "Impact of AI on healthcare"
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

def run(topic: str, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    researcher = ConversableAgent("Researcher", system_message="You gather key facts and sources.", llm_config=llm_config, human_input_mode="NEVER")
    analyst    = ConversableAgent("Analyst",    system_message="You identify trends, risks, and opportunities.", llm_config=llm_config, human_input_mode="NEVER")
    writer     = ConversableAgent("Writer",     system_message="You produce a polished final report.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Research
    print("Agent 1: Researcher ...")
    chat = researcher.initiate_chat(researcher, message=f"Gather research for: {topic}", max_turns=1)
    research = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/research.md", research)

    # Step 2: Analysis
    print("Agent 2: Analyst ...")
    chat = analyst.initiate_chat(analyst, message=f"Analyze this research:\n{research}", max_turns=1)
    analysis = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/analysis.md", analysis)

    # Step 3: Writer
    print("Agent 3: Writer ...")
    chat = writer.initiate_chat(writer, message=f"Write a report on {topic} based on:\nResearch:\n{research}\nAnalysis:\n{analysis}", max_turns=1)
    report = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/report.md", report)

    _write(f"{log_dir}/final.md", report)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic for the report")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/14_multi_agent/logs-autogen", help="Log directory")
def main(topic, model, log_dir):
    """Multi-Agent Collaboration — AutoGen edition"""
    run(topic, model, log_dir)

if __name__ == "__main__":
    main()
