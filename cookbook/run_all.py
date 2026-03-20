#!/usr/bin/env python3
"""run_all.py — SPL 2.0 Cookbook batch runner.

Recipes are defined in cookbook/cookbook_catalog.json — edit that file to
add, remove, or update recipes without touching Python code.

Usage:
    python cookbook/run_all.py                           # run all active recipes
    python cookbook/run_all.py --adapter ollama           # override adapter
    python cookbook/run_all.py --model gemma3             # override model
    python cookbook/run_all.py --ids 04,08,13             # run specific recipes by ID
    python cookbook/run_all.py --list                     # brief recipe list
    python cookbook/run_all.py --catalog                  # full catalog table
    python cookbook/run_all.py --catalog --category agentic
    python cookbook/run_all.py --catalog --status new

    python cookbook/run_all.py 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md 
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

COOKBOOK_DIR = Path(__file__).resolve().parent

# Approval status values
STATUS_APPROVED = "approved"
STATUS_NEW      = "new"
STATUS_WIP      = "wip"
STATUS_DISABLED = "disabled"
STATUS_REJECTED = "rejected"

# Status markers (visual indicators)
MARKERS = {
    "active":         "✅",
    STATUS_NEW:       "🆕",
    STATUS_WIP:       "🔧",
    STATUS_DISABLED:  "⏸ ",
    STATUS_REJECTED:  "❌",
}


def load_catalog() -> list[dict]:
    path = COOKBOOK_DIR / "cookbook_catalog.json"
    with open(path) as f:
        data = json.load(f)
    return data["recipes"]


def apply_filters(recipes: list[dict], cat_filter: str, status_filter: str) -> list[dict]:
    out = []
    for r in recipes:
        if cat_filter and r.get("category") != cat_filter:
            continue
        if status_filter and r.get("approval_status") != status_filter:
            continue
        out.append(r)
    return out


def status_marker(r: dict) -> str:
    if r.get("is_active"):
        return MARKERS["active"]
    return MARKERS.get(r.get("approval_status", ""), "  ")


def print_list(recipes: list[dict], cat_filter: str, status_filter: str) -> None:
    filtered = apply_filters(recipes, cat_filter, status_filter)
    label = f" (category={cat_filter!r} status={status_filter!r})" if (cat_filter or status_filter) else ""
    print(f"SPL 2.0 Cookbook — {len(filtered)} recipes{label}")
    for r in filtered:
        print(f"  {r['id']:<4}  {status_marker(r)}  {r['name']:<28}  {r.get('approval_status',''):<12}  {r.get('category',''):<14}  {r.get('description','')}")


def print_catalog(recipes: list[dict], cat_filter: str, status_filter: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filtered = apply_filters(recipes, cat_filter, status_filter)

    counts: dict[str, int] = {}
    for r in recipes:
        if r.get("is_active"):
            counts["active"] = counts.get("active", 0) + 1
        status = r.get("approval_status", "")
        counts[status] = counts.get(status, 0) + 1

    print(f"=== SPL 2.0 Cookbook Catalog — {now} ===")
    if cat_filter or status_filter:
        print(f"    Filter: category={cat_filter!r}  status={status_filter!r}  → {len(filtered)}/{len(recipes)} recipes\n")
    else:
        print(f"    Total: {len(recipes)} recipes  |  {counts.get('active', 0)} active  |  {counts.get(STATUS_NEW, 0)} new  |  {counts.get(STATUS_WIP, 0)} wip  |  {counts.get(STATUS_DISABLED, 0)} disabled\n")

    print(f"{'ID':<4}  {'':2}  {'Name':<28}  {'Category':<14}  {'Status':<12}  Description")
    print("-" * 110)
    for r in filtered:
        print(f"{r['id']:<4}  {status_marker(r)}  {r['name']:<28}  {r.get('category',''):<14}  {r.get('approval_status',''):<12}  {r.get('description','')}")

    print()
    print("Markers: ✅ active  🆕 new  🔧 wip  ⏸  disabled  ❌ rejected\n")
    print("Run active recipes:           python cookbook/run_all.py")
    print("Run specific recipe:          python cookbook/run_all.py --ids 05,11")
    print("Run any (incl. inactive):     python cookbook/run_all.py --ids 17")
    print("Override adapter/model:       python cookbook/run_all.py --adapter ollama --model gemma3")
    print("Filter catalog by category:   python cookbook/run_all.py --catalog --category agentic")
    print("Filter catalog by status:     python cookbook/run_all.py --catalog --status new")

    cat_counts: dict[str, int] = {}
    for r in recipes:
        c = r.get("category", "")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    parts = [f"{c}({n})" for c, n in sorted(cat_counts.items())]
    print(f"\nCategories: {'  '.join(parts)}")


def run_recipe(args: list[str], log_path: Path, cwd: Path) -> tuple[bool, float]:
    """Run a recipe subprocess and stream output with smart formatting.

    Two rendering modes applied line-by-line:
      - in_fence : inside any ```lang...``` block → printed as-is (no prefix)
      - normal   : everything else → printed with '     | ' prefix

    The ```output``` block for LLM results is emitted by `spl2 run` itself
    (via _print_result in cli.py), so run_all only needs to pass it through.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now()
    try:
        with open(log_path, "w") as log_file:
            process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=str(cwd),
            )

            state = "normal"   # "normal" | "in_fence"

            for line in (process.stdout or []):
                log_file.write(line)
                s = line.rstrip("\n")

                if state == "in_fence":
                    sys.stdout.write(s + "\n")
                    if s.strip() == "```":          # closing fence
                        state = "normal"
                else:
                    if s.strip().startswith("```") and s.strip() != "```":
                        sys.stdout.write(s + "\n")  # opening fence — no prefix
                        state = "in_fence"
                    else:
                        sys.stdout.write(f"     | {s}\n")

            process.wait()
            ok = process.returncode == 0
    except Exception as e:
        print(f"     | ERROR: {e}")
        ok = False
    elapsed = (datetime.now() - start).total_seconds()
    return ok, elapsed


