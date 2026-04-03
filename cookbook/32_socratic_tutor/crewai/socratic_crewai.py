"""
CrewAI equivalent of socratic_tutor.spl

Pattern: Task sequence with manual orchestration for loops/conditions.

Usage:
    pip install crewai langchain-ollama
    python cookbook/32_socratic_tutor/crewai/socratic_crewai.py \\
        --topic_id "recursion" --subject "programming"
"""

import click
import os
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task

# Add parent to path to import tools
sys.path.append(str(Path(__file__).parent.parent))
try:
    from tools import load_topic, get_level_guidance, compile_dialogue
except ImportError:
    def load_topic(tid, s): return f"Topic Context for {tid}"
    def get_level_guidance(l): return f"Guidance for {l}"
    def compile_dialogue(*args): return "Compiled Dialogue"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(topic: str, topic_id: str, subject: str, student_level: str, model: str, log_dir: str):
    llm = f"ollama/{model}"

    tutor = Agent(
        role="Socratic Tutor",
        goal=f"Guide a {student_level} student to discover answers themselves.",
        backstory="You never give direct answers. You only ask questions.",
        llm=llm,
        verbose=False,
    )
    student = Agent(
        role="Student",
        goal=f"Learn about {topic or topic_id} as a {student_level} student.",
        backstory=f"You are a curious student at the {student_level} level.",
        llm=llm,
        verbose=False,
    )
    judge = Agent(
        role="Professor",
        goal="Assess student understanding accurately.",
        backstory="You evaluate learning progress based on student responses.",
        llm=llm,
        verbose=False,
    )

    context = load_topic(topic_id, subject)
    guide = get_level_guidance(student_level)

    # Turn 1
    print("Step 1: Opening question ...")
    t1 = Task(description=f"Generate opening Socratic question for {topic or topic_id}. Context: {context}\nGuide: {guide}", expected_output="A single question.", agent=tutor)
    q1 = str(Crew(agents=[tutor], tasks=[t1], verbose=False).kickoff())

    print("Step 2: Student response 1 ...")
    t2 = Task(description=f"Answer this Socratic question as a {student_level} student: {q1}", expected_output="A student response.", agent=student)
    s1 = str(Crew(agents=[student], tasks=[t2], verbose=False).kickoff())

    # Turn 2
    print("Step 3: Follow-up question ...")
    t3 = Task(description=f"Previous Q: {q1}\nStudent A: {s1}\nGenerate follow-up question.", expected_output="A follow-up question.", agent=tutor)
    q2 = str(Crew(agents=[tutor], tasks=[t3], verbose=False).kickoff())

    print("Step 4: Student response 2 ...")
    t4 = Task(description=f"Answer this follow-up question as a {student_level} student: {q2}", expected_output="A second student response.", agent=student)
    s2 = str(Crew(agents=[student], tasks=[t4], verbose=False).kickoff())

    # Assess
    print("Step 5: Assessing understanding ...")
    t5 = Task(description=f"Rate understanding (0-10) based on these responses for '{topic or topic_id}':\n1: {s1}\n2: {s2}\nReply with ONLY the number.", expected_output="A single number 0-10.", agent=judge)
    score_str = str(Crew(agents=[judge], tasks=[t5], verbose=False).kickoff())
    try:
        score = float(score_str.strip())
    except:
        score = 5.0
    print(f"Score: {score}")

    # Turn 3
    print("Step 6: Final turn ...")
    if score > 7:
        desc = f"Consolidate understanding based on: {s2}"
    else:
        desc = f"Provide a hint question based on: {s2}"
    
    t6 = Task(description=desc, expected_output="A final question.", agent=tutor)
    q3 = str(Crew(agents=[tutor], tasks=[t6], verbose=False).kickoff())

    t7 = Task(description=f"Answer this final question as a {student_level} student: {q3}", expected_output="A final student response.", agent=student)
    s3 = str(Crew(agents=[student], tasks=[t7], verbose=False).kickoff())

    # Compile
    print("Step 7: Compiling dialogue ...")
    dialogue = compile_dialogue(q1, s1, q2, s2, q3, s3, topic or topic_id, str(score))
    _write(f"{log_dir}/dialogue.md", dialogue)
    print("Committed | status=complete")


@click.command()
@click.option("--topic", default="", help="Freeform topic")
@click.option("--topic_id", default="recursion", help="Topic ID from catalog")
@click.option("--subject", default="programming", help="Subject")
@click.option("--student_level", default="high school", help="Student level")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/32_socratic_tutor/logs-crewai", help="Log directory")
def main(topic, topic_id, subject, student_level, model, log_dir):
    """Socratic Tutor — CrewAI edition"""
    run(topic, topic_id, subject, student_level, model, log_dir)

if __name__ == "__main__":
    main()
