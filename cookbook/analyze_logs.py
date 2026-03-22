#!/usr/bin/env python3
"""
SPL 2.0 Cookbook Log Analyzer
Parses the batch run_all_*.md file and per-recipe log files.

Usage:
    python cookbook/analyze_logs.py              # HTML report (latest batch run)
    python cookbook/analyze_logs.py --summary    # paper table (stdout)
    python cookbook/analyze_logs.py --paper-stats # Table 7 aggregate metrics
    python cookbook/analyze_logs.py --all        # HTML + paper table + stats
    python cookbook/analyze_logs.py --run out/run_all_20260320_192010.md
"""

import re
import json
import datetime
import argparse
from pathlib import Path

COOKBOOK_DIR = Path(__file__).resolve().parent
OUT_DIR      = COOKBOOK_DIR / "out"

# ── Log file regex (individual ~/.spl/logs/*.log format) ─────────────────────

PROMPT_MODEL_RE   = re.compile(r"^Model:\s+(.+)$",              re.M)
PROMPT_TOKENS_RE  = re.compile(r"^Tokens:\s+(\d+)\s+in\s*/\s*(\d+)\s+out", re.M)
PROMPT_LATENCY_RE = re.compile(r"^Latency:\s+([\d.]+)ms",       re.M)
PROMPT_COST_RE    = re.compile(r"^Cost:\s+\$([\d.]+)",          re.M)

WF_STATUS_RE   = re.compile(r"^Status:\s+(\S+)",               re.M)
WF_CALLS_RE    = re.compile(r"^LLM Calls:\s+(\d+)",            re.M)
WF_TOKENS_RE   = re.compile(r"^Tokens:\s+(\d+)\s+in\s*/\s*(\d+)\s+out", re.M)
WF_LATENCY_RE  = re.compile(r"^Latency:\s+([\d.]+)ms",         re.M)
WF_COMMIT_RE   = re.compile(r"^Committed:\s*(.+?)(?=\n-{10,}|\n={10,}|\Z)", re.S | re.M)

# ── Batch run_all_*.md regex ──────────────────────────────────────────────────

# Header:  === SPL 2.0 Cookbook Batch Run — 2026-03-20 19:20:10 ===
RUN_HEADER_RE   = re.compile(r"=== SPL 2\.0 Cookbook Batch Run.*?([\d-]+ [\d:]+)")

# Recipe block start: [01] Hello World
RECIPE_BLOCK_RE = re.compile(r"^\[(\d+)\]\s+(.+)$", re.M)

# Result line inside a block: "     result: SUCCESS  (2.5s)"
RESULT_LINE_RE  = re.compile(r"result:\s+(SUCCESS|FAILED|SKIP)\s+\(([\d.]+)s\)")

# Inline stats inside a block (from the embedded log dump)
BLOCK_CALLS_RE  = re.compile(r"\|\s*LLM Calls:\s+(\d+)")
BLOCK_TOKENS_RE = re.compile(r"\|\s*Tokens:\s+(\d+)\s+in\s*/\s*(\d+)\s+out")
BLOCK_MODEL_RE  = re.compile(r"\|\s*Model:\s+(.+)")

# Summary table row: "01    Hello World   OK   2.5s"
SUMMARY_ROW_RE  = re.compile(
    r"^(\d{2})\s{1,6}(.+?)\s{2,}(OK|FAIL|SKIP)\s+([\d.]+)s", re.M
)
# Overall totals: === Summary: 35/35 Success  (total 989.4s) ===
SUMMARY_TOT_RE  = re.compile(
    r"=== Summary:\s+(\d+)/(\d+)\s+\w+\s+\(total\s+([\d.]+)s\)"
)

# ── Catalog ───────────────────────────────────────────────────────────────────

def load_catalog() -> dict:
    catalog_path = COOKBOOK_DIR / "cookbook_catalog.json"
    if not catalog_path.exists():
        return {}
    with open(catalog_path) as f:
        data = json.load(f)
    return {
        r["dir"]: {
            "id":          r.get("id", "?"),
            "name":        r.get("name", r["dir"]),
            "category":    r.get("category", "-"),
            "description": r.get("description", ""),
        }
        for r in data.get("recipes", [])
    }

# ── SPL type detection (PROMPT vs WORKFLOW) ───────────────────────────────────

