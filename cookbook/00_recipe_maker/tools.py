"""
tools.py — Python tools for Recipe 00: Recipe Maker.

The recipe-maker's own tool layer. Handles all deterministic operations:
loading patterns, reading datasets and resources, writing generated artifacts
to disk, and notifying the user for review.

Tools:
  load_patterns(pattern_id)           Load all patterns or a specific pattern from patterns.json.
  load_dataset(path)                  Load dataset content from a local file (JSON, CSV, TXT).
  load_resources(path)                Load reference/context material from a local file.
  write_artifact(output_dir, filename, content)
                                      Write a generated artifact to output_dir (with /tmp fallback).
  list_artifacts(output_dir)          List all files written to output_dir.
  notify_review(output_dir, artifact_list, feedback_mode)
                                      Format a human-readable review notification.

Usage:
  spl run cookbook/00_recipe_maker/recipe_maker.spl \\
      --adapter ollama -m gemma3 \\
      --tools cookbook/00_recipe_maker/tools.py \\
      concept="Customer churn predictor with explainability" \\
      output_dir="cookbook/38_churn_predictor/"
"""

import csv
import json
import os
import textwrap
from datetime import datetime

from spl.tools import spl_tool

_RECIPE_DIR = os.path.dirname(__file__)
_COOKBOOK_DIR = os.path.dirname(_RECIPE_DIR)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wrap(text: str, width: int = 76, indent: str = "  ") -> str:
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        lines.append(textwrap.fill(paragraph, width=width, subsequent_indent=indent))
    return "\n".join(lines)


