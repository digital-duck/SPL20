"""
LangGraph equivalent of guardrails.spl

Pattern: keyword_prescreen → llm_classify_input → pii_detect_redact → safe_generate → validate_output

Usage:
    pip install langgraph langchain-ollama
    python cookbook/18_guardrails/langgraph/guardrails_langgraph.py \
        --user-input "My SSN is 123-45-6789, help me file taxes"
"""

import argparse
import json
import re
from pathlib import Path
from typing import TypedDict, Optional

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors GENERATE blocks in guardrails.spl) ──────────────────────

CLASSIFY_INPUT_PROMPT = """\
You are a safety classifier. Review the following user input and determine if it is:
1. harmful (requesting illegal acts, violence, malware, or sensitive data)
2. off_topic (asking for financial, medical, or legal advice outside your scope)
3. safe (everything else)

Input: {user_input}

Reply with exactly one word: harmful, off_topic, or safe.
"""

SAFE_RESPONSE_PROMPT = """\
You are a helpful and safe assistant. Provide a helpful response to the user's request.
Do NOT include any personally identifiable information (PII) in your response.

Request: {clean_input}
"""

VALIDATE_OUTPUT_PROMPT = """\
You are a safety validator. Review the assistant's response to the user's request.
Determine if the response:
1. contains_pii (leaks SSNs, emails, phones, or credit cards)
2. harmful (contains unsafe content)
3. safe (everything else)

Request: {user_input}
Response: {raw_response}

Reply with exactly one word: contains_pii, harmful, or safe.
"""


# ── State ────────────────────────────────────────────────────────────────────

class GuardrailsState(TypedDict):
    user_input:    str
    clean_input:   str
    model:         str
    log_dir:       str
    
    keyword_class: str
    input_class:   str
    pii_report:    str
    raw_response:  str
    output_check:  str
    safe_response: str
    status:        str


# ── Deterministic Tool Logic (from tools.py) ──────────────────────────────────

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

def detect_pii_logic(text: str) -> str:
    if SSN_RE.search(text) or CC_RE.search(text) or EMAIL_RE.search(text) or PHONE_RE.search(text):
        return "pii_found"
    return "clean"

def redact_pii_logic(text: str) -> str:
    text = SSN_RE.sub("[REDACTED-SSN]", text)
    text = CC_RE.sub("[REDACTED-CC]", text)
    text = EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED-PHONE]", text)
    return text


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_keyword_prescreen(state: GuardrailsState) -> dict:
    print("Gate 1a: Keyword pre-screen ...")
    res = classify_keywords(state["user_input"])
    return {"keyword_class": res}

def node_llm_classify(state: GuardrailsState) -> dict:
    print("Gate 1b: LLM input classification ...")
    res = _invoke(state["model"], CLASSIFY_INPUT_PROMPT.format(user_input=state["user_input"]))
    return {"input_class": res.lower()}

def node_pii_detect_redact(state: GuardrailsState) -> dict:
    print("Gate 2: PII detection & redaction ...")
    report = detect_pii_logic(state["user_input"])
    clean = redact_pii_logic(state["user_input"]) if report == "pii_found" else state["user_input"]
    return {"pii_report": report, "clean_input": clean}

def node_safe_generate(state: GuardrailsState) -> dict:
    print("Gate 3: Safe generation ...")
    res = _invoke(state["model"], SAFE_RESPONSE_PROMPT.format(clean_input=state["clean_input"]))
    return {"raw_response": res}

def node_validate_output(state: GuardrailsState) -> dict:
    print("Gate 4: Output validation ...")
    check = _invoke(state["model"], VALIDATE_OUTPUT_PROMPT.format(
        user_input=state["user_input"], raw_response=state["raw_response"]
    ))
    check = check.lower()
    
    if "safe" in check:
        return {"safe_response": state["raw_response"], "status": "complete"}
    elif "pii" in check:
        return {"safe_response": redact_pii_logic(state["raw_response"]), "status": "redacted_output"}
    else:
        return {"safe_response": "I was unable to generate a safe response.", "status": "blocked_output"}

def node_block_harmful(state: GuardrailsState) -> dict:
    print("Blocked: Harmful content")
    return {"safe_response": "I cannot help with that request.", "status": "blocked_harmful"}

def node_block_off_topic(state: GuardrailsState) -> dict:
    print("Blocked: Off-topic content")
    return {"safe_response": "That question is outside my scope.", "status": "blocked_off_topic"}


# ── Routing ──────────────────────────────────────────────────────────────────

def _route_keyword(state: GuardrailsState) -> str:
    if state["keyword_class"].startswith("harmful"): return "harmful"
    if state["keyword_class"].startswith("off_topic"): return "off_topic"
    return "llm_classify"

def _route_input_class(state: GuardrailsState) -> str:
    if "harmful" in state["input_class"]: return "harmful"
    if "off_topic" in state["input_class"]: return "off_topic"
    return "pii"


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(GuardrailsState)
    g.add_node("keyword",      node_keyword_prescreen)
    g.add_node("llm_classify", node_llm_classify)
    g.add_node("pii",          node_pii_detect_redact)
    g.add_node("generate",     node_safe_generate)
    g.add_node("validate",     node_validate_output)
    g.add_node("harmful",      node_block_harmful)
    g.add_node("off_topic",    node_block_off_topic)

    g.set_entry_point("keyword")
    
    g.add_conditional_edges("keyword", _route_keyword, {
        "harmful": "harmful",
        "off_topic": "off_topic",
        "llm_classify": "llm_classify"
    })
    
    g.add_conditional_edges("llm_classify", _route_input_class, {
        "harmful": "harmful",
        "off_topic": "off_topic",
        "pii": "pii"
    })
    
    g.add_edge("pii", "generate")
    g.add_edge("generate", "validate")
    g.add_edge("validate", END)
    g.add_edge("harmful", END)
    g.add_edge("off_topic", END)
    
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Guardrails Pipeline — LangGraph edition")
    p.add_argument("--user-input", required=True)
    p.add_argument("--model",      default="gemma3")
    p.add_argument("--log-dir",    default="cookbook/18_guardrails/langgraph/logs-langgraph")
    args = p.parse_args()

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "user_input":    args.user_input,
        "clean_input":   "",
        "model":         args.model,
        "log_dir":       args.log_dir,
        "keyword_class": "",
        "input_class":   "",
        "pii_report":    "",
        "raw_response":  "",
        "output_check":  "",
        "safe_response": "",
        "status":        "",
    })

    print("\n" + "=" * 60)
    print(f"STATUS: {result['status']}")
    print(f"RESPONSE:\n{result['safe_response']}")

if __name__ == "__main__":
    main()
