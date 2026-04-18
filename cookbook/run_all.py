#!/usr/bin/env python3
"""run_all.py — SPL 2.0 Cookbook batch runner.

Recipes are defined in cookbook/cookbook_catalog.json — edit that file to
add, remove, or update recipes without touching Python code.

Usage:
    python cookbook/run_all.py                                                        # run all active recipes (spl)
    python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json       # run all active recipes (spl-go)
    python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json       # run all active recipes (spl-ts)
    python cookbook/run_all.py --adapter ollama                                       # override adapter
    python cookbook/run_all.py --adapter momagrid                                     # parallel submit to momagrid hub
    python cookbook/run_all.py --adapter momagrid --workers 5
    python cookbook/run_all.py --model gemma3                                         # override model
    python cookbook/run_all.py --ids 04,08,13                                         # run specific recipes by ID
    python cookbook/run_all.py --list                                                 # brief recipe list
    python cookbook/run_all.py --list --category agentic
    python cookbook/run_all.py --catalog                                              # full catalog table
    python cookbook/run_all.py --catalog --status new

conda activate spl
cd ~/projects/digital-duck/SPL20
python cookbook/run_all.py 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md

# run on Momagrid
python cookbook/run_all.py --workers 5 --adapter momagrid 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S)-momagrid.md

#################################################################
# run on Momagrid with gemma3 on 2026-04-06 over 4 GPUs
conda activate spl2         # so spl CLI is available
export MOMAGRID_HUB_URL=http://192.168.0.170:9000

# use pinggy-free.link for external access to a local hub (no auth, not recommended for production)
export MOMAGRID_HUB_URL=https://qgzqm-99-111-153-200.run.pinggy-free.link

python cookbook/run_all.py --workers 10 --adapter momagrid --model gemma3 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S)-momagrid.md
#################################################################

"""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import click

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


# ── Catalog helpers ───────────────────────────────────────────────────────────

def load_catalog(catalog_file: str = "") -> list[dict]:
    path = Path(catalog_file) if catalog_file else COOKBOOK_DIR / "cookbook_catalog.json"
    if not path.is_absolute():
        path = Path.cwd() / path
    with open(path) as f:
        data = json.load(f)
    return data["recipes"]


def apply_filters(recipes: list[dict], category: str, status: str) -> list[dict]:
    out = []
    for r in recipes:
        if category and r.get("category") != category:
            continue
        if status and r.get("approval_status") != status:
            continue
        out.append(r)
    return out


def status_marker(r: dict) -> str:
    if r.get("is_active"):
        return MARKERS["active"]
    return MARKERS.get(r.get("approval_status", ""), "  ")


def parse_id_filter(ids: str) -> set[str]:
    """Parse comma-separated IDs / ranges like '1-4,10' into a set of zero-padded strings."""
    id_filter: set[str] = set()
    for part in ids.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            for n in range(int(lo.strip()), int(hi.strip()) + 1):
                id_filter.add(f"{n:02d}")
        else:
            id_filter.add(f"{int(part):02d}" if part.isdigit() else part)
    return id_filter


# ── Recipe execution ──────────────────────────────────────────────────────────

def apply_overrides(cmd_args: list[str], adapter: str, model: str) -> list[str]:
    """Apply --adapter and --model overrides to spl execute commands."""
    if not cmd_args:
        return cmd_args

    # Check if we should use local spl.cli
    if cmd_args[0] == "spl":
        result = ["python3", "-m", "spl.cli"]
        # Skip the original 'spl'; keep subcommand as-is (spl run → python3 -m spl.cli run)
        result.extend(cmd_args[1:])
    else:
        result = list(cmd_args)

    if adapter:
        if "--adapter" in result:
            result[result.index("--adapter") + 1] = adapter
        else:
            # Add --adapter before the .spl file
            for i in range(len(result)):
                if result[i].endswith(".spl"):
                    result.insert(i, "--adapter")
                    result.insert(i + 1, adapter)
                    break

    if model:
        # Check if --model already exists (never match -m: that is Python's module flag)
        found_model = False
        for i in range(len(result)):
            if result[i] == "--model":
                result[i + 1] = model
                found_model = True
                break

        if not found_model:
            # Add --model after the subcommand (run/execute)
            for i in range(len(result)):
                if result[i] in ("run", "execute"):
                    result.insert(i + 1, "--model")
                    result.insert(i + 2, model)
                    found_model = True
                    break

        if not found_model:
            result.extend(["--model", model])

    return result