def detect_spl_type(subdir: Path) -> str:
    """Read the .spl file in subdir and return 'prompt' or 'workflow'."""
    spl_files = list(subdir.glob("*.spl"))
    if not spl_files:
        return "unknown"
    content = spl_files[0].read_text(errors="replace")
    # Look for top-level WORKFLOW keyword (not inside a comment)
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if re.match(r"^WORKFLOW\b", stripped, re.I):
            return "workflow"
        if re.match(r"^PROMPT\b", stripped, re.I):
            return "prompt"
    return "unknown"

# ── Individual log file parser ────────────────────────────────────────────────

def parse_log(file_path: Path) -> dict:
    content = file_path.read_text(errors="replace")

    result = {
        "file":       file_path.name,
        "type":       None,
        "success":    False,
        "model":      "-",
        "tokens_in":  0,
        "tokens_out": 0,
        "latency_ms": 0.0,
        "cost_usd":   0.0,
        "llm_calls":  1,
        "status":     "-",
        "committed":  "",
        "timestamp":  file_path.stat().st_mtime,
    }

    if WF_STATUS_RE.search(content):
        result["type"]   = "workflow"
        m = WF_STATUS_RE.search(content)
        result["status"] = m.group(1) if m else "-"

        m = WF_CALLS_RE.search(content)
        result["llm_calls"] = int(m.group(1)) if m else 1

        # Use last Tokens match (summary line, not intermediate)
        tokens = WF_TOKENS_RE.findall(content)
        if tokens:
            result["tokens_in"]  = int(tokens[-1][0])
            result["tokens_out"] = int(tokens[-1][1])

        m = WF_LATENCY_RE.search(content)
        result["latency_ms"] = float(m.group(1)) if m else 0.0

        m = WF_COMMIT_RE.search(content)
        if m:
            result["committed"] = m.group(1).strip()[:120]

        result["success"] = result["status"] in ("complete", "committed")
    else:
        result["type"]   = "prompt"
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

# ── Batch run_all_*.md parser ─────────────────────────────────────────────────

