"""
LangGraph equivalent of socratic_tutor.spl

Pattern: load_topic → opening → student_1 → follow_up → student_2 → assess → adapt_3 → student_3 → compile

Usage:
    pip install langgraph langchain-ollama
    python cookbook/32_socratic_tutor/langgraph/socratic_langgraph.py \\
        --topic_id "recursion" --subject "programming"
"""

import click
import os
import sys
from pathlib import Path
from typing import TypedDict, List

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

# Add parent to path to import tools
sys.path.append(str(Path(__file__).parent.parent))
try:
    from tools import load_topic, get_level_guidance, compile_dialogue
except ImportError:
    # Minimal fallbacks if tools.py not easily importable
    def load_topic(tid, s): return f"Topic Context for {tid}"
    def get_level_guidance(l): return f"Guidance for {l}"
    def compile_dialogue(*args): return "Compiled Dialogue"


# ── State ─────────────────────────────────────────────────────────────────────

class SocraticState(TypedDict):
    topic:         str
    topic_id:      str
    subject:       str
    student_level: str
    model:         str
    log_dir:       str
    
    topic_context: str
    level_guide:   str
    
    q1: str
    s1: str
    q2: str
    s2: str
    q3: str
    s3: str
    
    score: float
    dialogue: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def socratic_persona(level: str) -> str:
    return f"""\
You are a Socratic tutor. Your role is to guide the student to discover answers themselves.
Core rules: ONE clear question at a time. NEVER state facts. Build on student words.
Student level: {level}
"""


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_init(state: SocraticState) -> dict:
    print("Step 1: Loading topic and guidance ...")
    context = load_topic(state["topic_id"], state["subject"])
    guide = get_level_guidance(state["student_level"])
    return {"topic_context": context, "level_guide": guide}

def node_opening(state: SocraticState) -> dict:
    print("Step 2: Opening question ...")
    prompt = f"{socratic_persona(state['student_level'])}\n\nContext: {state['topic_context']}\nGuide: {state['level_guide']}\n\nTopic: {state['topic']}\n\nGenerate an opening Socratic question."
    q1 = _invoke(state["model"], prompt)
    return {"q1": q1}

def node_student_1(state: SocraticState) -> dict:
    print("Step 3: Simulating student response 1 ...")
    prompt = f"You are a student at the {state['student_level']} level. Answer this Socratic question about {state['topic'] or state['topic_id']}:\n\nQuestion: {state['q1']}"
    s1 = _invoke(state["model"], prompt)
    return {"s1": s1}

def node_followup(state: SocraticState) -> dict:
    print("Step 4: Follow-up question ...")
    prompt = f"{socratic_persona(state['student_level'])}\n\nContext: {state['topic_context']}\n\nQuestion 1: {state['q1']}\nStudent 1: {state['s1']}\n\nGenerate a follow-up question."
    q2 = _invoke(state["model"], prompt)
    return {"q2": q2}

def node_student_2(state: SocraticState) -> dict:
    print("Step 5: Simulating student response 2 ...")
    prompt = f"You are a student at the {state['student_level']} level. Answer this follow-up question about {state['topic'] or state['topic_id']}:\n\nPrevious Q: {state['q1']}\nYour previous A: {state['s1']}\n\nNew Question: {state['q2']}"
    s2 = _invoke(state["model"], prompt)
    return {"s2": s2}

def node_assess(state: SocraticState) -> dict:
    print("Step 6: Assessing understanding ...")
    prompt = f"Rate the student's understanding (0-10) based on their responses for the topic '{state['topic'] or state['topic_id']}'.\nResponse 1: {state['s1']}\nResponse 2: {state['s2']}\nReply with ONLY the number."
    score_str = _invoke(state["model"], prompt)
    try:
        score = float(score_str.strip())
    except:
        score = 5.0
    print(f"Score: {score}")
    return {"score": score}

def node_adapt_3(state: SocraticState) -> dict:
    print("Step 7: Adapting third question ...")
    if state["score"] > 7:
        print("  High score - Consolidation")
        prompt = f"{socratic_persona(state['student_level'])}\n\nConsolidate understanding for {state['topic'] or state['topic_id']} based on:\n{state['s2']}"
    else:
        print("  Low score - Hinting")
        prompt = f"{socratic_persona(state['student_level'])}\n\nProvide a hint question for {state['topic'] or state['topic_id']} to help the student who is stuck:\n{state['s2']}"
    q3 = _invoke(state["model"], prompt)
    return {"q3": q3}

def node_student_3(state: SocraticState) -> dict:
    print("Step 8: Final student response ...")
    prompt = f"You are a student at the {state['student_level']} level. Answer this final question about {state['topic'] or state['topic_id']}:\n\nQuestion: {state['q3']}"
    s3 = _invoke(state["model"], prompt)
    return {"s3": s3}

def node_compile(state: SocraticState) -> dict:
    print("Step 9: Compiling dialogue ...")
    dialogue = compile_dialogue(
        state["q1"], state["s1"],
        state["q2"], state["s2"],
        state["q3"], state["s3"],
        state["topic"] or state["topic_id"],
        str(state["score"])
    )
    _write(f"{state['log_dir']}/dialogue.md", dialogue)
    return {"dialogue": dialogue}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(SocraticState)
    g.add_node("init",      node_init)
    g.add_node("opening",   node_opening)
    g.add_node("student_1", node_student_1)
    g.add_node("followup",  node_followup)
    g.add_node("student_2", node_student_2)
    g.add_node("assess",    node_assess)
    g.add_node("adapt_3",   node_adapt_3)
    g.add_node("student_3", node_student_3)
    g.add_node("compile",   node_compile)

    g.set_entry_point("init")
    g.add_edge("init",      "opening")
    g.add_edge("opening",   "student_1")
    g.add_edge("student_1", "followup")
    g.add_edge("followup",  "student_2")
    g.add_edge("student_2", "assess")
    g.add_edge("assess",    "adapt_3")
    g.add_edge("adapt_3",   "student_3")
    g.add_edge("student_3", "compile")
    g.add_edge("compile",   END)
    return g.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--topic", default="", help="Freeform topic")
@click.option("--topic_id", default="recursion", help="Topic ID from catalog")
@click.option("--subject", default="programming", help="Subject")
@click.option("--student_level", default="high school", help="Student level")
@click.option("--model", default="gemma3", help="LLM model name")
@click.option("--log-dir", default="cookbook/32_socratic_tutor/logs-langgraph", help="Log directory")
def main(topic, topic_id, subject, student_level, model, log_dir):
    """Socratic Tutor — LangGraph edition"""
    build_graph().invoke({
        "topic":         topic,
        "topic_id":      topic_id,
        "subject":       subject,
        "student_level": student_level,
        "model":         model,
        "log_dir":       log_dir,
        "topic_context": "",
        "level_guide":   "",
        "q1": "", "s1": "", "q2": "", "s2": "", "q3": "", "s3": "",
        "score": 0.0,
        "dialogue": "",
    })

if __name__ == "__main__":
    main()
