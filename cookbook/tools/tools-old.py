from spl.tools import spl_tool
import sys

@spl_tool
def wait_for_human_feedback(prompt_msg: str) -> str:
    """Pause execution and wait for human input from stdin.
    In a real system, this might send a notification and wait for an API response.
    """
    print(f"\n--- HUMAN INTERVENTION REQUIRED ---")
    print(f"Message: {prompt_msg}")
    print(f"Type your feedback (or press Enter to skip):")
    # Note: in non-interactive environments, this might fail or return empty.
    # For the cookbook, we'll return a mock string if stdin is not a TTY.
    if not sys.stdin.isatty():
        return "Looks good, but maybe make it more concise."
    
    try:
        feedback = input("> ")
        return feedback.strip()
    except EOFError:
        return ""

@spl_tool
def rag_update(content: str, metadata: str = "") -> str:
    """Mock tool to simulate updating a vector store or knowledge base."""
    print(f"DEBUG: RAG Update triggered with content length {len(content)}")
    return "success"

@spl_tool
def check_quality(text: str) -> str:
    """Mock quality checker. Returns 'pass' or 'fail'."""
    # Simple heuristic for the mock: fail if too short.
    if len(text.split()) < 5:
        return "fail"
    return "pass"
