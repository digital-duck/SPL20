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
def read_news_feed(file_path: str) -> str:
    """Read news feed file and split by lines, returning JSON list of news items"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Split by 'BATCH' and filter empty results
        # Assuming the file starts with 'BATCH', content.split('BATCH') will have an empty first element
        news_items = [line.strip() for line in content.split('BATCH') if line.strip()]
        return json.dumps(news_items)
    except FileNotFoundError:
        return "[]"
    except Exception as e:
        return "[]"

@spl_tool
def get_list_length(news_list: str) -> int:
    """Return the length of a list (supports JSON and Python string representations)"""
    if not news_list:
        return 0
        
    try:
        # Try JSON first
        items = json.loads(news_list)
        if isinstance(items, list):
            return len(items)
    except (json.JSONDecodeError, TypeError):
        # Handle stringified Python list like ['a', 'b'] which uses single quotes
        if news_list.strip().startswith('[') and news_list.strip().endswith(']'):
            try:
                import ast
                items = ast.literal_eval(news_list)
                if isinstance(items, list):
                    return len(items)
            except:
                pass
    
    # If it's not a list representation, it might have been passed a literal list from some other tool
    if isinstance(news_list, list):
        return len(news_list)
        
    return 0

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

# @spl_tool
# def write_log(path: str, content: str) -> str:
#     os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
#     with open(path, 'w', encoding='utf-8') as f:
#         f.write(content)
#     return f"logged_to_{path}"