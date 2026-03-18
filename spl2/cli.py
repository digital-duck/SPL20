"""SPL 2.0 Command-Line Interface.

Usage examples:
    spl2 init
    spl2 validate query.spl
    spl2 syntax   query.spl
    spl2 explain  query.spl
    spl2 run      query.spl --adapter ollama -p task="Write a haiku"
    spl2 execute  query.spl --adapter momagrid --cache
    spl2 adapters
    spl2 memory list
    spl2 memory get  <key>
    spl2 memory set  <key> <value>
    spl2 memory delete <key>
    spl2 rag add   "document text"
    spl2 rag query "search text" --top-k 5
    spl2 rag count
    spl2 version
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import click

from spl2 import __version__


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_file(filepath: str) -> str:
    """Read a file and raise ClickException if not found."""
    path = Path(filepath)
    if not path.exists():
        raise click.ClickException(f"File not found: {filepath}")
    return path.read_text(encoding="utf-8")


def _parse_params(raw: tuple[str, ...]) -> dict[str, str]:
    """Parse KEY=VALUE tuples into a dict."""
    params: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise click.BadParameter(
                f"Expected KEY=VALUE, got: {item!r}", param_hint="-p/--param"
            )
        key, value = item.split("=", 1)
        params[key.strip()] = value.strip()
    return params


def _ensure_workspace(storage_dir: str = ".spl") -> bool:
    """Create workspace directory and memory DB if they don't exist."""
    if os.path.exists(storage_dir):
        return False
    os.makedirs(storage_dir, exist_ok=True)
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    store.close()
    return True


def _parse_source(source: str):
    """Lex → Parse → return AST."""
    from spl2.lexer import Lexer
    from spl2.parser import Parser
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def _analyze_source(source: str):
    """Lex → Parse → Analyze → return AnalysisResult."""
    from spl2.analyzer import Analyzer
    ast = _parse_source(source)
    return Analyzer().analyze(ast)


def _print_result(result) -> None:
    """Pretty-print an SPLResult or WorkflowResult."""
    from spl2.executor import SPLResult, WorkflowResult

    if isinstance(result, SPLResult):
        click.echo("=" * 60)
        click.echo(f"Model: {result.model}")
        click.echo(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
        click.echo(f"Latency: {result.latency_ms:.0f}ms")
        if result.cost_usd is not None:
            click.echo(f"Cost: ${result.cost_usd:.6f}")
        click.echo("-" * 60)
        click.echo(result.content)
        click.echo("=" * 60)
    elif isinstance(result, WorkflowResult):
        click.echo("=" * 60)
        click.echo(f"Status: {result.status}")
        click.echo(f"LLM Calls: {result.total_llm_calls}")
        click.echo(f"Tokens: {result.total_input_tokens} in / {result.total_output_tokens} out")
        click.echo(f"Latency: {result.total_latency_ms:.0f}ms")
        if result.committed_value:
            click.echo("-" * 60)
            click.echo(f"Committed: {result.committed_value}")
        if result.output:
            click.echo("-" * 60)
            click.echo("Variables:")
            for k, v in result.output.items():
                val_preview = v[:200] if len(v) > 200 else v
                click.echo(f"  @{k} = {val_preview}")
        click.echo("=" * 60)


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="spl2")
def cli() -> None:
    """SPL 2.0 — Structured Prompt Language.  SQL for Agentic Workflow Orchestration."""


# ── spl2 init ─────────────────────────────────────────────────────────────────

@cli.command("init")
def cmd_init() -> None:
    """Initialise .spl/ workspace in the current directory."""
    if _ensure_workspace(".spl"):
        click.echo(f"Initialised SPL workspace in {os.path.abspath('.spl')}/")
        click.echo("  .spl/memory.db  — persistent memory store")
    else:
        click.echo("Workspace already exists: .spl/")


# ── spl2 validate / syntax ───────────────────────────────────────────────────

