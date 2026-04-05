"""
tools.py — Python tools for Recipe 41: Human Steering (Human-in-the-Loop).

Tools:
  wait_for_human_feedback(prompt)   Block and prompt the user for text input via stdin.
  write_file(path, content)         Write text to a file (creates parent dirs).

Usage:
  spl run cookbook/41_human_steering/human_steering.spl \\
      --tools cookbook/41_human_steering/tools.py \\
      --adapter ollama \\
      topic="The future of agentic AI"
"""

import os

from spl.tools import spl_tool


@spl_tool
def wait_for_human_feedback(prompt_msg: str) -> str:
    """
    Pause the workflow and prompt the human for feedback via stdin.

    Displays the prompt message, then reads a multi-line response until the user
    enters a blank line or presses Ctrl-D.  Returns the trimmed response text,
    or '' if no feedback is given (workflow continues with the original draft).
    """
    print("\n" + "=" * 60)
    print("HUMAN FEEDBACK REQUIRED")
    print("=" * 60)
    print(prompt_msg)
    print("-" * 60)
    print("Enter feedback (blank line or Ctrl-D to skip):")

    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass

    feedback = "\n".join(lines).strip()
    if feedback:
        print(f"[Feedback recorded: {len(feedback)} chars]")
    else:
        print("[No feedback — using draft as-is]")
    print("=" * 60 + "\n")
    return feedback


@spl_tool
def write_file(path: str, content: str) -> str:
    """
    Write text content to a file, creating parent directories if needed.

    Returns 'ok:<path>' on success or 'error:<message>' on failure.
    Pass 'NONE' as path to discard output without writing.
    """
    if not path or path.upper() == "NONE":
        return "ok:discarded"
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"ok:{path}"
    except OSError as exc:
        return f"error:{exc}"