def run_recipe_sequential(cmd_args: list[str], log_path: Path, cwd: Path) -> tuple[bool, float]:
    """Run a recipe subprocess, stream output with smart formatting, and log to file.

    Two rendering modes applied line-by-line:
      - in_fence : inside any ```lang...``` block → printed as-is (no prefix)
      - normal   : everything else → printed with '     | ' prefix
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(cwd)
        with open(log_path, "w") as log_file:
            process = subprocess.Popen(
                cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=str(cwd), env=env
            )
            state = "normal"
            for line in (process.stdout or []):
                log_file.write(line)
                s = line.rstrip("\n")
                if state == "in_fence":
                    sys.stdout.write(s + "\n")
                    if s.strip() == "```":
                        state = "normal"
                else:
                    if s.strip().startswith("```") and s.strip() != "```":
                        sys.stdout.write(s + "\n")
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


def run_recipe_parallel(recipe: dict, cmd_args: list[str], log_path: Path, cwd: Path) -> dict:
    """Run a single recipe in a background thread without live stdout streaming.

    Used when --adapter momagrid so that multiple recipes are submitted to the
    hub simultaneously, giving the dispatcher enough queued tasks to spread
    work across all registered agents.
    """
    rid = recipe["id"]
    name = recipe["name"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime.now()
    print(f"[{rid}] {name}  →  started")
    sys.stdout.flush()
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(cwd)
        with open(log_path, "w") as log_file:
            proc = subprocess.Popen(
                cmd_args, stdout=log_file, stderr=subprocess.STDOUT,
                text=True, cwd=str(cwd), env=env
            )
            proc.wait()
        ok = proc.returncode == 0
    except Exception as e:
        print(f"[{rid}] ERROR: {e}")
        ok = False
    elapsed = (datetime.now() - start).total_seconds()
    status = "SUCCESS" if ok else "FAILED"
    print(f"[{rid}] {name}  →  {status}  ({elapsed:.1f}s)  log: {log_path.name}")
    sys.stdout.flush()
    return {"id": rid, "name": name, "ok": ok, "elapsed": elapsed}


def print_list(recipes: list[dict], category: str, status: str) -> None:
    filtered = apply_filters(recipes, category, status)
    label = f" (category={category!r} status={status!r})" if (category or status) else ""
    print(f"SPL 2.0 Cookbook — {len(filtered)} recipes{label}")
    for r in filtered:
        print(
            f"  {r['id']:<4}  {status_marker(r)}  {r['name']:<28}  "
            f"{r.get('approval_status',''):<12}  {r.get('category',''):<14}  "
            f"{r.get('description','')}"
        )


def print_catalog(recipes: list[dict], category: str, status: str) -> None:
    filtered = apply_filters(recipes, category, status)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    counts: dict[str, int] = {}
    for r in recipes:
        if r.get("is_active"):
            counts["active"] = counts.get("active", 0) + 1
        s = r.get("approval_status", "")
        counts[s] = counts.get(s, 0) + 1

    print(f"=== SPL 2.0 Cookbook Catalog — {now} ===")
    if category or status:
        print(f"    Filter: category={category!r}  status={status!r}  → {len(filtered)}/{len(recipes)} recipes\n")
    else:
        print(
            f"    Total: {len(recipes)} recipes  |  {counts.get('active', 0)} active  |  "
            f"{counts.get(STATUS_NEW, 0)} new  |  {counts.get(STATUS_WIP, 0)} wip  |  "
            f"{counts.get(STATUS_DISABLED, 0)} disabled\n"
        )

    print(f"{'ID':<4}  {'':2}  {'Name':<28}  {'Category':<14}  {'Status':<12}  Description")
    print("-" * 110)
    for r in filtered:
        print(
            f"{r['id']:<4}  {status_marker(r)}  {r['name']:<28}  "
            f"{r.get('category',''):<14}  {r.get('approval_status',''):<12}  "
            f"{r.get('description','')}"
        )

    print()
    print("Markers: ✅ active  🆕 new  🔧 wip  ⏸  disabled  ❌ rejected\n")
    print("Run active recipes:           python cookbook/run_all.py")
    print("Run specific recipe:          python cookbook/run_all.py --ids 05,11")
    print("Override adapter/model:       python cookbook/run_all.py --adapter momagrid --model llama3.2")
    print("Filter catalog by category:   python cookbook/run_all.py --catalog --category agentic")
    print("Filter catalog by status:     python cookbook/run_all.py --catalog --status new")

    cat_counts: dict[str, int] = {}
    for r in recipes:
        c = r.get("category", "")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    parts = [f"{c}({n})" for c, n in sorted(cat_counts.items())]
    print(f"\nCategories: {'  '.join(parts)}")


def print_summary(results: list[dict], start_all: datetime) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    total_elapsed = (datetime.now() - start_all).total_seconds()
    print(f"\n=== Summary: {passed}/{total} Success  (total {total_elapsed:.1f}s) ===\n")
    print(f"{'ID':<4}  {'Recipe':<28}  {'Status':<8}  {'Elapsed':>8}")
    print("-" * 56)
    for r in results:
        s = "OK" if r["ok"] else "FAILED"
        print(f"{r['id']:<4}  {r['name']:<28}  {s:<8}  {r['elapsed']:>7.1f}s")
    print()


@click.command()
@click.option("--adapter",      "-a", default="ollama", show_default=True,
              help="Override LLM adapter for all recipes (e.g. ollama, momagrid)")
@click.option("--model",        "-m", default="gemma3", show_default=True,
              help="Override model for all recipes")
@click.option("--ids",          default="", help="Comma-separated recipe IDs or ranges (e.g. '04,08,10-13')")
@click.option("--workers",      "-w", default=0, show_default=True, type=int,
              help="Max parallel workers for momagrid")
@click.option("--category",     default="", help="Only run recipes in this category")
@click.option("--status",       default="", help="Only run recipes with this approval status")
@click.option("--list",         "list_recipes", is_flag=True, help="Print brief recipe list and exit")
@click.option("--catalog",      is_flag=True, help="Print full catalog table and exit")
@click.option("--catalog-file", "catalog_file", default="",
              help="Path to catalog JSON (default: cookbook/cookbook_catalog.json). "
                   "Use cookbook/cookbook_catalog_go.json to test against the spl-go binary.")
def main(adapter, model, ids, workers, category, status, list_recipes, catalog, catalog_file) -> None:
    """SPL 2.0 Cookbook batch runner."""
    recipes = load_catalog(catalog_file)

    if catalog:
        print_catalog(recipes, category, status)
        return

    if list_recipes:
        print_list(recipes, category, status)
        return

    use_parallel = adapter == "momagrid"
    id_filter = parse_id_filter(ids) if ids else set()

    start_all = datetime.now()
    print(f"=== SPL 2.0 Cookbook Batch Run — {start_all.strftime('%Y-%m-%d %H:%M:%S')} ===")
    overrides = []
    if adapter:
        overrides.append(f"adapter={adapter}")
    if model:
        overrides.append(f"model={model}")
    if overrides:
        print(f"    Overrides : {', '.join(overrides)}")
    if use_parallel:
        print("    Mode      : parallel (momagrid — recipes submitted concurrently)")
    print()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build the work list
    active: list[tuple[dict, list[str], Path]] = []
    for r in recipes:
        rid = r["id"]
        if id_filter:
            if rid not in id_filter:
                continue
        else:
            if category and r.get("category") != category:
                continue
            if status and r.get("approval_status") != status:
                continue
            if not r.get("is_active"):
                print(f"[{rid}] {r['name']}  (skipping — {r.get('approval_status','').upper()})")
                continue
        cmd_args = apply_overrides(r["args"], adapter, model)
        log_path = COOKBOOK_DIR / r["dir"] / "logs" / f"{r['log']}_{ts}.md"
        active.append((r, cmd_args, log_path))

    if not active:
        print("No recipes to run.")
        return

    results: list[dict] = []

    PROJECT_ROOT = COOKBOOK_DIR.parent

    if use_parallel:
        n_workers = workers or len(active)
        print(f"Submitting {len(active)} recipe(s) with {n_workers} parallel worker(s)...\n")
        futures: dict = {}
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            for r, cmd_args, log_path in active:
                f = pool.submit(run_recipe_parallel, r, cmd_args, log_path, PROJECT_ROOT)
                futures[f] = r
        for f in as_completed(futures):
            results.append(f.result())
        results.sort(key=lambda x: x["id"])
    else:
        for r, cmd_args, log_path in active:
            rid = r["id"]
            print(f"[{rid}] {r['name']}")
            print(f"     cmd : {' '.join(cmd_args)}")
            print(f"     log : {log_path}")
            ok, elapsed = run_recipe_sequential(cmd_args, log_path, PROJECT_ROOT)
            print(f"     result: {'SUCCESS' if ok else 'FAILED'}  ({elapsed:.1f}s)\n")
            results.append({"id": rid, "name": r["name"], "ok": ok, "elapsed": elapsed})

    print_summary(results, start_all)


if __name__ == "__main__":
    main()
