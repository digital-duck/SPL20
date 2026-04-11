"""
CrewAI equivalent of support_triage.spl

Multiple Agents (Triage Specialist, Data Extractor, Drafter, Quality Auditor)
collaborate on a multi-step support triage pipeline managed by a Python loop.

Usage:
    pip install crewai langchain-ollama
    python cookbook/28_support_triage/crewai/support_triage_crewai.py \
        --ticket "My account has been charged twice for order #ORD-12345"
"""

import click
import json
import re
from pathlib import Path

from crewai import Agent, Crew, Process, Task


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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_task(agent: Agent, description: str, expected_output: str) -> str:
    t = Task(description=description, expected_output=expected_output, agent=agent)
    result = Crew(agents=[agent], tasks=[t], process=Process.sequential, verbose=False).kickoff()
    return str(result).strip()


# ── Main runner ───────────────────────────────────────────────────────────────

def run(ticket: str, product: str, tone: str, model: str, log_dir: str) -> str:
    llm = f"ollama/{model}"

    triage_specialist = Agent(
        role="Triage Specialist",
        goal="Classify support tickets and detect urgency.",
        backstory="You are an expert at routing customer issues and identifying critical problems.",
        llm=llm,
        verbose=False,
    )
    data_extractor = Agent(
        role="Data Extractor",
        goal="Extract key details from support tickets and order data.",
        backstory="You are a meticulous analyst who pulls structured data from noisy text.",
        llm=llm,
        verbose=False,
    )
    support_drafter = Agent(
        role="Support Drafter",
        goal="Draft professional and helpful responses to customer issues.",
        backstory="You are a skilled communicator who crafts grounded and empathetic support responses.",
        llm=llm,
        verbose=False,
    )
    quality_auditor = Agent(
        role="Quality Auditor",
        goal="Ensure support responses meet high standards of accuracy and tone.",
        backstory="You are a strict reviewer who identifies areas for improvement in support communications.",
        llm=llm,
        verbose=False,
    )

    # Preprocess
    print("Preprocessing ...")
    onums = extract_order_logic(ticket)
    ocontext = lookup_order_logic(onums)

    # Classify
    print("Classifying ...")
    classification = _run_task(
        triage_specialist,
        description=f"Classify this ticket into categories: {CATEGORIES}\nTicket: {ticket}\nOrder Context: {ocontext}\nReturn JSON with category, reasoning, priority.",
        expected_output="JSON with category, reasoning, priority."
    )

    # Extract details
    print("Extracting details ...")
    details = _run_task(
        data_extractor,
        description=f"Extract key details (order_id, issue, customer, amount, product) from:\nTicket: {ticket}\nOrder Context: {ocontext}",
        expected_output="JSON with extracted fields."
    )

    # Detect urgency
    print("Detecting urgency ...")
    urgency_res = _run_task(
        triage_specialist,
        description=f"Score urgency (0-10) for:\nTicket: {ticket}\nClassification: {classification}",
        expected_output="A single numeric score."
    )
    try: score = int(re.search(r"\d+", urgency_res).group())
    except: score = 5

    if score > 8:
        print(f"High urgency ({score}) — escalating ...")
        alert = _run_task(
            support_drafter,
            description=f"Generate urgent escalation alert for:\nTicket: {ticket}\nContext: {ocontext}",
            expected_output="A concise escalation summary."
        )
        _write(f"{log_dir}/escalation.md", alert)
        return f"STATUS: escalated\n\n{alert}"

    # Draft
    print("Drafting response ...")
    tone_guide = TONE_GUIDES.get(tone, TONE_GUIDES["professional"])
    draft = _run_task(
        support_drafter,
        description=f"Draft response for: {ticket}\nDetails: {details}\nContext: {ocontext}\nTone Guide: {tone_guide}",
        expected_output="A professional support response."
    )

    # Quality check
    print("Checking quality ...")
    q_res = _run_task(
        quality_auditor,
        description=f"Score quality (0-10) for:\nDraft: {draft}\nTicket: {ticket}",
        expected_output="A single numeric score."
    )
    try: q_score = int(re.search(r"\d+", q_res).group())
    except: q_score = 7

    status = "drafted"
    if q_score < 6:
        print(f"Quality ({q_score}) below threshold — improving ...")
        draft = _run_task(
            support_drafter,
            description=f"Improve this draft based on the original issue and context:\n{draft}",
            expected_output="An improved support response."
        )
        status = "drafted_revised"

    _write(f"{log_dir}/response.md", draft)
    return f"STATUS: {status}\n\n{draft}"


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--ticket",  required=True,       help="Support ticket text")
@click.option("--product", default="CloudDash", show_default=True)
@click.option("--tone",    default="professional", show_default=True)
@click.option("--model",   default="gemma3",    show_default=True)
@click.option("--log-dir", default="cookbook/28_support_triage/crewai/logs-crewai", show_default=True)
def main(ticket: str, product: str, tone: str, model: str, log_dir: str):
    result = run(ticket, product, tone, model, log_dir)
    print("\n" + "=" * 60)
    print(result)

if __name__ == "__main__":
    main()
