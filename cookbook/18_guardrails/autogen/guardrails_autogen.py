"""
AutoGen equivalent of guardrails.spl

A procedural script coordinates agents (Classifier, Helper, Validator)
and deterministic filters (Keywords, PII) to implement a safety pipeline.

Usage:
    pip install pyautogen
    python cookbook/18_guardrails/autogen/guardrails_autogen.py \
        --user-input "My SSN is 123-45-6789, help me file taxes"
"""

import click
import re
from pathlib import Path

from autogen import ConversableAgent


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


# ── Agent system messages ─────────────────────────────────────────────────────

CLASSIFIER_SYSTEM = """\
You are a safety classifier. Review input and determine if it is:
1. harmful (illegal acts, violence, malware)
2. off_topic (financial, medical, or legal advice outside scope)
3. safe (everything else)
Reply with exactly one word: harmful, off_topic, or safe."""

HELPER_SYSTEM = """\
You are a helpful and safe assistant. Provide a helpful response.
Do NOT include any PII in your response."""

VALIDATOR_SYSTEM = """\
You are a safety validator. Review output and determine if it:
1. contains_pii (leaks SSNs, emails, phones, CCs)
2. harmful (unsafe content)
3. safe (everything else)
Reply with exactly one word: contains_pii, harmful, or safe."""


# ── Main runner ───────────────────────────────────────────────────────────────

def run(user_input: str, model: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # Agents
    classifier = ConversableAgent("Classifier", system_message=CLASSIFIER_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")
    helper     = ConversableAgent("Helper",     system_message=HELPER_SYSTEM,     llm_config=llm_config, human_input_mode="NEVER")
    validator  = ConversableAgent("Validator",  system_message=VALIDATOR_SYSTEM,  llm_config=llm_config, human_input_mode="NEVER")

    # Gate 1a: Keyword pre-screen
    print("Gate 1a: Keyword pre-screen ...")
    kw_class = classify_keywords(user_input)
    if kw_class.startswith("harmful"): return "I cannot help with that request. (Blocked by Keyword)"
    if kw_class.startswith("off_topic"): return "That question is outside my scope. (Blocked by Keyword)"

    # Gate 1b: LLM classification
    print("Gate 1b: LLM input classification ...")
    input_reply = classifier.generate_reply(messages=[{"content": user_input, "role": "user"}])
    input_class = str(input_reply).lower()
    if "harmful" in input_class: return "I cannot help with that request. (Blocked by LLM)"
    if "off_topic" in input_class: return "That question is outside my scope. (Blocked by LLM)"

    # Gate 2: PII redaction
    print("Gate 2: PII redaction ...")
    clean_input = redact_pii_logic(user_input)

    # Gate 3: Safe generation
    print("Gate 3: Safe generation ...")
    gen_reply = helper.generate_reply(messages=[{"content": clean_input, "role": "user"}])
    raw_response = str(gen_reply)

    # Gate 4: Output validation
    print("Gate 4: Output validation ...")
    val_reply = validator.generate_reply(messages=[{
        "content": f"User: {user_input}\nAssistant: {raw_response}",
        "role": "user"
    }])
    val_class = str(val_reply).lower()

    if "safe" in val_class:
        return raw_response
    elif "pii" in val_class:
        return redact_pii_logic(raw_response)
    else:
        return "I was unable to generate a safe response."


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--user-input", required=True,    help="User message to process")
@click.option("--model",      default="gemma3", show_default=True)
@click.option("--log-dir",    default="cookbook/18_guardrails/autogen/logs-autogen", show_default=True)
def main(user_input: str, model: str, log_dir: str):
    result = run(user_input, model, log_dir)
    print("\n" + "=" * 60)
    print(f"RESPONSE:\n{result}")

if __name__ == "__main__":
    main()
