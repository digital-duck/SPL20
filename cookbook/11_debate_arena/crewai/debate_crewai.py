"""
CrewAI equivalent of debate.spl

Three Agents (Pro, Con, Judge) with a manual round-robin loop.
CrewAI tasks are used for each stage of the debate.

Usage:
    pip install crewai langchain-ollama
    python cookbook/11_debate_arena/crewai/debate_crewai.py --topic "AI should be open-sourced"
"""

import click
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, max_rounds: int, model: str, log_dir: str) -> str:
    # Standardize to the 'ollama/' prefix for more robust local model support
    llm = f"ollama/{model}"

    # Agents (mirrors CREATE FUNCTION blocks in debate.spl)
    pro_agent = Agent(
        role="Proponent",
        goal=f"Argue STRONGLY IN FAVOR of the motion: {topic}",
        backstory="You are a skilled debate champion specializing in supporting motions.",
        llm=llm,
        verbose=False,
    )
    con_agent = Agent(
        role="Opponent",
        goal=f"Argue STRONGLY AGAINST the motion: {topic}",
        backstory="You are a skilled debate champion specializing in opposing motions.",
        llm=llm,
        verbose=False,
    )
    judge_agent = Agent(
        role="Impartial Judge",
        goal="Evaluate a debate based on argument strength, rebuttal quality, and clarity.",
        backstory="You are a fair and experienced judge who analyzes both sides impartially.",
        llm=llm,
        verbose=False,
    )

    # Opening Statements
    print("[0] Pro opening ...")
    pro_opening = _run_task(
        pro_agent,
        description=f"Provide an opening statement STRONGLY IN FAVOR of the motion: {topic}",
        expected_output="A persuasive opening statement (3-5 paragraphs).",
    )
    _write(f"{log_dir}/opening_pro.md", pro_opening)

    print("[0] Con opening ...")
    con_opening = _run_task(
        con_agent,
        description=f"Provide an opening statement STRONGLY AGAINST the motion: {topic}.\n"
                    f"Address Pro's opening if necessary:\n\n{pro_opening}",
        expected_output="A persuasive opening statement (3-5 paragraphs).",
    )
    _write(f"{log_dir}/opening_con.md", con_opening)

    pro_history = pro_opening
    con_history = con_opening
    last_con = con_opening

    # Rebuttal rounds
    for r in range(max_rounds):
        print(f"[{r}] Pro rebuttal ...")
        pro_rebuttal = _run_task(
            pro_agent,
            description=f"Rebut the following argument from your opponent:\n\n{last_con}",
            expected_output="A focused rebuttal supporting the motion.",
        )
        pro_history += "\n---\n" + pro_rebuttal
        _write(f"{log_dir}/round_{r}_pro.md", pro_rebuttal)

        print(f"[{r}] Con rebuttal ...")
        con_rebuttal = _run_task(
            con_agent,
            description=f"Rebut the following argument from your opponent:\n\n{pro_rebuttal}",
            expected_output="A focused rebuttal opposing the motion.",
        )
        con_history += "\n---\n" + con_rebuttal
        last_con = con_rebuttal
        _write(f"{log_dir}/round_{r}_con.md", con_rebuttal)

    # Judge evaluation
    print("Judge deliberating ...")
    verdict = _run_task(
        judge_agent,
        description=(
            f"Evaluate the following debate on the motion: {topic}\n\n"
            f"--- PRO SIDE ---\n{pro_history}\n\n"
            f"--- CON SIDE ---\n{con_history}\n\n"
            "Declare a winner (PRO or CON) and explain your reasoning in 2-3 paragraphs."
        ),
        expected_output="A clear verdict and reasoning.",
    )
    _write(f"{log_dir}/verdict.md", verdict)
    return verdict


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic",      required=True,    help="Debate topic")
@click.option("--max-rounds", default=3,        show_default=True, type=int)
@click.option("--model",      default="gemma3", show_default=True)
@click.option("--log-dir",    default="cookbook/11_debate_arena/crewai/logs-crewai", show_default=True)
def main(topic: str, max_rounds: int, model: str, log_dir: str):
    result = run(topic, max_rounds, model, log_dir)
    print("\n" + "=" * 60)
    print("VERDICT:")
    print(result)

if __name__ == "__main__":
    main()