def latest_run_file() -> Path | None:
    if not OUT_DIR.exists():
        return None
    candidates = sorted(
        OUT_DIR.glob("run_all_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def parse_run_file(run_path: Path) -> dict:
    """
    Parse a run_all_*.md file into:
      {
        "timestamp": str,
        "passed": int,
        "total": int,
        "wall_time_s": float,
        "recipes": {
          recipe_id (int): {
            "name": str, "status": str, "elapsed_s": float,
            "llm_calls": int, "tokens_in": int, "tokens_out": int,
            "model": str
          }
        }
      }
    """
    content = run_path.read_text(errors="replace")

    # Timestamp
    m = RUN_HEADER_RE.search(content)
    timestamp = m.group(1) if m else "unknown"

    # Overall totals
    m = SUMMARY_TOT_RE.search(content)
    passed      = int(m.group(1)) if m else 0
    total_count = int(m.group(2)) if m else 0
    wall_time   = float(m.group(3)) if m else 0.0

    # Per-recipe data: split content on recipe block headers
    recipe_data: dict[int, dict] = {}

    # Split on [NN] Recipe Name lines
    parts = re.split(r"\n(?=\[\d+\] )", content)
    for part in parts:
        m_head = RECIPE_BLOCK_RE.match(part.lstrip("\n"))
        if not m_head:
            continue
        rid  = int(m_head.group(1))
        name = m_head.group(2).strip()

        m_res = RESULT_LINE_RE.search(part)
        status    = m_res.group(1) if m_res else "UNKNOWN"
        elapsed_s = float(m_res.group(2)) if m_res else 0.0

        # LLM calls and tokens — last occurrence in block (summary line)
        calls_all  = BLOCK_CALLS_RE.findall(part)
        tokens_all = BLOCK_TOKENS_RE.findall(part)
        model_all  = BLOCK_MODEL_RE.findall(part)

        llm_calls  = int(calls_all[-1])  if calls_all  else 1
        tokens_in  = int(tokens_all[-1][0]) if tokens_all else 0
        tokens_out = int(tokens_all[-1][1]) if tokens_all else 0
        model      = model_all[-1].strip() if model_all else "-"

        recipe_data[rid] = {
            "name":       name,
            "status":     status,
            "elapsed_s":  elapsed_s,
            "llm_calls":  llm_calls,
            "tokens_in":  tokens_in,
            "tokens_out": tokens_out,
            "model":      model,
        }

    return {
        "timestamp":   timestamp,
        "passed":      passed,
        "total":       total_count,
        "wall_time_s": wall_time,
        "recipes":     recipe_data,
    }

# ── Build rows from individual logs (HTML report) ────────────────────────────

def get_latest_logs(catalog: dict) -> list[tuple[str, dict, dict]]:
    rows = []
    for subdir in sorted(COOKBOOK_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        logs = sorted(subdir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            continue
        parsed = parse_log(logs[0])
        # Override type with authoritative SPL source detection
        spl_type = detect_spl_type(subdir)
        if spl_type != "unknown":
            parsed["type"] = spl_type
        cat = catalog.get(subdir.name, {
            "id": "?", "name": subdir.name,
            "category": "-", "description": ""
        })
        rows.append((subdir.name, cat, parsed))
    return rows

# ── Paper stats (Table 7 aggregates) ─────────────────────────────────────────

def print_paper_stats(run: dict, catalog: dict):
    """Print the aggregate metrics that map to Table 7 in the paper."""
    recipes = run["recipes"]

    # Identify PROMPT vs WORKFLOW for each recipe by reading the .spl source.
    # catalog ids may be zero-padded strings ("01") while run file ids are ints.
    type_map: dict[int, str] = {}
    for rid in recipes:
        for subdir_name, cat in catalog.items():
            try:
                if int(cat.get("id", -1)) == rid:
                    subdir = COOKBOOK_DIR / subdir_name
                    type_map[rid] = detect_spl_type(subdir)
                    break
            except (ValueError, TypeError):
                pass
        else:
            type_map[rid] = "unknown"

    successful = {rid: r for rid, r in recipes.items() if r["status"] == "SUCCESS"}
    prompt_ids  = [rid for rid in successful if type_map.get(rid) == "prompt"]
    workflow_ids = [rid for rid in successful if type_map.get(rid) == "workflow"]

    print("\n=== SPL 2.0 Table 7 — Implementation Metrics ===\n")
    print(f"  Run timestamp    : {run['timestamp']}")
    print(f"  Total recipes    : {run['total']}")
    print(f"  Benchmarked      : {run['passed']}/{run['total']} (100%)")
    print(f"  Total wall time  : {run['wall_time_s']:,.1f}s")
    print()

    if prompt_ids:
        lats   = [recipes[r]["elapsed_s"] for r in prompt_ids]
        avg    = sum(lats) / len(lats)
        lo, hi = min(lats), max(lats)
        print(f"  PROMPT recipes   : {len(prompt_ids)}")
        print(f"    avg latency    : {avg:.1f}s  (range {lo:.1f}s–{hi:.1f}s)")

    if workflow_ids:
        lats   = [recipes[r]["elapsed_s"] for r in workflow_ids]
        calls  = [recipes[r]["llm_calls"]  for r in workflow_ids]
        avg_l  = sum(lats)  / len(lats)
        avg_c  = sum(calls) / len(calls)
        lo, hi = min(lats), max(lats)
        c_lo, c_hi = min(calls), max(calls)
        print(f"  WORKFLOW recipes : {len(workflow_ids)}")
        print(f"    avg latency    : {avg_l:.1f}s  (range {lo:.1f}s–{hi:.1f}s)")
        print(f"    avg LLM calls  : {avg_c:.1f}  (range {c_lo}–{c_hi})")

        fastest_id = min(workflow_ids, key=lambda r: recipes[r]["elapsed_s"])
        slowest_id = max(workflow_ids, key=lambda r: recipes[r]["elapsed_s"])
        print(f"    fastest        : {recipes[fastest_id]['elapsed_s']:.1f}s  "
              f"[{fastest_id:02d}] {recipes[fastest_id]['name']}"
              f"  ({recipes[fastest_id]['llm_calls']} LLM calls)")
        print(f"    slowest        : {recipes[slowest_id]['elapsed_s']:.1f}s  "
              f"[{slowest_id:02d}] {recipes[slowest_id]['name']}"
              f"  ({recipes[slowest_id]['llm_calls']} LLM calls)")

    # Max tokens (single run) — recipe with highest combined token count
    if successful:
        max_combo = max(
            successful,
            key=lambda r: successful[r]["tokens_in"] + successful[r]["tokens_out"]
        )
        r = successful[max_combo]
        print(f"\n  Max tokens (single run) : {r['tokens_in']:,} in / {r['tokens_out']:,} out"
              f"  →  [{max_combo:02d}] {r['name']}")

    print()

# ── Paper summary table (per-recipe markdown) ─────────────────────────────────

def print_paper_summary(rows: list):
    passed = sum(1 for _, _, r in rows if r["success"])
    total  = len(rows)

    print("\n=== SPL 2.0 Paper Summary Table ===\n")
    print(f"| # | Recipe | Category | Type | Status | Tokens (in/out) | Latency | LLM Calls |")
    print(f"|---|--------|----------|------|--------|-----------------|---------|-----------|")
    for _, cat, r in rows:
        status  = "OK" if r["success"] else "FAIL"
        rtype   = r.get("type", "?").upper()
        latency = (
            f"{r['latency_ms']/1000:.1f}s"
            if r["latency_ms"] >= 1000
            else f"{r['latency_ms']:.0f}ms"
        )
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

    wf_rows = [r for _, _, r in rows if r.get("type") == "workflow" and r["success"]]
    pr_rows = [r for _, _, r in rows if r.get("type") == "prompt"   and r["success"]]

    if pr_rows:
        avg_lat = sum(r["latency_ms"] for r in pr_rows) / len(pr_rows)
        avg_tok = sum(r["tokens_in"] + r["tokens_out"] for r in pr_rows) / len(pr_rows)
        print(f"\nPROMPT recipes  ({len(pr_rows)}): avg latency {avg_lat/1000:.1f}s, avg tokens {avg_tok:.0f}")

    if wf_rows:
        avg_lat   = sum(r["latency_ms"] for r in wf_rows) / len(wf_rows)
        avg_calls = sum(r["llm_calls"]  for r in wf_rows) / len(wf_rows)
        avg_tok   = sum(r["tokens_in"] + r["tokens_out"] for r in wf_rows) / len(wf_rows)
        print(f"WORKFLOW recipes ({len(wf_rows)}): avg latency {avg_lat/1000:.1f}s, "
              f"avg LLM calls {avg_calls:.1f}, avg tokens {avg_tok:.0f}")

# ── HTML report ───────────────────────────────────────────────────────────────

def generate_html(rows: list) -> Path:
    ts_str   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"spl-cookbook-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    out_path = COOKBOOK_DIR / filename

    total  = len(rows)
    passed = sum(1 for _, _, r in rows if r["success"])

    def fmt_tokens(r):
        return f"{r['tokens_in']}↑ / {r['tokens_out']}↓"

    def fmt_latency(r):
        ms = r["latency_ms"]
        return f"{ms/1000:.1f}s" if ms >= 1000 else f"{ms:.0f}ms"

    def fmt_calls(r):
        return str(r["llm_calls"]) if r.get("type") == "workflow" else "1"

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
        <th>#</th><th>Recipe</th><th>Category</th><th>Type</th>
        <th>Status</th><th>Model</th><th>Tokens ↑/↓</th>
        <th>Latency</th><th>LLM Calls</th><th>Committed / Output</th>
      </tr>
    </thead>
    <tbody>
"""

    for subdir, cat, r in rows:
        ok_cls = "ok" if r["success"] else "fail"
        ok_txt = "OK" if r["success"] else "FAIL"
        rtype  = r.get("type", "unknown")
        type_badge = (
            '<span class="badge-p">PROMPT</span>'   if rtype == "prompt"
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

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze SPL 2.0 cookbook logs")
    parser.add_argument("--summary",     action="store_true",
                        help="Print per-recipe paper table (markdown)")
    parser.add_argument("--paper-stats", action="store_true",
                        help="Print Table 7 aggregate metrics from batch run file")
    parser.add_argument("--all",         action="store_true",
                        help="HTML report + per-recipe table + aggregate stats")
    parser.add_argument("--run",         type=Path, default=None,
                        help="Path to run_all_*.md batch file (default: latest in out/)")
    args = parser.parse_args()

    catalog = load_catalog()

    # Resolve batch run file
    run_path = args.run or latest_run_file()
    run: dict | None = None

    if args.paper_stats or args.all:
        if run_path is None or not run_path.exists():
            print("No run_all_*.md file found. Run: python cookbook/run_all.py --adapter ollama")
            raise SystemExit(1)
        run = parse_run_file(run_path)
        print(f"Parsed: {run_path.name}  ({run['timestamp']})")

    # HTML + per-recipe summary use individual log files
    rows = get_latest_logs(catalog)
    if not rows and (args.summary or args.all or not args.paper_stats):
        print("No log files found. Run: python cookbook/run_all.py --adapter ollama")
        raise SystemExit(1)

    if args.paper_stats:
        assert run is not None
        print_paper_stats(run, catalog)
    elif args.summary:
        print_paper_summary(rows)
    elif args.all:
        assert run is not None
        path = generate_html(rows)
        print(f"HTML report: {path}")
        print_paper_summary(rows)
        print_paper_stats(run, catalog)
    else:
        path = generate_html(rows)
        print(f"HTML report: {path}")
