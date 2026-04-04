import json
import os
from spl.tools import spl_tool

@spl_tool
def extract_risk_rating(report_text: str) -> str:
    """Deterministic parser for LLM risk assessment output"""
    t = report_text.lower()
    if "high risk" in t or "critical" in t or "red flag" in t:
        return "high"
    elif "medium risk" in t or "moderate" in t or "review needed" in t:
        return "medium"
    return "low"

@spl_tool
def extract_json_field(json_str: str, field: str) -> str:
    """Safely extract a field from LLM JSON output"""
    try:
        # Handle potential markdown code blocks from LLMs
        clean = json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return str(data.get(field, "unknown"))
    except json.JSONDecodeError:
        return "parse_error"

@spl_tool
def send_alert(alert_payload: str) -> str:
    """Mock alert dispatcher (replace with Slack/Email webhook in prod)"""
    print(f"🚨 COMPLIANCE ALERT DISPATCHED:\n{alert_payload[:150]}...\n")
    return "alert_sent"

@spl_tool
def write_log(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"logged_to_{path}"