"""
AutoGen equivalent of chain.spl

Three ConversableAgents (Researcher, Analyst, Summarizer) driven sequentially
by a proxy — each invoked once via initiate_chat(max_turns=1).
No conversation loop needed: this is a pure sequential pipeline.

Usage:
    pip install pyautogen
    python cookbook/09_chain_of_thought/autogen/chain_autogen.py \\
        --topic "distributed AI inference"
    python cookbook/09_chain_of_thought/autogen/chain_autogen.py \\
        --topic "quantum computing" --model llama3.2
"""

import click
from pathlib import Path

from autogen import ConversableAgent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _make_agent(name: str, system_msg: str, llm_config: dict) -> ConversableAgent:
    return ConversableAgent(
        name=name,
        system_message=system_msg,
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
    )


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, model: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # Proxy drives each agent — it never calls an LLM itself
    proxy = ConversableAgent("proxy", llm_config=False, human_input_mode="NEVER")

    # SPL: three separate GENERATE calls, each scoped to one agent's expertise
    researcher = _make_agent(
        "Researcher",
        "You are a research expert. When given a topic, provide key facts, "
        "current state, and important context. Be thorough and factual.",
        llm_config,
    )
    analyst = _make_agent(
        "Analyst",
        "You are an analytical expert. When given research findings, identify "
        "patterns, implications, and key insights.",
        llm_config,
    )
    summarizer = _make_agent(
        "Summarizer",
        "You are an expert summarizer. Write a concise 2-3 paragraph executive "
        "summary of the given analysis. Be clear and direct.",
        llm_config,
    )

    # GENERATE research(@topic) INTO @research
    print("Step 1 | researching ...")
    r1 = proxy.initiate_chat(
        researcher,
        message=f"Research this topic thoroughly: {topic}",
        max_turns=1,
    )
    research = r1.chat_history[-1]["content"]
    _write(f"{log_dir}/research.md", research)

    # GENERATE analyze(@research) INTO @analysis
    print("Step 2 | analyzing ...")
    r2 = proxy.initiate_chat(
        analyst,
        message=f"Analyze these research findings:\n\n{research}",
        max_turns=1,
    )
    analysis = r2.chat_history[-1]["content"]
    _write(f"{log_dir}/analysis.md", analysis)

    # GENERATE summarize(@analysis) INTO @summary
    print("Step 3 | summarizing ...")
    r3 = proxy.initiate_chat(
        summarizer,
        message=f"Summarize this analysis:\n\n{analysis}",
        max_turns=1,
    )
    summary = r3.chat_history[-1]["content"]
    _write(f"{log_dir}/summary.md", summary)

    # COMMIT @summary WITH status = 'complete'
    _write(f"{log_dir}/final.md", summary)
    print("Done | status=complete")
    return summary


# ── Entry point  (SPL: built into CLI — `spl run ...`) ────────────────────────

@click.command()
@click.option("--topic",   required=True,    help="Topic to analyze")
@click.option("--model",   default="gemma3", show_default=True)
@click.option("--log-dir", default="cookbook/09_chain_of_thought/autogen/logs", show_default=True)
def main(topic: str, model: str, log_dir: str):
    result = run(topic, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