@cli.command("validate")
@click.argument("file", type=click.Path(dir_okay=False))
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output AST as JSON.")
def cmd_validate(file: str, as_json: bool) -> None:
    """Parse and validate FILE without executing."""
    source = _read_file(file)
    try:
        ast = _parse_source(source)
        if as_json:
            from spl2.ir import ast_to_json
            click.echo(json.dumps(ast_to_json(ast), indent=2))
        else:
            from spl2.analyzer import Analyzer
            analysis = Analyzer().analyze(ast)
            click.echo(f"Parsed OK: {len(ast.statements)} statement(s)")
            for stmt in ast.statements:
                kind = type(stmt).__name__.replace("Statement", "")
                name = getattr(stmt, "name", "")
                click.echo(f"  - {kind}: {name}")
            if analysis.warnings:
                click.echo(f"\nWarnings ({len(analysis.warnings)}):")
                for w in analysis.warnings:
                    click.echo(f"  ! {w}")
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# Register aliases: parse, syntax
cli.add_command(cmd_validate, name="parse")
cli.add_command(cmd_validate, name="syntax")


# ── spl2 explain ──────────────────────────────────────────────────────────────

@cli.command("explain")
@click.argument("file", type=click.Path(dir_okay=False))
def cmd_explain(file: str) -> None:
    """Show execution plan for FILE (no LLM call)."""
    source = _read_file(file)
    try:
        from spl2.optimizer import Optimizer
        from spl2.explain import explain_plans

        analysis = _analyze_source(source)
        plans = Optimizer().optimize(analysis)
        click.echo(explain_plans(plans))
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# ── spl2 execute / run ────────────────────────────────────────────────────────

@cli.command("execute", context_settings={"ignore_unknown_options": True})
@click.argument("file", type=click.Path(dir_okay=False))
@click.option("--adapter", default="echo", show_default=True, metavar="NAME",
              help="LLM adapter engine.")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Override USING MODEL for all statements (e.g. gemma3, llama3.2).")
@click.option("--param", "-p", multiple=True, metavar="KEY=VALUE",
              help="Pass parameter (repeatable).")
@click.option("--cache", is_flag=True, default=False,
              help="Enable prompt caching.")
@click.option("--storage-dir", default=".spl", show_default=True,
              help="Storage directory for memory/cache.")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def cmd_execute(file: str, adapter: str, model: str | None,
                param: tuple[str, ...],
                cache: bool, storage_dir: str,
                extra_args: tuple[str, ...]) -> None:
    """Execute FILE and print each PROMPT/WORKFLOW result.

    Parameters can be passed with -p KEY=VALUE or as trailing KEY=VALUE args:

    \b
      spl2 run query.spl -p question="What is SPL?"
      spl2 run query.spl question="What is SPL?"
      spl2 run query.spl --adapter ollama --model gemma3 question="hello"
    """
    source = _read_file(file)
    params = _parse_params(param + extra_args)

    _ensure_workspace(storage_dir)

    try:
        from spl2.executor import Executor
        from spl2.ast_nodes import PromptStatement

        ast = _parse_source(source)

        # Override model on all PROMPT statements if --model is given
        if model:
            for stmt in ast.statements:
                if isinstance(stmt, PromptStatement):
                    stmt.model = model

        from spl2.analyzer import Analyzer
        analysis = Analyzer().analyze(ast)

        executor = Executor(
            adapter_name=adapter,
            storage_dir=storage_dir,
            cache_enabled=cache,
        )
        try:
            results = asyncio.run(executor.execute_program(analysis, params=params))
            for result in results:
                _print_result(result)
        finally:
            executor.close()
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


# Register alias: run
cli.add_command(cmd_execute, name="run")


# ── spl2 adapters ─────────────────────────────────────────────────────────────

@cli.command("adapters")
def cmd_adapters() -> None:
    """List available LLM adapter engines."""
    from spl2.adapters import list_adapters

    adapters_info = {
        "echo": "Returns prompt as response (testing, no setup required)",
        "claude_cli": "Wraps claude -p CLI (requires Claude Code installed)",
        "openrouter": "100+ models via OpenRouter.ai (requires httpx, OPENROUTER_API_KEY)",
        "ollama": "Local models via Ollama (requires httpx, ollama running)",
        "momagrid": "Decentralized AI inference grid (requires httpx, MOMAGRID_HUB_URL)",
    }

    available = list_adapters()
    click.echo(f"Available LLM adapters ({len(available)}):\n")
    for name in sorted(available):
        desc = adapters_info.get(name, "")
        click.echo(f"  {name:<14} {desc}")
    click.echo(f"\nUsage: spl2 run <file.spl> --adapter <name>")


