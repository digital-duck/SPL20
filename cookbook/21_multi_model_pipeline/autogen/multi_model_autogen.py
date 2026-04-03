"""
AutoGen equivalent of multi_model.spl

Pattern: research → analyze → write → score → (pass? commit : refine → loop)

Usage:
    pip install pyautogen
    python cookbook/21_multi_model_pipeline/autogen/multi_model_autogen.py \\
        --topic "climate change"
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

def run(topic: str, max_iterations: int, model: str, log_dir: str):
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    researcher = ConversableAgent("Researcher", system_message="Gather key facts.", llm_config=llm_config, human_input_mode="NEVER")
    analyst    = ConversableAgent("Analyst",    system_message="Identify insights.", llm_config=llm_config, human_input_mode="NEVER")
    writer     = ConversableAgent("Writer",     system_message="Write engaging summaries.", llm_config=llm_config, human_input_mode="NEVER")
    judge      = ConversableAgent("Judge",      system_message="Rate text quality.", llm_config=llm_config, human_input_mode="NEVER")

    # Step 1: Research
    print("Step 1: Research ...")
    chat = researcher.initiate_chat(researcher, message=f"Gather key facts about: {topic}", max_turns=1)
    facts = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/research.md", facts)

    # Step 2: Analysis
    print("Step 2: Analysis ...")
    chat = analyst.initiate_chat(analyst, message=f"Analyze these facts and find the 3 most significant insights:\n{facts}", max_turns=1)
    analysis = chat.chat_history[-1]["content"]
    _write(f"{log_dir}/analysis.md", analysis)

    # Step 3: Writing loop
    iteration = 0
    while iteration < max_iterations:
        print(f"Step 3: Writing (iteration {iteration}) ...")
        chat = writer.initiate_chat(writer, message=f"Write a clear, engaging 2-paragraph summary based on this analysis:\n{analysis}", max_turns=1)
        draft = chat.chat_history[-1]["content"]
        _write(f"{log_dir}/draft_{iteration}.md", draft)

        # Step 4: Quality check
        print("Step 4: Quality score ...")
        chat = judge.initiate_chat(judge, message=f"Rate the following text on a scale of 0.0 to 1.0 for clarity, accuracy, and completeness.\nText: {draft}\nReply with ONLY the average number.", max_turns=1)
        try:
            score = float(chat.chat_history[-1]["content"].strip())
        except:
            score = 0.5
        print(f"Quality score: {score}")

        if score > 0.7:
            print(f"Quality threshold met at iteration {iteration}")
            break
        
        iteration += 1

    _write(f"{log_dir}/final.md", draft)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", required=True, help="Topic for the pipeline")
@click.option("--max-iterations", default=3, help="Max quality cycles")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/21_multi_model_pipeline/logs-autogen", help="Log directory")
def main(topic, max_iterations, model, log_dir):
    """Multi-Model Pipeline — AutoGen edition"""
    run(topic, max_iterations, model, log_dir)

if __name__ == "__main__":
    main()
