"""
LangGraph equivalent of support_triage.spl

Pattern: extract_order → lookup_order → classify_ticket → extract_details → detect_urgency → (escalate | draft → check → refine)

Usage:
    pip install langgraph langchain-ollama
    python cookbook/28_support_triage/langgraph/support_triage_langgraph.py \
        --ticket "My account has been charged twice for order #ORD-12345"
"""

import click
import json
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Optional

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ── Prompts (mirrors GENERATE blocks in support_triage.spl) ─────────────────

CLASSIFY_PROMPT = """\
You are a support triage specialist. Classify the following ticket into one of these categories:
{categories}

Ticket: {ticket}
Order Context: {order_context}

Return a JSON object with:
- category: the selected category
- reasoning: brief explanation
- priority: low, medium, high, or urgent
"""

EXTRACT_DETAILS_PROMPT = """\
Extract key details from the support ticket and order context.
Ticket: {ticket}
Order Context: {order_context}

Return a JSON object with:
- order_id: if found
- issue_type: brief description
- customer_name: if found
- amount: if referenced
- product: if referenced
"""

DETECT_URGENCY_PROMPT = """\
Score the urgency of this support ticket on a scale of 0-10.
0 = very low, 10 = critical escalation.

Ticket: {ticket}
Classification: {classification}

Return ONLY the numeric score.
"""

ESCALATION_ALERT_PROMPT = """\
Generate an urgent escalation alert for the internal team.
Ticket: {ticket}
Classification: {classification}
Order Context: {order_context}

Provide a concise summary of why this needs immediate attention.
"""

DRAFT_RESPONSE_PROMPT = """\
Draft a response to the customer support ticket.
Ticket: {ticket}
Classification: {classification}
Details: {details}
Order Context: {order_context}
Product: {product}
Tone Guide: {tone_guide}

Write a professional and helpful response addressing the customer's issue.
"""

CHECK_QUALITY_PROMPT = """\
Score the quality of this draft response on a scale of 0-10.
0 = poor, 10 = excellent.

Draft: {draft}
Ticket: {ticket}
Order Context: {order_context}

Return ONLY the numeric score.
"""

IMPROVE_RESPONSE_PROMPT = """\
Improve the following draft response based on the ticket and order context.
Draft: {draft}
Ticket: {ticket}
Order Context: {order_context}

Provide a more accurate, helpful, and empathetic version.
"""


# ── State ────────────────────────────────────────────────────────────────────

class TriageState(TypedDict):
    ticket:         str
    product:        str
    tone:           str
    model:          str
    log_dir:        str
    
    order_numbers:  str
    order_context:  str
    classification: dict
    details:        dict
    urgency_score:  int
    draft:          str
    quality_score:  int
    final_output:   str
    status:         str


# ── Deterministic Tool Logic (from tools.py) ──────────────────────────────────

def extract_order_logic(text: str) -> str:
    patterns = [r'\bORD-(\d{5,})\b', r'\bORDER-(\d{5,})\b', r'#(\d{5,})\b', r'\border\s+(?:number\s+)?#?(\d{5,})\b']
    found = []
    seen = set()
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            oid = f"ORD-{m.group(1)}"
            if oid not in seen:
                seen.add(oid); found.append(oid)
    return ", ".join(found)

def lookup_order_logic(order_numbers: str) -> str:
    if not order_numbers: return "No order number found in this ticket."
    # For the port, we'll look for orders.json relative to this script
    orders_file = Path(__file__).parent.parent / "orders.json"
    if not orders_file.exists(): return f"Order context unavailable (orders.json not found at {orders_file})"
    
    with open(orders_file, encoding="utf-8") as f:
        orders = json.load(f)
    index = {o["order_id"].upper(): o for o in orders}
    found = []; missing = []
    for raw in order_numbers.split(","):
        oid = raw.strip().upper()
        if oid in index: found.append(index[oid])
        else: missing.append(oid)
    if not found: return f"Order(s) not found: {', '.join(missing)}"
    return json.dumps({"orders_found": found, "orders_not_found": missing}, indent=2)


# ── Support Triage Logic ──────────────────────────────────────────────────────

CATEGORIES = """
- billing:      finance team, SLA 4h,  high priority
- account:      auth team,    SLA 2h,  high priority
- shipping:     fulfillment,  SLA 6h,  high priority
- technical:    engineering,  SLA 8h,  medium priority
- product:      product team, SLA 24h, medium priority
- complaint:    customer success, SLA 1h, urgent
- general:      first-line,   SLA 48h, low priority
"""

