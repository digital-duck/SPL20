"""
CrewAI equivalent of guardrails.spl

Three Agents (Auditor, Assistant, Validator) collaborate on a multi-gate
safety pipeline managed by a Python-orchestrated workflow.

Usage:
    pip install crewai langchain-ollama
    python cookbook/18_guardrails/crewai/guardrails_crewai.py \
        --user-input "My SSN is 123-45-6789, help me file taxes"
"""

import argparse
import re
from pathlib import Path

from crewai import Agent, Crew, Process, Task


# ── Deterministic Tool Logic ──────────────────────────────────────────────────

SSN_RE = re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b")
CC_RE = re.compile(r"\b(?:\d{4}[-\s]){3}\d{4}\b|\b\d{16}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4}\b")

HARMFUL_KEYWORDS = ["keylogger", "malware", "ransomware", "phishing", "bomb", "explosive", "poison"]
OFF_TOPIC_KEYWORDS = ["buy stock", "invest in", "trading advice", "diagnose me", "legal advice"]

def classify_keywords(text: str) -> str:
    lower = text.lower()
    for kw in HARMFUL_KEYWORDS:
        if kw in lower: return f"harmful:{kw}"
    for kw in OFF_TOPIC_KEYWORDS:
        if kw in lower: return f"off_topic:{kw}"
    return "safe"

def redact_pii_logic(text: str) -> str:
    text = SSN_RE.sub("[REDACTED-SSN]", text)
    text = CC_RE.sub("[REDACTED-CC]", text)
    text = EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED-PHONE]", text)
    return text


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()


# ── Main runner ───────────────────────────────────────────────────────────────

def run(user_input: str, model: str, log_dir: str) -> str:
    llm = f"ollama/{model}"

    # Agents
    auditor = Agent(
        role="Safety Auditor",
        goal="Identify harmful or off-topic inputs based on safety guidelines.",
        backstory="You are a strict safety auditor who ensures all user requests are safe and on-topic.",
        llm=llm,
        verbose=False,
    )
    assistant = Agent(
        role="Helpful Assistant",
        goal="Provide helpful and accurate responses to safe user requests.",
        backstory="You are a helpful assistant who provides clear and safe information.",
        llm=llm,
        verbose=False,
    )
    validator = Agent(
        role="Output Validator",
        goal="Review assistant outputs for safety violations or PII leakage.",
        backstory="You ensure that all outgoing information is safe and free of personal data.",
        llm=llm,
        verbose=False,
    )

    # Gate 1a: Keyword pre-screen
    print("Gate 1a: Keyword pre-screen ...")
    kw_class = classify_keywords(user_input)
    if kw_class.startswith("harmful"): return "I cannot help with that request. (Blocked by Keyword)"
    if kw_class.startswith("off_topic"): return "That question is outside my scope. (Blocked by Keyword)"

    # Gate 1b: LLM classification
    print("Gate 1b: LLM input classification ...")
    input_class = _run_task(
        auditor,
        description=f"Classify this user input as 'harmful', 'off_topic', or 'safe':\n\n{user_input}",
        expected_output="Exactly one word: 'harmful', 'off_topic', or 'safe'."
    ).lower()
    
    if "harmful" in input_class: return "I cannot help with that request. (Blocked by Auditor)"
    if "off_topic" in input_class: return "That question is outside my scope. (Blocked by Auditor)"

    # Gate 2: PII redaction
    print("Gate 2: PII redaction ...")
    clean_input = redact_pii_logic(user_input)

    # Gate 3: Safe generation
    print("Gate 3: Safe generation ...")
    raw_response = _run_task(
        assistant,
        description=f"Provide a helpful response to this request: {clean_input}",
        expected_output="A helpful and safe response."
    )

    # Gate 4: Output validation
    print("Gate 4: Output validation ...")
    val_class = _run_task(
        validator,
        description=f"Review this response for safety: {raw_response}\nReply 'safe', 'contains_pii', or 'harmful'.",
        expected_output="Exactly one word: 'safe', 'contains_pii', or 'harmful'."
    ).lower()

    if "safe" in val_class:
        return raw_response
    elif "pii" in val_class:
        return redact_pii_logic(raw_response)
    else:
        return "I was unable to generate a safe response."


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Guardrails Pipeline — CrewAI edition")
    p.add_argument("--user-input", required=True)
    p.add_argument("--model",      default="gemma3")
    p.add_argument("--log-dir",    default="cookbook/18_guardrails/crewai/logs-crewai")
    args = p.parse_args()

    result = run(args.user_input, args.model, args.log_dir)
    print("\n" + "=" * 60)
    print(f"RESPONSE:\n{result}")

if __name__ == "__main__":
    main()
