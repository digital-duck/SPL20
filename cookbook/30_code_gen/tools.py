"""Tools for Recipe 30: Code Generator + Tests"""

import os
from spl.tools import spl_tool


@spl_tool
def load_spec(spec: str) -> str:
    """Load a spec from a file path or return the text as-is.

    If *spec* looks like a readable file path, the file contents are returned.
    Otherwise the string is returned unchanged so callers can pass an inline spec.
    """
    candidate = spec.strip()
    if candidate and os.path.exists(candidate) and os.path.isfile(candidate):
        with open(candidate, encoding="utf-8") as fh:
            contents = fh.read().strip()
        return f"[loaded from {candidate}]\n\n{contents}"
    return candidate