# ── spl2 memory ───────────────────────────────────────────────────────────────

@cli.group("memory")
def cmd_memory() -> None:
    """Manage the SPL persistent memory store (.spl/memory.db)."""


@cmd_memory.command("list")
@click.option("--storage-dir", default=".spl", show_default=True)
def memory_list(storage_dir: str) -> None:
    """List all memory keys."""
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    keys = store.list_keys()
    if not keys:
        click.echo("(empty)")
    else:
        for key in keys:
            val = store.get(key)
            preview = (val[:80] + "...") if val and len(val) > 80 else val
            click.echo(f"  {key} = {preview}")
    store.close()


@cmd_memory.command("get")
@click.argument("key")
@click.option("--storage-dir", default=".spl", show_default=True)
def memory_get(key: str, storage_dir: str) -> None:
    """Print the value stored under KEY."""
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    value = store.get(key)
    store.close()
    if value is not None:
        click.echo(value)
    else:
        raise click.ClickException(f"Key not found: {key}")


@cmd_memory.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--storage-dir", default=".spl", show_default=True)
def memory_set(key: str, value: str, storage_dir: str) -> None:
    """Store VALUE under KEY."""
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    store.set(key, value)
    store.close()
    click.echo(f"Set: {key}")


@cmd_memory.command("delete")
@click.argument("key")
@click.option("--storage-dir", default=".spl", show_default=True)
def memory_delete(key: str, storage_dir: str) -> None:
    """Delete KEY from the memory store."""
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    deleted = store.delete(key)
    store.close()
    if deleted:
        click.echo(f"Deleted: {key}")
    else:
        raise click.ClickException(f"Key not found: {key}")


# ── spl2 rag ──────────────────────────────────────────────────────────────────

@cli.group("rag")
def cmd_rag() -> None:
    """Manage the SPL vector store for RAG (.spl/vectors)."""


@cmd_rag.command("add")
@click.argument("text")
@click.option("--storage-dir", default=".spl", show_default=True)
def rag_add(text: str, storage_dir: str) -> None:
    """Add TEXT to the vector store."""
    from spl2.storage import get_vector_store
    store = get_vector_store("faiss", storage_dir)
    doc_id = store.add(text)
    click.echo(f"Added document (id={doc_id}), total: {store.count()}")
    store.close()


@cmd_rag.command("query")
@click.argument("query")
@click.option("--top-k", default=5, show_default=True, metavar="N",
              help="Number of results to return.")
@click.option("--storage-dir", default=".spl", show_default=True)
def rag_query(query: str, top_k: int, storage_dir: str) -> None:
    """Search the vector store for QUERY."""
    from spl2.storage import get_vector_store
    store = get_vector_store("faiss", storage_dir)
    results = store.query(query, top_k=top_k)
    store.close()
    if not results:
        click.echo("No results found.")
    else:
        for i, r in enumerate(results, 1):
            score = r.get("score", 0)
            text = r.get("text", "")
            preview = (text[:120] + "...") if len(text) > 120 else text
            click.echo(f"  {i}. [score={score:.4f}] {preview}")


@cmd_rag.command("count")
@click.option("--storage-dir", default=".spl", show_default=True)
def rag_count(storage_dir: str) -> None:
    """Show the number of indexed documents."""
    from spl2.storage import get_vector_store
    store = get_vector_store("faiss", storage_dir)
    n = store.count()
    store.close()
    click.echo(f"Documents indexed: {n}")


# ── spl2 version ──────────────────────────────────────────────────────────────

@cli.command("version")
def cmd_version() -> None:
    """Print the SPL engine version."""
    click.echo(f"spl2 {__version__}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Setuptools entry-point: delegates to the click CLI group."""
    cli()


if __name__ == "__main__":
    main()