def _resolve_output_dir(output_dir: str) -> tuple[str, bool]:
    """
    Resolve and create output_dir. Falls back to /tmp/spl_recipes/<name>/ on
    permission error. Returns (resolved_path, used_fallback).
    """
    path = os.path.abspath(output_dir.strip()) if output_dir.strip() else ""
    if not path:
        path = os.path.join("/tmp", "spl_recipes", f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    try:
        os.makedirs(path, exist_ok=True)
        # Quick write-permission test
        test = os.path.join(path, ".write_test")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return path, False
    except PermissionError:
        fallback = os.path.join("/tmp", "spl_recipes", os.path.basename(path.rstrip("/")))
        os.makedirs(fallback, exist_ok=True)
        return fallback, True


# ── Tools ─────────────────────────────────────────────────────────────────────

@spl_tool
def load_patterns(pattern_id: str = "") -> str:
    """
    Load the SPL recipe pattern catalog from patterns.json.

    Pass pattern_id="" to return all patterns as a structured summary.
    Pass a specific pattern_id (e.g. "chain", "debate", "guardrails") to get full detail.
    Pass pattern_id="list" to get a compact ID+name listing only.
    """
    path = os.path.join(_RECIPE_DIR, "patterns.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    patterns = data["patterns"]
    pid = pattern_id.strip().lower()

    if pid == "list":
        lines = ["Available patterns:", ""]
        for p in patterns:
            lines.append(f"  {p['id']:20s} [{p['category']:12s}] — {p['name']}")
        return "\n".join(lines)

    if pid:
        match = next((p for p in patterns if p["id"] == pid), None)
        if match is None:
            available = ", ".join(p["id"] for p in patterns)
            return f"Pattern '{pid}' not found. Available: {available}"
        lines = [
            f"PATTERN: {match['name']} ({match['id']})",
            f"Category: {match['category']}",
            "",
            f"Description: {_wrap(match['description'])}",
            "",
            f"Use when: {_wrap(match['use_when'])}",
            "",
            f"Key structure:",
            f"  {match['key_structure']}",
            "",
            f"Example recipes: {', '.join(match['example_recipes'])}",
        ]
        return "\n".join(lines)

    # Full catalog summary
    lines = ["SPL RECIPE PATTERNS", "=" * 68, ""]
    for p in patterns:
        lines.append(f"[{p['id']}] {p['name']} — {p['category']}")
        lines.append(f"  {_wrap(p['description'], indent='  ')}")
        lines.append(f"  Use when: {_wrap(p['use_when'], indent='  ')}")
        lines.append(f"  Structure: {p['key_structure']}")
        lines.append(f"  See: {', '.join(p['example_recipes'])}")
        lines.append("")
    return "\n".join(lines)


@spl_tool
def load_dataset(path: str) -> str:
    """
    Load dataset content from a local file for use as recipe context.

    Supports:
      - .json  — pretty-printed JSON (first 50 records if array)
      - .csv   — first 20 rows as pipe-separated text
      - .txt   — first 100 lines of plain text
      - empty  — returns a placeholder message

    The returned text is injected as context into generate_sample_data()
    so the recipe-maker can generate realistic, schema-compatible sample data.
    """
    path = path.strip()
    if not path:
        return "(no dataset provided — recipe-maker will generate representative sample data)"

    if not os.path.exists(path):
        return f"(dataset file not found: {path} — recipe-maker will generate sample data)"

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".json":
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                preview = data[:50]
                note = f"(showing first {len(preview)} of {len(data)} records)"
            else:
                preview = data
                note = "(full JSON object)"
            return f"DATASET from {os.path.basename(path)} {note}:\n{json.dumps(preview, indent=2)}"

        elif ext == ".csv":
            lines = ["DATASET from " + os.path.basename(path) + " (first 20 rows):"]
            with open(path, encoding="utf-8", newline="") as fh:
                reader = csv.reader(fh)
                for i, row in enumerate(reader):
                    if i >= 20:
                        lines.append("... (truncated)")
                        break
                    lines.append(" | ".join(row))
            return "\n".join(lines)

        else:  # .txt and other text formats
            with open(path, encoding="utf-8") as fh:
                raw_lines = fh.readlines()
            preview = raw_lines[:100]
            note = f"(showing first {len(preview)} of {len(raw_lines)} lines)"
            return f"DATASET from {os.path.basename(path)} {note}:\n{''.join(preview)}"

    except Exception as e:
        return f"(could not read dataset {path}: {e})"


@spl_tool
def load_resources(path: str) -> str:
    """
    Load reference material, documentation, or context from a local file.

    Accepts .txt, .md, .json, or any text file. Returns up to 200 lines.
    Pass path="" to skip — returns a placeholder.

    Used to ground the recipe plan with domain knowledge, related work,
    API docs, or any other reference the user wants to include.
    """
    path = path.strip()
    if not path:
        return "(no resources provided)"

    if not os.path.exists(path):
        return f"(resource file not found: {path})"

    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        preview = lines[:200]
        note = f"(showing first {len(preview)} of {len(lines)} lines)" if len(lines) > 200 else ""
        return f"RESOURCES from {os.path.basename(path)} {note}:\n{''.join(preview)}"
    except Exception as e:
        return f"(could not read resources {path}: {e})"


@spl_tool
def write_artifact(output_dir: str, filename: str, content: str) -> str:
    """
    Write a generated artifact to output_dir.

    Creates output_dir (and any parent directories) if they do not exist.
    Falls back to /tmp/spl_recipes/<dirname>/ on permission error and
    notifies the caller of the actual path used.

    Returns a status line: "written: <full_path>" or "error: <message>".
    """
    resolved, used_fallback = _resolve_output_dir(output_dir)
    full_path = os.path.join(resolved, filename.strip())

    try:
        with open(full_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        note = f" [NOTE: permission denied on '{output_dir}', used fallback]" if used_fallback else ""
        return f"written: {full_path}{note}"
    except Exception as e:
        return f"error writing {filename}: {e}"


@spl_tool
def list_artifacts(output_dir: str) -> str:
    """
    List all files written to output_dir with their sizes.

    Returns a structured summary of the generated artifact bundle,
    ready to be included in the review notification.
    """
    resolved, _ = _resolve_output_dir(output_dir)

    if not os.path.isdir(resolved):
        return f"(output directory not found: {resolved})"

    entries = []
    for fname in sorted(os.listdir(resolved)):
        fpath = os.path.join(resolved, fname)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            entries.append((fname, size))

    if not entries:
        return f"(no artifacts found in {resolved})"

    lines = [f"GENERATED ARTIFACTS in {resolved}:", ""]
    for fname, size in entries:
        lines.append(f"  {fname:<30s} {size:>8,} bytes")
    lines.append("")
    lines.append(f"  Total: {len(entries)} file(s), {sum(s for _, s in entries):,} bytes")
    return "\n".join(lines)


@spl_tool
def notify_review(output_dir: str, artifact_list: str, feedback_mode: str) -> str:
    """
    Format a human-readable review notification for the generated recipe bundle.

    When feedback_mode is 'human' (default): instructs the user to review the
    artifacts and validate manually. The workflow does not auto-iterate.

    When feedback_mode is 'llm-judge': placeholder for v2 auto-validation.

    Returns the notification text that is COMMIT-ted as the workflow output.
    """
    resolved, used_fallback = _resolve_output_dir(output_dir)
    divider = "─" * 68
    feedback_mode = feedback_mode.strip().lower() or "human"

    lines = [
        "RECIPE GENERATION COMPLETE",
        divider,
        "",
        artifact_list,
        divider,
        "",
    ]

    if feedback_mode == "human":
        lines += [
            "NEXT STEPS — Human Review Required:",
            "",
            "  1. Review the generated artifacts in:",
            f"     {resolved}",
            "",
            "  2. Run the generated workflow:",
            f"     spl run {os.path.join(resolved, 'workflow.spl')} --adapter ollama -m <model>",
            "        --tools " + os.path.join(resolved, "tools.py"),
            "",
            "  3. Taste the cake — does it produce the expected output?",
            "",
            "  4. If satisfied: re-run with --reflect and --publish flags (v2).",
            "     If not: edit the artifacts and re-run with your corrections.",
            "",
            "  Status: awaiting_human_review",
        ]
        if used_fallback:
            lines += [
                "",
                f"  NOTE: Original output_dir was not writable. Artifacts saved to:",
                f"  {resolved}",
            ]
    else:
        lines += [
            "NEXT STEPS — LLM-as-Judge validation (v2 placeholder):",
            "  Auto-validation not yet implemented. Please review manually.",
            f"  Artifacts: {resolved}",
        ]

    lines.append(divider)
    return "\n".join(lines)
