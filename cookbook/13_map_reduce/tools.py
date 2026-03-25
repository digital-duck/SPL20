"""Python tools for recipe 13: Map-Reduce Summarizer.

Loaded with:
    spl run cookbook/13_map_reduce/map_reduce.spl --tools cookbook/13_map_reduce/tools.py

Deterministic tools (CALL, zero tokens):
    CALL chunk_plan(@document) INTO @chunk_count
    CALL extract_chunk(@document, @chunk_index, @chunk_count) INTO @chunk

Note: write_file() and read_file() are SPL built-ins — no tools.py entry needed.
"""

from spl.tools import spl_tool

# Target chunk size: ~800 words (fits comfortably in most LLM context windows
# even after adding system prompt and instruction overhead)
_TARGET_CHUNK_WORDS = 800


@spl_tool
def chunk_plan(document: str) -> str:
    """Return the number of chunks needed to process the document.

    Splits by word count. Returns a string integer so SPL can store it
    in a NUMBER variable and use it in WHILE loop comparisons.
    """
    words = document.split()
    if not words:
        return "1"
    count = max(1, (len(words) + _TARGET_CHUNK_WORDS - 1) // _TARGET_CHUNK_WORDS)
    return str(count)


@spl_tool
def extract_chunk(document: str, chunk_index: str, chunk_count: str) -> str:
    """Extract the nth chunk of a document split evenly by word count.

    Args:
        document:    full document text
        chunk_index: 0-based index of the chunk to extract (string)
        chunk_count: total number of chunks (string)

    Returns the chunk text. If indices are out of range, returns empty string.
    """
    try:
        idx = int(float(chunk_index))
        total = int(float(chunk_count))
    except (ValueError, TypeError):
        return ""

    if total <= 0 or idx < 0 or idx >= total:
        return ""

    words = document.split()
    n = len(words)
    chunk_size = (n + total - 1) // total   # ceiling division for even distribution

    start = idx * chunk_size
    end = min(start + chunk_size, n)
    return " ".join(words[start:end])
