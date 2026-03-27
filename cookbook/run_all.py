#!/usr/bin/env python3
"""run_all.py — SPL 2.0 Cookbook batch runner.

Recipes are defined in cookbook/cookbook_catalog.json — edit that file to
add, remove, or update recipes without touching Python code.

Usage:
    python cookbook/run_all.py run                               # run all active recipes
    python cookbook/run_all.py run --adapter ollama              # override adapter
    python cookbook/run_all.py run --model gemma3                # override model
    python cookbook/run_all.py run --ids 04,08,13                # run specific recipes by ID
    python cookbook/run_all.py run --adapter momagrid            # parallel submit to momagrid hub
    python cookbook/run_all.py run --adapter momagrid --workers 4
    python cookbook/run_all.py list                              # brief recipe list
    python cookbook/run_all.py list --category agentic
    python cookbook/run_all.py catalog                           # full catalog table
    python cookbook/run_all.py catalog --status new

conda activate spl
cd ~/projects/digital-duck/SPL20
python cookbook/run_all.py 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md 

# run on Momagrid
python cookbook/run_all.py --adapter momagrid 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S)-momagrid.md 

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

def load_catalog() -> list[dict]:
    path = COOKBOOK_DIR / "cookbook_catalog.json"
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
    """Apply --adapter and --model overrides to spl run commands."""
    if not cmd_args or cmd_args[0] != "spl":
        return cmd_args

    result = list(cmd_args)

    if adapter:
        if "--adapter" in result:
            result[result.index("--adapter") + 1] = adapter
        else:
            for i, arg in enumerate(result):
                if arg.endswith(".spl"):
                    result.insert(i + 1, "--adapter")
                    result.insert(i + 2, adapter)
                    break

    if model:
        if "-m" in result:
            result[result.index("-m") + 1] = model
        elif "--model" in result:
            result[result.index("--model") + 1] = model
        else:
            result.extend(["-m", model])

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
        with open(log_path, "w") as log_file:
            process = subprocess.Popen(
                cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=str(cwd),
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
        click.echo(f"     | ERROR: {e}")
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
    click.echo(f"[{rid}] {name}  →  started")
    sys.stdout.flush()
    try:
        with open(log_path, "w") as log_file:
            proc = subprocess.Popen(
                cmd_args, stdout=log_file, stderr=subprocess.STDOUT,
                text=True, cwd=str(cwd),
            )
            proc.wait()
        ok = proc.returncode == 0
    except Exception as e:
        click.echo(f"[{rid}] ERROR: {e}")
        ok = False
    elapsed = (datetime.now() - start).total_seconds()
    status = "SUCCESS" if ok else "FAILED"
    click.echo(f"[{rid}] {name}  →  {status}  ({elapsed:.1f}s)  log: {log_path.name}")
    sys.stdout.flush()
    return {"id": rid, "name": name, "ok": ok, "elapsed": elapsed}


def print_summary(results: list[dict], start_all: datetime) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    total_elapsed = (datetime.now() - start_all).total_seconds()
    click.echo(f"\n=== Summary: {passed}/{total} passed  (total {total_elapsed:.1f}s) ===\n")
    click.echo(f"{'ID':<4}  {'Recipe':<28}  {'Status':<8}  {'Elapsed':>8}")
    click.echo("-" * 56)
    for r in results:
        s = "OK" if r["ok"] else "FAILED"
        click.echo(f"{r['id']:<4}  {r['name']:<28}  {s:<8}  {r['elapsed']:>7.1f}s")
    click.echo()


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.group()
def cli() -> None:
    """SPL 2.0 Cookbook batch runner."""


@cli.command("run")
@click.option("--adapter", "-a", default="", metavar="NAME",
              help="Override LLM adapter for all recipes (e.g. ollama, momagrid).")
@click.option("--model", "-m", default="", metavar="MODEL",
              help="Override model for all recipes.")
@click.option("--ids", default="", metavar="IDS",
              help="Comma-separated recipe IDs or ranges to run (e.g. '04,08,10-13').")
@click.option("--workers", "-w", default=0, type=int, metavar="N",
              help="Max parallel workers when using momagrid adapter (default: 5).")
@click.option("--category", default="", metavar="CAT",
              help="Only run recipes in this category.")
@click.option("--status", default="", metavar="STATUS",
              help="Only run recipes with this approval status.")
def cmd_run(adapter: str, model: str, ids: str, workers: int,
            category: str, status: str) -> None:
    """Run active cookbook recipes.

    When --adapter momagrid, recipes are submitted in parallel so the hub
    dispatcher sees multiple tasks queued simultaneously and can spread work
    across all registered agents.

    \b
    Examples:
      python run_all.py run
      python run_all.py run --adapter momagrid --model llama3.2
      python run_all.py run --adapter momagrid --workers 4
      python run_all.py run --ids 01,03,10-13
      python run_all.py run --category agentic
    """
    use_parallel = adapter == "momagrid"
    recipes = load_catalog()
    id_filter = parse_id_filter(ids) if ids else set()

    start_all = datetime.now()
    click.echo(f"=== SPL 2.0 Cookbook Batch Run — {start_all.strftime('%Y-%m-%d %H:%M:%S')} ===")
    overrides = []
    if adapter:
        overrides.append(f"adapter={adapter}")
    if model:
        overrides.append(f"model={model}")
    if overrides:
        click.echo(f"    Overrides : {', '.join(overrides)}")
    if use_parallel:
        click.echo("    Mode      : parallel (momagrid — recipes submitted concurrently)")
    click.echo()

    os.chdir(COOKBOOK_DIR)
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
                click.echo(f"[{rid}] {r['name']}  (skipping — {r.get('approval_status','').upper()})")
                continue
        cmd_args = apply_overrides(r["args"], adapter, model)
        log_path = COOKBOOK_DIR / r["dir"] / f"{r['log']}_{ts}.md"
        active.append((r, cmd_args, log_path))

    if not active:
        click.echo("No recipes to run.")
        return

    results: list[dict] = []

    if use_parallel:
        n_workers = workers or len(active)
        click.echo(f"Submitting {len(active)} recipe(s) with {n_workers} parallel worker(s)...\n")
        futures: dict = {}
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            for r, cmd_args, log_path in active:
                f = pool.submit(run_recipe_parallel, r, cmd_args, log_path, COOKBOOK_DIR)
                futures[f] = r
        for f in as_completed(futures):
            results.append(f.result())
        results.sort(key=lambda x: x["id"])
    else:
        for r, cmd_args, log_path in active:
            rid = r["id"]
            click.echo(f"[{rid}] {r['name']}")
            click.echo(f"     cmd : {' '.join(cmd_args)}")
            click.echo(f"     log : {log_path}")
            ok, elapsed = run_recipe_sequential(cmd_args, log_path, COOKBOOK_DIR)
            click.echo(f"     result: {'SUCCESS' if ok else 'FAILED'}  ({elapsed:.1f}s)\n")
            results.append({"id": rid, "name": r["name"], "ok": ok, "elapsed": elapsed})

    print_summary(results, start_all)


@cli.command("list")
@click.option("--category", default="", metavar="CAT", help="Filter by category.")
@click.option("--status", default="", metavar="STATUS", help="Filter by approval status.")
def cmd_list(category: str, status: str) -> None:
    """Print a brief recipe list.

    \b
    Examples:
      python run_all.py list
      python run_all.py list --category agentic
      python run_all.py list --status new
    """
    recipes = load_catalog()
    filtered = apply_filters(recipes, category, status)
    label = f" (category={category!r} status={status!r})" if (category or status) else ""
    click.echo(f"SPL 2.0 Cookbook — {len(filtered)} recipes{label}")
    for r in filtered:
        click.echo(
            f"  {r['id']:<4}  {status_marker(r)}  {r['name']:<28}  "
            f"{r.get('approval_status',''):<12}  {r.get('category',''):<14}  "
            f"{r.get('description','')}"
        )


@cli.command("catalog")
@click.option("--category", default="", metavar="CAT", help="Filter by category.")
@click.option("--status", default="", metavar="STATUS", help="Filter by approval status.")
def cmd_catalog(category: str, status: str) -> None:
    """Print the full recipe catalog table.

    \b
    Examples:
      python run_all.py catalog
      python run_all.py catalog --category reasoning
      python run_all.py catalog --status new
    """
    recipes = load_catalog()
    filtered = apply_filters(recipes, category, status)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    counts: dict[str, int] = {}
    for r in recipes:
        if r.get("is_active"):
            counts["active"] = counts.get("active", 0) + 1
        s = r.get("approval_status", "")
        counts[s] = counts.get(s, 0) + 1

    click.echo(f"=== SPL 2.0 Cookbook Catalog — {now} ===")
    if category or status:
        click.echo(f"    Filter: category={category!r}  status={status!r}  → {len(filtered)}/{len(recipes)} recipes\n")
    else:
        click.echo(
            f"    Total: {len(recipes)} recipes  |  {counts.get('active', 0)} active  |  "
            f"{counts.get(STATUS_NEW, 0)} new  |  {counts.get(STATUS_WIP, 0)} wip  |  "
            f"{counts.get(STATUS_DISABLED, 0)} disabled\n"
        )

    click.echo(f"{'ID':<4}  {'':2}  {'Name':<28}  {'Category':<14}  {'Status':<12}  Description")
    click.echo("-" * 110)
    for r in filtered:
        click.echo(
            f"{r['id']:<4}  {status_marker(r)}  {r['name']:<28}  "
            f"{r.get('category',''):<14}  {r.get('approval_status',''):<12}  "
            f"{r.get('description','')}"
        )

    click.echo()
    click.echo("Markers: ✅ active  🆕 new  🔧 wip  ⏸  disabled  ❌ rejected\n")
    click.echo("Run active recipes:           python run_all.py run")
    click.echo("Run specific recipe:          python run_all.py run --ids 05,11")
    click.echo("Run any (incl. inactive):     python run_all.py run --ids 17")
    click.echo("Override adapter/model:       python run_all.py run --adapter momagrid --model llama3.2")
    click.echo("Filter catalog by category:   python run_all.py catalog --category agentic")
    click.echo("Filter catalog by status:     python run_all.py catalog --status new")

    cat_counts: dict[str, int] = {}
    for r in recipes:
        c = r.get("category", "")
        cat_counts[c] = cat_counts.get(c, 0) + 1
    parts = [f"{c}({n})" for c, n in sorted(cat_counts.items())]
    click.echo(f"\nCategories: {'  '.join(parts)}")


if __name__ == "__main__":
    cli()
