"""
AutoGen equivalent of support_triage.spl

A procedural script coordinates specialized agents and deterministic tools
to implement a multi-step support triage pipeline.

Usage:
    pip install pyautogen
    python cookbook/28_support_triage/autogen/support_triage_autogen.py \
        --ticket "My account has been charged twice for order #ORD-12345"
"""

import click
import json
import re
from pathlib import Path

from autogen import ConversableAgent


# ── Deterministic Tool Logic ──────────────────────────────────────────────────

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
    orders_file = Path(__file__).parent.parent / "orders.json"
    if not orders_file.exists(): return "Order context unavailable."
    with open(orders_file, encoding="utf-8") as f: orders = json.load(f)
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
- billing: finance team, SLA 4h, high priority
- account: auth team, SLA 2h, high priority
- shipping: fulfillment, SLA 6h, high priority
- technical: engineering, SLA 8h, medium priority
- product: product team, SLA 24h, medium priority
- complaint: customer success, SLA 1h, urgent
- general: first-line, SLA 48h, low priority
"""

TONE_GUIDES = {
    "empathetic": 'Warm and understanding. Acknowledge frustration. Use "I understand" and "I am sorry".',
    "formal": 'Professional and precise. Reference ticket numbers and order IDs explicitly.',
    "friendly": 'Conversational and positive. Use the customer first name.',
    "professional": 'Professional but approachable. Concise. Action-oriented.'
}


# ── Agent system messages ─────────────────────────────────────────────────────

CLASSIFIER_SYSTEM = f"You are a support triage specialist. Classify tickets into these categories: {CATEGORIES}. Return JSON with category, reasoning, priority."
EXTRACTOR_SYSTEM = "Extract key details from support tickets and order context. Return JSON with order_id, issue_type, customer_name, amount, product."
URGENCY_SYSTEM = "Score the urgency of support tickets on a scale of 0-10. Return ONLY the numeric score."
DRAFER_SYSTEM = "Draft professional and helpful responses to customer support tickets based on classification, details, and order context."
CHECKER_SYSTEM = "Score the quality of support responses on a scale of 0-10. Return ONLY the numeric score."
REFINER_SYSTEM = "Improve support responses based on ticket and order context to make them more accurate and helpful."


# ── Helpers ───────────────────────────────────────────────────────────────────

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


# ── Main runner ───────────────────────────────────────────────────────────────

def run(ticket: str, product: str, tone: str, model: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # Agents
    classifier = ConversableAgent("Classifier", system_message=CLASSIFIER_SYSTEM, llm_config=llm_config, human_input_mode="NEVER")
    extractor  = ConversableAgent("Extractor",  system_message=EXTRACTOR_SYSTEM,  llm_config=llm_config, human_input_mode="NEVER")
    urgency    = ConversableAgent("Urgency",    system_message=URGENCY_SYSTEM,    llm_config=llm_config, human_input_mode="NEVER")
    drafter    = ConversableAgent("Drafter",    system_message=DRAFER_SYSTEM,    llm_config=llm_config, human_input_mode="NEVER")
    checker    = ConversableAgent("Checker",    system_message=CHECKER_SYSTEM,    llm_config=llm_config, human_input_mode="NEVER")
    refiner    = ConversableAgent("Refiner",    system_message=REFINER_SYSTEM,    llm_config=llm_config, human_input_mode="NEVER")

    # Step 1 & 2: Preprocess
    print("Preprocessing ...")
    onums = extract_order_logic(ticket)
    ocontext = lookup_order_logic(onums)

    # Step 3: Classify
    print("Classifying ...")
    class_reply = classifier.generate_reply(messages=[{"content": f"Ticket: {ticket}\nOrder Context: {ocontext}", "role": "user"}])
    classification = _parse_json(str(class_reply))

    # Step 4: Extract Details
    print("Extracting details ...")
    det_reply = extractor.generate_reply(messages=[{"content": f"Ticket: {ticket}\nOrder Context: {ocontext}", "role": "user"}])
    details = _parse_json(str(det_reply))

    # Step 5: Detect Urgency
    print("Detecting urgency ...")
    urg_reply = urgency.generate_reply(messages=[{"content": f"Ticket: {ticket}\nClassification: {classification}", "role": "user"}])
    try: score = int(re.search(r"\d+", str(urg_reply)).group())
    except: score = 5

    if score > 8:
        print(f"High urgency ({score}) — escalating ...")
        # Reuse drafter for escalation alert logic
        alert_reply = drafter.generate_reply(messages=[{"content": f"Generate an urgent escalation alert for: {ticket}\nContext: {ocontext}\nClass: {classification}", "role": "user"}])
        _write(f"{log_dir}/escalation.md", str(alert_reply))
        return f"STATUS: escalated\n\n{alert_reply}"

    # Step 7: Draft
    print("Drafting response ...")
    tone_guide = TONE_GUIDES.get(tone, TONE_GUIDES["professional"])
    draft_reply = drafter.generate_reply(messages=[{"content": f"Draft response for: {ticket}\nDetails: {details}\nContext: {ocontext}\nProduct: {product}\nTone: {tone_guide}", "role": "user"}])
    draft = str(draft_reply)

    # Step 8: Quality Check
    print("Checking quality ...")
    chk_reply = checker.generate_reply(messages=[{"content": f"Score quality: {draft}\nTicket: {ticket}\nContext: {ocontext}", "role": "user"}])
    try: q_score = int(re.search(r"\d+", str(chk_reply)).group())
    except: q_score = 7

    if q_score < 6:
        print(f"Quality ({q_score}) below threshold — refining ...")
        ref_reply = refiner.generate_reply(messages=[{"content": f"Improve this draft: {draft}\nTicket: {ticket}\nContext: {ocontext}", "role": "user"}])
        draft = str(ref_reply)
        status = "drafted_revised"
    else:
        status = "drafted"

    _write(f"{log_dir}/response.md", draft)
    return f"STATUS: {status}\n\n{draft}"


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--ticket",  required=True,       help="Support ticket text")
@click.option("--product", default="CloudDash", show_default=True)
@click.option("--tone",    default="professional", show_default=True)
@click.option("--model",   default="gemma3",    show_default=True)
@click.option("--log-dir", default="cookbook/28_support_triage/autogen/logs-autogen", show_default=True)
def main(ticket: str, product: str, tone: str, model: str, log_dir: str):
    result = run(ticket, product, tone, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
