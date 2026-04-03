"""
CrewAI equivalent of bedrock_quickstart.spl

Pattern: Multiple tasks executed by different agents (simulated).

Usage:
    pip install crewai langchain-aws
    python cookbook/38_bedrock_quickstart/crewai/bedrock_crewai.py \\
        --prompt "Explain the CAP theorem in two sentences."
"""

import click
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(prompt: str, m1: str, m2: str, m3: str, judge_m: str, log_dir: str):
    llm = "ollama/gemma3" # Simulating Bedrock with local Ollama

    agent_1 = Agent(role=f"Model 1 ({m1})", goal="Provide a high-quality response.", backstory="Expert AI model.", llm=llm, verbose=False)
    agent_2 = Agent(role=f"Model 2 ({m2})", goal="Provide a high-quality response.", backstory="Fast AI model.", llm=llm, verbose=False)
    agent_3 = Agent(role=f"Model 3 ({m3})", goal="Provide a high-quality response.", backstory="Advanced AI model.", llm=llm, verbose=False)
    judge   = Agent(role="Judge", goal="Evaluate AI model responses neutrally.", backstory="Senior AI researcher.", llm=llm, verbose=False)

    # Step 1: Tasks
    t1 = Task(description=prompt, expected_output="A response.", agent=agent_1)
    t2 = Task(description=prompt, expected_output="A response.", agent=agent_2)
    t3 = Task(description=prompt, expected_output="A response.", agent=agent_3)

    print("Executing fan-out tasks ...")
    crew = Crew(agents=[agent_1, agent_2, agent_3], tasks=[t1, t2, t3], process=Process.sequential, verbose=False)
    crew.kickoff()

    # Step 2: Comparison Task
    ans_1, ans_2, ans_3 = t1.output.raw, t2.output.raw, t3.output.raw
    comp_desc = f"""\
Compare these responses for the prompt: "{prompt}"

=== {m1} ===
{ans_1}

=== {m2} ===
{ans_2}

=== {m3} ===
{ans_3}

Evaluation: Accuracy, Conciseness, Recommendation."""

    t_comp = Task(description=comp_desc, expected_output="A comparison report.", agent=judge)
    print("Synthesizing comparison ...")
    comparison = str(Crew(agents=[judge], tasks=[t_comp], verbose=False).kickoff())

    _write(f"{log_dir}/comparison.md", comparison)
    print("Committed | status=complete")


@click.command()
@click.option("--prompt", default="Explain the CAP theorem in two sentences.")
@click.option("--model_1", default="anthropic.claude-sonnet-4")
@click.option("--model_2", default="anthropic.claude-haiku-4-5")
@click.option("--model_3", default="amazon.nova-pro")
@click.option("--judge_model", default="gemma3")
@click.option("--log-dir", default="cookbook/38_bedrock_quickstart/logs-crewai")
def main(prompt, model_1, model_2, model_3, judge_model, log_dir):
    """Bedrock Quickstart — CrewAI edition"""
    run(prompt, model_1, model_2, model_3, judge_model, log_dir)

if __name__ == "__main__":
    main()
