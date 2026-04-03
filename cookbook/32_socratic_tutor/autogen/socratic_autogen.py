"""
AutoGen equivalent of socratic_tutor.spl

Pattern: Sequential orchestration of specialized prompts.

Usage:
    pip install pyautogen
    python cookbook/32_socratic_tutor/autogen/socratic_autogen.py \\
        --topic_id "recursion" --subject "programming"
"""

import click
import os
import sys
from pathlib import Path

from autogen import ConversableAgent

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
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    tutor = ConversableAgent("Tutor", system_message=f"You are a Socratic tutor for a {student_level} student. Guide them to the answer.", llm_config=llm_config, human_input_mode="NEVER")
    student = ConversableAgent("Student", system_message=f"You are a student at the {student_level} level.", llm_config=llm_config, human_input_mode="NEVER")
    judge = ConversableAgent("Judge", system_message="Rate student understanding (0-10).", llm_config=llm_config, human_input_mode="NEVER")

    context = load_topic(topic_id, subject)
    guide = get_level_guidance(student_level)

    # Turn 1
    print("Step 1: Opening question ...")
    chat = tutor.initiate_chat(tutor, message=f"Context: {context}\nGuide: {guide}\nTopic: {topic}\nGenerate opening Socratic question.", max_turns=1)
    q1 = chat.chat_history[-1]["content"]

    print("Step 2: Student response 1 ...")
    chat = student.initiate_chat(student, message=f"Question: {q1}\nAnswer as a {student_level} student.", max_turns=1)
    s1 = chat.chat_history[-1]["content"]

    # Turn 2
    print("Step 3: Follow-up question ...")
    chat = tutor.initiate_chat(tutor, message=f"Previous Q: {q1}\nStudent A: {s1}\nGenerate follow-up Socratic question.", max_turns=1)
    q2 = chat.chat_history[-1]["content"]

    print("Step 4: Student response 2 ...")
    chat = student.initiate_chat(student, message=f"New Question: {q2}\nAnswer as a {student_level} student.", max_turns=1)
    s2 = chat.chat_history[-1]["content"]

    # Assess
    print("Step 5: Assessing understanding ...")
    chat = judge.initiate_chat(judge, message=f"Response 1: {s1}\nResponse 2: {s2}\nRate understanding (0-10). Score only.", max_turns=1)
    try:
        score = float(chat.chat_history[-1]["content"].strip())
    except:
        score = 5.0
    print(f"Score: {score}")

    # Turn 3 (Adaptive)
    print("Step 6: Final turn ...")
    if score > 7:
        prompt = f"Consolidate understanding based on: {s2}"
    else:
        prompt = f"Provide a hint question based on: {s2}"
    
    chat = tutor.initiate_chat(tutor, message=prompt, max_turns=1)
    q3 = chat.chat_history[-1]["content"]

    chat = student.initiate_chat(student, message=f"Final Question: {q3}\nAnswer as a {student_level} student.", max_turns=1)
    s3 = chat.chat_history[-1]["content"]

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
@click.option("--log-dir", default="cookbook/32_socratic_tutor/logs-autogen", help="Log directory")
def main(topic, topic_id, subject, student_level, model, log_dir):
    """Socratic Tutor — AutoGen edition"""
    run(topic, topic_id, subject, student_level, model, log_dir)

if __name__ == "__main__":
    main()