TONE_GUIDES = {
    "empathetic": 'Warm and understanding. Acknowledge frustration. Use "I understand" and "I am sorry".',
    "formal": 'Professional and precise. Reference ticket numbers and order IDs explicitly.',
    "friendly": 'Conversational and positive. Use the customer first name.',
    "professional": 'Professional but approachable. Concise. Action-oriented.'
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _invoke(model: str, prompt: str) -> str:
    return ChatOllama(model=model).invoke(prompt).content.strip()

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _parse_json(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```json"): clean = clean[7:-3].strip()
    elif clean.startswith("```"): clean = clean[3:-3].strip()
    try: return json.loads(clean)
    except: return {"raw": text}


# ── Nodes ────────────────────────────────────────────────────────────────────

def node_preprocess(state: TriageState) -> dict:
    print("Extracting order numbers and looking up context ...")
    onums = extract_order_logic(state["ticket"])
    ocontext = lookup_order_logic(onums)
    return {"order_numbers": onums, "order_context": ocontext}

def node_classify(state: TriageState) -> dict:
    print("Classifying ticket ...")
    res = _invoke(state["model"], CLASSIFY_PROMPT.format(
        categories=CATEGORIES, ticket=state["ticket"], order_context=state["order_context"]
    ))
    return {"classification": _parse_json(res)}

def node_extract_details(state: TriageState) -> dict:
    print("Extracting structured details ...")
    res = _invoke(state["model"], EXTRACT_DETAILS_PROMPT.format(
        ticket=state["ticket"], order_context=state["order_context"]
    ))
    return {"details": _parse_json(res)}

def node_detect_urgency(state: TriageState) -> dict:
    print("Detecting urgency ...")
    res = _invoke(state["model"], DETECT_URGENCY_PROMPT.format(
        ticket=state["ticket"], classification=json.dumps(state["classification"])
    ))
    try: score = int(re.search(r"\d+", res).group())
    except: score = 5
    return {"urgency_score": score}

def node_escalate(state: TriageState) -> dict:
    print(f"High urgency ({state['urgency_score']}) — generating escalation alert ...")
    res = _invoke(state["model"], ESCALATION_ALERT_PROMPT.format(
        ticket=state["ticket"], classification=json.dumps(state["classification"]), order_context=state["order_context"]
    ))
    _write(f"{state['log_dir']}/escalation.md", res)
    return {"final_output": res, "status": "escalated"}

def node_draft(state: TriageState) -> dict:
    print("Drafting response ...")
    tone_guide = TONE_GUIDES.get(state["tone"], TONE_GUIDES["professional"])
    res = _invoke(state["model"], DRAFT_RESPONSE_PROMPT.format(
        ticket=state["ticket"], classification=json.dumps(state["classification"]),
        details=json.dumps(state["details"]), order_context=state["order_context"],
        product=state["product"], tone_guide=tone_guide
    ))
    return {"draft": res}

def node_quality_check(state: TriageState) -> dict:
    print("Checking draft quality ...")
    res = _invoke(state["model"], CHECK_QUALITY_PROMPT.format(
        draft=state["draft"], ticket=state["ticket"], order_context=state["order_context"]
    ))
    try: score = int(re.search(r"\d+", res).group())
    except: score = 7
    return {"quality_score": score}

def node_improve(state: TriageState) -> dict:
    print(f"Quality ({state['quality_score']}) below threshold — improving draft ...")
    res = _invoke(state["model"], IMPROVE_RESPONSE_PROMPT.format(
        draft=state["draft"], ticket=state["ticket"], order_context=state["order_context"]
    ))
    return {"draft": res, "status": "drafted_revised"}

def node_finalize(state: TriageState) -> dict:
    print("Finalizing response ...")
    _write(f"{state['log_dir']}/response.md", state["draft"])
    status = state.get("status", "drafted")
    return {"final_output": state["draft"], "status": status}


# ── Routing ──────────────────────────────────────────────────────────────────

def _route_urgency(state: TriageState) -> str:
    if state["urgency_score"] > 8: return "escalate"
    return "draft"

def _route_quality(state: TriageState) -> str:
    if state["quality_score"] < 6 and state.get("status") != "drafted_revised": 
        return "improve"
    return "finalize"


# ── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(TriageState)
    g.add_node("preprocess", node_preprocess)
    g.add_node("classify",   node_classify)
    g.add_node("details",    node_extract_details)
    g.add_node("urgency",    node_detect_urgency)
    g.add_node("escalate",   node_escalate)
    g.add_node("draft",      node_draft)
    g.add_node("quality",    node_quality_check)
    g.add_node("improve",    node_improve)
    g.add_node("finalize",   node_finalize)

    g.set_entry_point("preprocess")
    g.add_edge("preprocess", "classify")
    g.add_edge("classify", "details")
    g.add_edge("details", "urgency")
    
    g.add_conditional_edges("urgency", _route_urgency, {
        "escalate": "escalate",
        "draft": "draft"
    })
    
    g.add_edge("draft", "quality")
    g.add_conditional_edges("quality", _route_quality, {
        "improve": "improve",
        "finalize": "finalize"
    })
    
    g.add_edge("improve", "finalize")
    g.add_edge("escalate", END)
    g.add_edge("finalize", END)
    
    return g.compile()


# ── Main ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--ticket",  required=True,       help="Support ticket text")
@click.option("--product", default="CloudDash", show_default=True)
@click.option("--tone",    default="professional", show_default=True)
@click.option("--model",   default="gemma3",    show_default=True)
@click.option("--log-dir", default="cookbook/28_support_triage/langgraph/logs-langgraph", show_default=True)
def main(ticket: str, product: str, tone: str, model: str, log_dir: str):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    result = build_graph().invoke({
        "ticket":         ticket,
        "product":        product,
        "tone":           tone,
        "model":          model,
        "log_dir":        log_dir,
        "order_numbers":  "",
        "order_context":  "",
        "classification": {},
        "details":        {},
        "urgency_score":  0,
        "draft":          "",
        "quality_score":  0,
        "final_output":   "",
        "status":         "",
    })

    print("\n" + "=" * 60)
    print(f"STATUS: {result['status']}")
    print(f"RESULT:\n{result['final_output']}")

if __name__ == "__main__":
    main()
