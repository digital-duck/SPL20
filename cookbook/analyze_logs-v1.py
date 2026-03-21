#!/usr/bin/env python3
"""
SPL 2.0 Cookbook Log Analyzer
Parses per-recipe log files and generates an HTML report + paper table summary.

Usage:
    python cookbook/analyze_logs.py              # HTML report
    python cookbook/analyze_logs.py --summary    # paper table (stdout)
    python cookbook/analyze_logs.py --all        # HTML + paper table
"""

import re
import json
import datetime
import argparse
from pathlib import Path

COOKBOOK_DIR = Path(__file__).resolve().parent

# ── Log format regex ──────────────────────────────────────────────────────────

# PROMPT format
PROMPT_MODEL_RE   = re.compile(r"^Model:\s+(.+)$",              re.M)
PROMPT_TOKENS_RE  = re.compile(r"^Tokens:\s+(\d+)\s+in\s*/\s*(\d+)\s+out", re.M)
PROMPT_LATENCY_RE = re.compile(r"^Latency:\s+([\d.]+)ms",       re.M)
PROMPT_COST_RE    = re.compile(r"^Cost:\s+\$([\d.]+)",          re.M)

# WORKFLOW format
WF_STATUS_RE   = re.compile(r"^Status:\s+(\S+)",               re.M)
WF_CALLS_RE    = re.compile(r"^LLM Calls:\s+(\d+)",            re.M)
WF_TOKENS_RE   = re.compile(r"^Tokens:\s+(\d+)\s+in\s*/\s*(\d+)\s+out", re.M)
WF_LATENCY_RE  = re.compile(r"^Latency:\s+([\d.]+)ms",         re.M)
WF_COMMIT_RE   = re.compile(r"^Committed:\s*(.+?)(?=\n-{10,}|\n={10,}|\Z)", re.S | re.M)

# ── Catalog ───────────────────────────────────────────────────────────────────

def load_catalog() -> dict:
    """Return dict keyed by recipe dir name → {name, category, description}."""
    catalog_path = COOKBOOK_DIR / "cookbook_catalog.json"
    if not catalog_path.exists():
        return {}
    with open(catalog_path) as f:
        data = json.load(f)
    index = {}
    for r in data.get("recipes", []):
        index[r["dir"]] = {
            "id":          r.get("id", "?"),
            "name":        r.get("name", r["dir"]),
            "category":    r.get("category", "-"),
            "description": r.get("description", ""),
        }
    return index

# ── Log parser ────────────────────────────────────────────────────────────────

def parse_log(file_path: Path) -> dict:
    content = file_path.read_text(errors="replace")

    result = {
        "file":     file_path.name,
        "type":     None,      # "prompt" | "workflow"
        "success":  False,
        "model":    "-",
        "tokens_in":  0,
        "tokens_out": 0,
        "latency_ms": 0.0,
        "cost_usd":   0.0,
        "llm_calls":  1,
        "status":   "-",
        "committed": "",
        "timestamp": file_path.stat().st_mtime,
    }

    # Detect type by presence of "Status:" line (workflow) vs "Model:" (prompt)
    if WF_STATUS_RE.search(content):
        result["type"] = "workflow"
        m = WF_STATUS_RE.search(content)
        result["status"] = m.group(1) if m else "-"

        m = WF_CALLS_RE.search(content)
        result["llm_calls"] = int(m.group(1)) if m else 1

        m = WF_TOKENS_RE.search(content)
        if m:
            result["tokens_in"]  = int(m.group(1))
            result["tokens_out"] = int(m.group(2))

        m = WF_LATENCY_RE.search(content)
        result["latency_ms"] = float(m.group(1)) if m else 0.0

        m = WF_COMMIT_RE.search(content)
        if m:
            result["committed"] = m.group(1).strip()[:120]

        result["success"] = result["status"] in ("complete", "committed")

    else:
        result["type"] = "prompt"
        result["status"] = "complete"

        m = PROMPT_MODEL_RE.search(content)
        result["model"] = m.group(1).strip() if m else "-"

        m = PROMPT_TOKENS_RE.search(content)
        if m:
            result["tokens_in"]  = int(m.group(1))
            result["tokens_out"] = int(m.group(2))

        m = PROMPT_LATENCY_RE.search(content)
        result["latency_ms"] = float(m.group(1)) if m else 0.0

        m = PROMPT_COST_RE.search(content)
        result["cost_usd"] = float(m.group(1)) if m else 0.0

        result["success"] = (
            "Traceback" not in content
            and result["tokens_out"] > 0
        )

    return result