def apply_overrides(cmd_args: list[str], adapter: str, model: str) -> list[str]:
    """Apply --adapter and --model overrides to spl2 run commands."""
    if not cmd_args or cmd_args[0] != "spl2":
        return cmd_args

    result = list(cmd_args)

    if adapter:
        # Replace existing --adapter or insert after 'run'
        if "--adapter" in result:
            idx = result.index("--adapter")
            result[idx + 1] = adapter
        else:
            # Insert after 'run' and the .spl file path
            for i, arg in enumerate(result):
                if arg.endswith(".spl"):
                    result.insert(i + 1, "--adapter")
                    result.insert(i + 2, adapter)
                    break

    if model:
        # Replace existing -m/--model or insert after --adapter
        if "-m" in result:
            idx = result.index("-m")
            result[idx + 1] = model
        elif "--model" in result:
            idx = result.index("--model")
            result[idx + 1] = model
        else:
            result.extend(["-m", model])

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="SPL 2.0 Cookbook batch runner")
    parser.add_argument("--adapter", default="", help="Override LLM adapter for all spl2 recipes")
    parser.add_argument("--model", "-m", default="", help="Override model for all spl2 recipes")
    parser.add_argument("--ids", default="", help="Comma-separated recipe IDs to run")
    parser.add_argument("--list", action="store_true", dest="list_recipes", help="List recipes and exit")
    parser.add_argument("--catalog", action="store_true", help="Print full catalog table and exit")
    parser.add_argument("--category", default="", help="Filter by category (use with --catalog or --list)")
    parser.add_argument("--status", default="", help="Filter by approval_status (use with --catalog or --list)")
    args = parser.parse_args()

    recipes = load_catalog()

    if args.catalog:
        print_catalog(recipes, args.category, args.status)
        return

    if args.list_recipes:
        print_list(recipes, args.category, args.status)
        return

    # Build ID filter set — supports "1-4, 10" ranges and plain lists
    id_filter: set[str] = set()
    if args.ids:
        for part in args.ids.split(","):
            part = part.strip()
            if "-" in part:
                lo, hi = part.split("-", 1)
                for n in range(int(lo.strip()), int(hi.strip()) + 1):
                    id_filter.add(f"{n:02d}")
            else:
                id_filter.add(f"{int(part):02d}" if part.isdigit() else part)

    start_all = datetime.now()
    print(f"=== SPL 2.0 Cookbook Batch Run — {start_all.strftime('%Y-%m-%d %H:%M:%S')} ===")
    if args.adapter or args.model:
        overrides = []
        if args.adapter:
            overrides.append(f"adapter={args.adapter}")
        if args.model:
            overrides.append(f"model={args.model}")
        print(f"    Overrides: {', '.join(overrides)}")
    print()

    os.chdir(COOKBOOK_DIR)

    results: list[dict] = []

    for recipe in recipes:
        rid = recipe["id"]

        if id_filter:
            if rid not in id_filter:
                continue
        elif not recipe.get("is_active"):
            print(f"[{rid}] {recipe['name']}  (skipping — {recipe.get('approval_status','').upper()})\n")
            continue

        # Apply adapter/model overrides
        cmd_args = apply_overrides(recipe["args"], args.adapter, args.model)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = COOKBOOK_DIR / recipe["dir"] / f"{recipe['log']}_{ts}.log"

        print(f"[{rid}] {recipe['name']}")
        print(f"     cmd : {' '.join(cmd_args)}")
        print(f"     log : {log_path}")

        ok, elapsed = run_recipe(cmd_args, log_path, COOKBOOK_DIR)
        status = "SUCCESS" if ok else "FAILED"
        print(f"     result: {status}  ({elapsed:.1f}s)\n")

        results.append({"id": rid, "name": recipe["name"], "ok": ok, "elapsed": elapsed})

    # Summary table
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    total_elapsed = (datetime.now() - start_all).total_seconds()
    print(f"=== Summary: {passed}/{total} Success  (total {total_elapsed:.1f}s) ===\n")

    print(f"{'ID':<4}  {'Recipe':<28}  {'Status':<8}  {'Elapsed':>8}")
    print("-" * 56)
    for r in results:
        status = "OK" if r["ok"] else "FAILED"
        print(f"{r['id']:<4}  {r['name']:<28}  {status:<8}  {r['elapsed']:>7.1f}s")
    print()


if __name__ == "__main__":
    main()