def get_latest_logs(catalog: dict) -> list[tuple[str, dict, dict]]:
    """Return list of (subdir, catalog_entry, parsed_log) for latest log per recipe."""
    rows = []
    for subdir in sorted(COOKBOOK_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        logs = sorted(subdir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            continue
        parsed  = parse_log(logs[0])
        cat     = catalog.get(subdir.name, {
            "id": "?", "name": subdir.name,
            "category": "-", "description": ""
        })
        rows.append((subdir.name, cat, parsed))
    return rows

# ── HTML report ───────────────────────────────────────────────────────────────

def generate_html(rows: list) -> Path:
    ts_str   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"spl2-cookbook-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = COOKBOOK_DIR / filename

    total    = len(rows)
    passed   = sum(1 for _, _, r in rows if r["success"])

    def fmt_tokens(r):
        return f"{r['tokens_in']}↑ / {r['tokens_out']}↓"

    def fmt_latency(r):
        ms = r["latency_ms"]
        return f"{ms/1000:.1f}s" if ms >= 1000 else f"{ms:.0f}ms"

    def fmt_calls(r):
        if r["type"] == "workflow":
            return str(r["llm_calls"])
        return "1"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>SPL 2.0 Cookbook Report</title>
  <style>
    body     {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
               background: #0e1117; color: #fafafa; margin: 40px; }}
    h1       {{ color: #4f8ef7; border-bottom: 2px solid #1e293b; padding-bottom: 10px; }}
    .summary {{ color: #888; margin-bottom: 30px; font-size: 1.1em; }}
    .summary span {{ color: #3fb950; font-weight: bold; }}
    table    {{ width: 100%; border-collapse: collapse; background: #161b22;
               border-radius: 8px; overflow: hidden;
               box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    th, td   {{ padding: 11px 14px; text-align: left;
               border-bottom: 1px solid #30363d; }}
    th       {{ background: #21262d; color: #8b949e; font-weight: 600;
               text-transform: uppercase; font-size: 11px; }}
    tr:hover {{ background: #1c2128; }}
    .ok      {{ color: #3fb950; font-weight: bold; }}
    .fail    {{ color: #f85149; font-weight: bold; }}
    .mono    {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; color: #c9d1d9; }}
    .cat     {{ font-size: 11px; color: #8b949e; }}
    .commit  {{ font-size: 11px; color: #a5d6ff; font-style: italic; max-width: 260px;
               overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .badge-p {{ background: #1f4068; color: #58a6ff; padding: 1px 6px; border-radius: 10px;
               font-size: 10px; }}
    .badge-w {{ background: #2d1f5e; color: #d2a8ff; padding: 1px 6px; border-radius: 10px;
               font-size: 10px; }}
    .footer  {{ margin-top: 40px; font-size: 12px; color: #8b949e; text-align: center; }}
  </style>
</head>
<body>
  <h1>SPL 2.0 Cookbook — Batch Run Report</h1>
  <div class="summary">
    Generated: {ts_str} &nbsp;|&nbsp;
    Status: <span>{passed}/{total} Success</span> &nbsp;|&nbsp;
    Adapter: ollama
  </div>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Recipe</th>
        <th>Category</th>
        <th>Type</th>
        <th>Status</th>
        <th>Model</th>
        <th>Tokens ↑/↓</th>
        <th>Latency</th>
        <th>LLM Calls</th>
        <th>Committed / Output</th>
      </tr>
    </thead>
    <tbody>
"""

    for subdir, cat, r in rows:
        ok_cls   = "ok"   if r["success"] else "fail"
        ok_txt   = "OK"   if r["success"] else "FAIL"
        type_badge = (
            '<span class="badge-p">PROMPT</span>'   if r["type"] == "prompt"
            else '<span class="badge-w">WORKFLOW</span>'
        )
        committed_td = f'<td class="commit" title="{r["committed"]}">{r["committed"]}</td>'

        html += f"""      <tr>
        <td class="mono">{cat.get('id','?')}</td>
        <td><strong>{cat.get('name', subdir)}</strong></td>
        <td class="cat">{cat.get('category','-')}</td>
        <td>{type_badge}</td>
        <td class="{ok_cls}">{ok_txt} <span style="font-weight:normal;font-size:11px">({r['status']})</span></td>
        <td class="mono">{r['model']}</td>
        <td class="mono">{fmt_tokens(r)}</td>
        <td class="mono">{fmt_latency(r)}</td>
        <td class="mono" style="text-align:center">{fmt_calls(r)}</td>
        {committed_td}
      </tr>
"""

    html += f"""    </tbody>
  </table>

  <div class="footer">
    SPL 2.0 — Declarative Agentic Workflow Orchestration &nbsp;|&nbsp;
    Digital Duck &copy; 2026 &nbsp;|&nbsp; Apache 2.0
  </div>
</body>
</html>
"""

    out_path.write_text(html)
    return out_path

# ── Paper summary table ───────────────────────────────────────────────────────

def print_paper_summary(rows: list):
    """Print a markdown table suitable for pasting into the paper (Table 7)."""
    passed = sum(1 for _, _, r in rows if r["success"])
    total  = len(rows)

    print("\n=== SPL 2.0 Paper Summary Table ===\n")
    print(f"| # | Recipe | Category | Type | Status | Tokens (in/out) | Latency | LLM Calls |")
    print(f"|---|--------|----------|------|--------|-----------------|---------|-----------|")
    for _, cat, r in rows:
        status  = "OK" if r["success"] else "FAIL"
        rtype   = "WORKFLOW" if r["type"] == "workflow" else "PROMPT"
        latency = f"{r['latency_ms']/1000:.1f}s" if r['latency_ms'] >= 1000 else f"{r['latency_ms']:.0f}ms"
        print(
            f"| {cat.get('id','?'):<2} "
            f"| {cat.get('name','-'):<28} "
            f"| {cat.get('category','-'):<13} "
            f"| {rtype:<8} "
            f"| {status:<6} "
            f"| {r['tokens_in']:>5} / {r['tokens_out']:<5} "
            f"| {latency:>8} "
            f"| {r['llm_calls']:>4} |"
        )

    print(f"\nTotal: {passed}/{total} passed")

    # Aggregate stats
    wf_rows = [r for _, _, r in rows if r["type"] == "workflow" and r["success"]]
    pr_rows = [r for _, _, r in rows if r["type"] == "prompt"   and r["success"]]

    if pr_rows:
        avg_lat = sum(r["latency_ms"] for r in pr_rows) / len(pr_rows)
        avg_tok = sum(r["tokens_in"] + r["tokens_out"] for r in pr_rows) / len(pr_rows)
        print(f"\nPROMPT recipes  ({len(pr_rows)}): avg latency {avg_lat/1000:.1f}s, avg tokens {avg_tok:.0f}")

    if wf_rows:
        avg_lat  = sum(r["latency_ms"] for r in wf_rows) / len(wf_rows)
        avg_calls = sum(r["llm_calls"] for r in wf_rows) / len(wf_rows)
        avg_tok  = sum(r["tokens_in"] + r["tokens_out"] for r in wf_rows) / len(wf_rows)
        print(f"WORKFLOW recipes ({len(wf_rows)}): avg latency {avg_lat/1000:.1f}s, avg LLM calls {avg_calls:.1f}, avg tokens {avg_tok:.0f}")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze SPL 2.0 cookbook logs")
    parser.add_argument("--summary", action="store_true", help="Print paper table to stdout")
    parser.add_argument("--all",     action="store_true", help="HTML report + paper table")
    args = parser.parse_args()

    catalog = load_catalog()
    rows    = get_latest_logs(catalog)

    if not rows:
        print("No log files found. Run: python cookbook/run_all.py --adapter ollama")
        raise SystemExit(1)

    if args.summary:
        print_paper_summary(rows)
    elif args.all:
        path = generate_html(rows)
        print(f"HTML report: {path}")
        print_paper_summary(rows)
    else:
        path = generate_html(rows)
        print(f"HTML report: {path}")
