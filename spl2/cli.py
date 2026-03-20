"""SPL 2.0 Command-Line Interface.

Usage examples:
    spl2 init
    spl2 validate query.spl
    spl2 syntax   query.spl
    spl2 explain  query.spl
    spl2 run      query.spl --adapter ollama -p task="Write a haiku"
    spl2 execute  query.spl --adapter momagrid --cache
    spl2 text2spl "summarize a document" --adapter ollama
    spl2 compile  "build a review agent" --adapter ollama --execute
    spl2 config show
    spl2 config set adapter ollama
    spl2 config get adapter
    spl2 config init
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
from datetime import datetime
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


def _get_cfg():
    """Load SPL config (lazy, cached per process)."""
    from spl2.config import load_config
    return load_config()


def _cfg_default(key: str, fallback):
    """Get a config value, returning fallback if missing."""
    try:
        cfg = _get_cfg()
        return cfg.get(key, fallback)
    except Exception:
        return fallback


def _setup_logging(run_name: str, adapter: str = "", spl_file: str = ""):
    """Set up dd-logging for the current run. Returns log file path."""
    from dd_logging import setup_logging
    from spl2.config import LOG_DIR

    # Build a descriptive run_name from the spl file
    if spl_file:
        stem = Path(spl_file).stem
        run_name = stem

    log_level = _cfg_default("log_level", "info")
    console = _cfg_default("log_console", False)

    log_path = setup_logging(
        run_name=run_name,
        root_name="spl2",
        adapter=adapter,
        log_level=log_level,
        log_dir=str(LOG_DIR),
        console=console,
    )
    return log_path


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
        click.echo(f"```output\n{result.content}\n```")
        click.echo("=" * 60)
    elif isinstance(result, WorkflowResult):
        click.echo("=" * 60)
        click.echo(f"Status: {result.status}")
        click.echo(f"LLM Calls: {result.total_llm_calls}")
        click.echo(f"Tokens: {result.total_input_tokens} in / {result.total_output_tokens} out")
        click.echo(f"Latency: {result.total_latency_ms:.0f}ms")
        if result.committed_value:
            click.echo("-" * 60)
            click.echo(f"```output\n{result.committed_value}\n```")
        # Show intermediate variables: skip empty values and skip any variable
        # whose value duplicates the committed output (already shown above).
        intermediate = {
            k: v for k, v in result.output.items()
            if v and v != result.committed_value
        }
        if intermediate:
            click.echo("-" * 60)
            click.echo("Variables:")
            for k, v in intermediate.items():
                click.echo(f"  @{k} = {v}")
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

    # Also ensure ~/.spl/config.yaml exists
    from spl2.config import ensure_defaults, CONFIG_PATH
    ensure_defaults()
    click.echo(f"  Config: {CONFIG_PATH}")


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
@click.option("--adapter", default=None, metavar="NAME",
              help="LLM adapter engine (default from config or 'echo').")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Override USING MODEL for all statements (e.g. gemma3, llama3.2).")
@click.option("--param", "-p", multiple=True, metavar="KEY=VALUE",
              help="Pass parameter (repeatable).")
@click.option("--cache/--no-cache", default=None,
              help="Enable/disable prompt caching (default from config).")
@click.option("--storage-dir", default=None, show_default=True,
              help="Storage directory for memory/cache (default from config or '.spl').")
@click.option("--allowed-tools", default=None, metavar="TOOLS",
              help="Comma-separated tools for claude_cli adapter (e.g. WebSearch,Bash).")
@click.option("--tools", "tools_module", default=None, metavar="FILE",
              help="Python module to load as CALL-able tools (e.g. tools/my_tools.py).")
@click.option("--timeout", default=None, type=int, metavar="SECONDS",
              help="Per-call timeout in seconds (default: 600 with --allowed-tools, 300 otherwise).")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def cmd_execute(file: str, adapter: str | None, model: str | None,
                param: tuple[str, ...],
                cache: bool | None, storage_dir: str | None,
                allowed_tools: str | None,
                tools_module: str | None,
                timeout: int | None,
                extra_args: tuple[str, ...]) -> None:
    """Execute FILE and print each PROMPT/WORKFLOW result.

    Parameters can be passed with -p KEY=VALUE or as trailing KEY=VALUE args:

    \b
      spl2 run query.spl -p question="What is SPL?"
      spl2 run query.spl question="What is SPL?"
      spl2 run query.spl --adapter ollama --model gemma3 question="hello"
    """
    # Apply config defaults
    adapter = adapter or _cfg_default("adapter", "echo")
    model = model or _cfg_default("model", None) or None
    cache = cache if cache is not None else _cfg_default("cache", False)
    storage_dir = storage_dir or _cfg_default("storage_dir", ".spl")

    source = _read_file(file)
    params = _parse_params(param + extra_args)

    # Print the invocation and script source for easy review / log readability
    cmd_parts = ["spl2", "run", file, "--adapter", adapter]
    if model:
        cmd_parts += ["-m", model]
    cmd_parts += [f"{k}={v}" for k, v in params.items()]
    click.echo(f"\n```bash\n{' '.join(cmd_parts)}\n```\n")
    if "prompt" in params:
        click.echo(f"```prompt\n{params['prompt']}\n```\n")
    click.echo(f"```spl2\n{source.rstrip()}\n```\n")

    _ensure_workspace(storage_dir)

    # Set up logging
    log_path = _setup_logging(run_name="run", adapter=adapter, spl_file=file)

    from dd_logging import get_logger
    log = get_logger("cli", "spl2")
    log.info("spl2 run %s --adapter %s %s", file, adapter,
             f"-m {model}" if model else "")

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

        cache_ttl = _cfg_default("cache_ttl", 3600)
        adapter_kwargs = {}
        if allowed_tools:
            adapter_kwargs["allowed_tools"] = [t.strip() for t in allowed_tools.split(",")]
        if timeout is not None:
            adapter_kwargs["timeout"] = timeout
        executor = Executor(
            adapter_name=adapter,
            adapter_kwargs=adapter_kwargs,
            storage_dir=storage_dir,
            cache_enabled=cache,
            cache_ttl=cache_ttl,
        )
        if tools_module:
            from spl2.tools import load_tools_module
            loaded = load_tools_module(tools_module)
            for tool_name, tool_fn in loaded.items():
                executor.register_tool(tool_name, tool_fn)
            log.info("Loaded %d tool(s) from %s", len(loaded), tools_module)
        try:
            results = asyncio.run(executor.execute_program(analysis, params=params))
            for result in results:
                _print_result(result)
                log.info("Result: model=%s tokens=%d latency=%.0fms",
                         getattr(result, "model", ""),
                         getattr(result, "total_tokens", 0) or
                         getattr(result, "total_input_tokens", 0) +
                         getattr(result, "total_output_tokens", 0),
                         getattr(result, "latency_ms", 0) or
                         getattr(result, "total_latency_ms", 0))
        finally:
            executor.close()
    except click.ClickException:
        raise
    except Exception as exc:
        log.exception("Execution failed: %s", exc)
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Log: {log_path}", err=True)


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
        "anthropic": "Claude models via Anthropic API (requires anthropic, ANTHROPIC_API_KEY)",
        "openai": "GPT/o-series via OpenAI API (requires openai, OPENAI_API_KEY)",
        "google": "Gemini models via Google GenAI (requires google-genai, GOOGLE_API_KEY)",
        "deepseek": "DeepSeek models (requires httpx, DEEPSEEK_API_KEY)",
        "qwen": "Qwen models via DashScope (requires httpx, DASHSCOPE_API_KEY)",
    }

    available = list_adapters()
    click.echo(f"Available LLM adapters ({len(available)}):\n")
    for name in sorted(available):
        desc = adapters_info.get(name, "")
        click.echo(f"  {name:<14} {desc}")
    click.echo(f"\nUsage: spl2 run <file.spl> --adapter <name>")


# ── spl2 config ──────────────────────────────────────────────────────────────

@cli.group("config")
def cmd_config() -> None:
    """Manage SPL 2.0 configuration (~/.spl/config.yaml)."""


@cmd_config.command("show")
def config_show() -> None:
    """Show current configuration."""
    from spl2.config import load_config, CONFIG_PATH
    import yaml

    cfg = load_config()
    click.echo(f"# {CONFIG_PATH}")
    click.echo(yaml.dump(cfg.to_dict(), default_flow_style=False, sort_keys=False))


@cmd_config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value (supports dot-path like 'adapters.ollama.timeout')."""
    from spl2.config import load_config

    cfg = load_config()
    value = cfg.get(key)
    if value is None:
        raise click.ClickException(f"Key not found: {key}")
    if isinstance(value, dict):
        import yaml
        click.echo(yaml.dump(value, default_flow_style=False, sort_keys=False))
    else:
        click.echo(value)


@cmd_config.command("set", context_settings={"ignore_unknown_options": True})
@click.argument("pairs", nargs=-1, required=True)
def config_set(pairs: tuple[str, ...]) -> None:
    """Set configuration value(s). Supports KEY VALUE or KEY=VALUE syntax.

    \b
    Examples:
      spl2 config set adapter ollama
      spl2 config set adapter ollama model gemma3
      spl2 config set adapters.ollama.timeout 300
      spl2 config set adapter=ollama model=gemma3
    """
    from spl2.config import load_config, save_config

    cfg = load_config()

    # Parse pairs: support both "key value" and "key=value" syntax
    kvs: list[tuple[str, str]] = []
    i = 0
    args = list(pairs)
    while i < len(args):
        if "=" in args[i]:
            k, v = args[i].split("=", 1)
            kvs.append((k.strip(), v.strip()))
            i += 1
        elif i + 1 < len(args) and "=" not in args[i + 1]:
            kvs.append((args[i], args[i + 1]))
            i += 2
        elif i + 1 < len(args):
            # Next arg has '=', so current is a key without a value
            raise click.UsageError(f"Missing value for key: {args[i]}")
        else:
            raise click.UsageError(
                f"Missing value for key: {args[i]}\n"
                f"Usage: spl2 config set KEY VALUE [KEY VALUE ...]\n"
                f"   or: spl2 config set KEY=VALUE [KEY=VALUE ...]"
            )

    for key, value in kvs:
        # Auto-detect types
        if value.lower() == "true":
            typed_value: str | bool | int | float = True
        elif value.lower() == "false":
            typed_value = False
        elif value.isdigit():
            typed_value = int(value)
        else:
            try:
                typed_value = float(value)
            except ValueError:
                typed_value = value

        cfg[key] = typed_value
        click.echo(f"Set {key} = {typed_value}")

    save_config(cfg)


@cmd_config.command("init")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing config with defaults.")
def config_init(force: bool) -> None:
    """Create ~/.spl/config.yaml with smart defaults."""
    from spl2.config import CONFIG_PATH, save_config, DEFAULTS, SPL_HOME
    from dd_config import Config

    if CONFIG_PATH.exists() and not force:
        click.echo(f"Config already exists: {CONFIG_PATH}")
        click.echo("Use --force to overwrite with defaults.")
        return

    SPL_HOME.mkdir(parents=True, exist_ok=True)
    cfg = Config.from_dict(DEFAULTS)
    save_config(cfg)
    click.echo(f"Created {CONFIG_PATH} with defaults")


@cmd_config.command("path")
def config_path() -> None:
    """Print the config file path."""
    from spl2.config import CONFIG_PATH, LOG_DIR
    click.echo(f"Config: {CONFIG_PATH}")
    click.echo(f"Logs:   {LOG_DIR}")


@cmd_config.command("reset")
@click.argument("key")
def config_reset(key: str) -> None:
    """Reset a configuration key to its default value."""
    from spl2.config import load_config, save_config, DEFAULTS
    from dd_config import Config

    defaults = Config.from_dict(DEFAULTS)
    default_val = defaults.get(key)
    if default_val is None:
        raise click.ClickException(f"No default for key: {key}")

    cfg = load_config()
    cfg[key] = default_val
    save_config(cfg)
    click.echo(f"Reset {key} = {default_val}")


# ── spl2 cache ────────────────────────────────────────────────────────────────

@cli.group("cache")
def cmd_cache() -> None:
    """Manage the prompt cache (.spl/memory.db)."""


@cmd_cache.command("list")
@click.option("--storage-dir", default=None, show_default=True)
def cache_list(storage_dir: str | None) -> None:
    """List cached prompts."""
    storage_dir = storage_dir or _cfg_default("storage_dir", ".spl")
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    rows = store._conn.execute(
        "SELECT prompt_hash, model, tokens_used, created_at, expires_at "
        "FROM prompt_cache ORDER BY created_at DESC"
    ).fetchall()
    store.close()
    if not rows:
        click.echo("(empty)")
        return
    for r in rows:
        expired = ""
        if r["expires_at"]:
            from datetime import datetime
            try:
                # Handle both ISO format and SQLite format
                exp_str = r["expires_at"].replace("T", " ")
                exp = datetime.strptime(exp_str[:19], "%Y-%m-%d %H:%M:%S")
                if exp < datetime.utcnow():
                    expired = " [EXPIRED]"
            except (ValueError, TypeError):
                pass
        click.echo(
            f"  {r['prompt_hash'][:12]}...  model={r['model']}  "
            f"tokens={r['tokens_used']}  created={r['created_at']}"
            f"  expires={r['expires_at'] or 'never'}{expired}"
        )
    click.echo(f"\nTotal: {len(rows)} cached entries")


@cmd_cache.command("clear")
@click.option("--storage-dir", default=None, show_default=True)
@click.option("--expired-only", is_flag=True, default=False,
              help="Only clear expired entries.")
def cache_clear(storage_dir: str | None, expired_only: bool) -> None:
    """Clear the prompt cache."""
    storage_dir = storage_dir or _cfg_default("storage_dir", ".spl")
    from spl2.storage.memory import MemoryStore
    store = MemoryStore(os.path.join(storage_dir, "memory.db"))
    if expired_only:
        cursor = store._conn.execute(
            "DELETE FROM prompt_cache WHERE expires_at IS NOT NULL "
            "AND expires_at < CURRENT_TIMESTAMP"
        )
    else:
        cursor = store._conn.execute("DELETE FROM prompt_cache")
    store._conn.commit()
    store.close()
    label = "expired " if expired_only else ""
    click.echo(f"Cleared {cursor.rowcount} {label}cache entries")


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
@click.option("--chunk/--no-chunk", default=None,
              help="Split file into paragraphs and index each separately. "
                   "Auto-enabled when TEXT is a file path.")
def rag_add(text: str, storage_dir: str, chunk: bool | None) -> None:
    """Add TEXT (or a file path) to the vector store.

    When TEXT is a file path, the file is read automatically.
    Paragraph chunking is enabled by default for files (use --no-chunk to disable).
    """
    import os, re
    from spl2.storage import get_vector_store

    if os.path.isfile(text):
        with open(text, "r", encoding="utf-8") as f:
            content = f.read()
        click.echo(f"Reading file: {text} ({len(content):,} chars)")
        do_chunk = chunk if chunk is not None else True  # default ON for files
    else:
        content = text
        do_chunk = chunk or False  # default OFF for inline text

    store = get_vector_store("faiss", storage_dir)

    if do_chunk:
        chunks = [c.strip() for c in re.split(r"\n{2,}", content) if c.strip()]
        ids = store.add_batch(chunks)
        click.echo(f"Indexed {len(ids)} paragraphs (model: {store.model_name}), total: {store.count()}")
    else:
        doc_id = store.add(content)
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


# ── spl2 code-rag ────────────────────────────────────────────────────────────

@cli.group("code-rag")
def cmd_code_rag() -> None:
    """Manage the Code-RAG store for text2SPL generation (.spl/code_rag)."""


def _get_code_rag_store(storage_dir: str | None = None, collection: str | None = None):
    """Return a CodeRAGStore using config defaults."""
    from spl2.code_rag import CodeRAGStore
    sd  = storage_dir or _cfg_default("code_rag.storage_dir", ".spl/code_rag")
    col = collection  or _cfg_default("code_rag.collection",  CodeRAGStore.COLLECTION_NAME)
    return CodeRAGStore(storage_dir=sd, collection_name=col)


@cmd_code_rag.command("import")
@click.option("--cookbook-dir", default="./cookbook", show_default=True,
              help="Import all cookbook recipes (default source).")
@click.option("--catalog", default=None, metavar="FILE",
              help="Path to cookbook_catalog.json (default: <cookbook-dir>/cookbook_catalog.json).")
@click.option("--from", "from_file", default=None, metavar="FILE",
              help="Import (description, SPL) pairs from a JSONL file instead of cookbook.")
@click.option("--source", default="external", show_default=True,
              help="Provenance tag for JSONL imports (e.g. 'research', 'synthetic').")
@click.option("--validate/--no-validate", default=True, show_default=True,
              help="Validate each SPL pair before importing (JSONL mode only).")
@click.option("--storage-dir", default=None, help="Code-RAG DB directory (default from config).")
def code_rag_import(cookbook_dir: str, catalog: str | None, from_file: str | None,
                    source: str, validate: bool, storage_dir: str | None) -> None:
    """Prime the Code-RAG store with (description, SPL) pairs.

    Without --from: imports all cookbook recipes (run this first to prime the DB).

    \b
      spl2 code-rag import
      spl2 code-rag import --cookbook-dir /path/to/cookbook

    With --from FILE: bulk-imports pairs from a JSONL file. Each line must be:

    \b
      {"description": "summarize a PDF", "spl_source": "PROMPT ..."}

    Optional fields: name, category, source. Or reference an external file:

    \b
      {"description": "...", "spl_file": "./my_recipe.spl"}

    The JSONL format matches `spl2 code-rag export` output exactly, so
    exported pairs can be re-imported into another project or after a DB reset.

    \b
      spl2 code-rag import --from ./my_pairs.jsonl
      spl2 code-rag import --from ./my_pairs.jsonl --source synthetic --no-validate
    """
    store = _get_code_rag_store(storage_dir)

    if from_file:
        # ── JSONL import ──────────────────────────────────────────────────
        from spl2.text2spl import Text2SPL
        path = Path(from_file)
        if not path.exists():
            raise click.ClickException(f"File not found: {from_file}")

        added = skipped = invalid = 0
        with path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    click.echo(f"  line {lineno}: JSON parse error — {exc}", err=True)
                    skipped += 1
                    continue

                description = record.get("description", "").strip()
                if not description:
                    click.echo(f"  line {lineno}: missing 'description' — skipped", err=True)
                    skipped += 1
                    continue

                spl_source = record.get("spl_source", "").strip()
                if not spl_source:
                    spl_file_ref = record.get("spl_file", "").strip()
                    if spl_file_ref:
                        ref = Path(spl_file_ref)
                        if not ref.exists():
                            click.echo(f"  line {lineno}: spl_file not found: {spl_file_ref} — skipped", err=True)
                            skipped += 1
                            continue
                        spl_source = ref.read_text(encoding="utf-8").strip()
                    else:
                        click.echo(f"  line {lineno}: missing 'spl_source' or 'spl_file' — skipped", err=True)
                        skipped += 1
                        continue

                if validate:
                    valid, message = Text2SPL.validate_output(spl_source)
                    if not valid:
                        click.echo(f"  line {lineno}: invalid SPL ({message}) — skipped", err=True)
                        invalid += 1
                        continue

                meta = {
                    "name":     record.get("name", ""),
                    "category": record.get("category", ""),
                    "source":   record.get("source", source),
                }
                store.add_pair(description=description, spl_source=spl_source, metadata=meta)
                added += 1

        click.echo(f"Imported {added} pair(s)  |  skipped {skipped}  |  invalid {invalid}")

    else:
        # ── Cookbook import ───────────────────────────────────────────────
        click.echo(f"Importing cookbook recipes from {cookbook_dir} ...")
        added = store.index_recipes(cookbook_dir=cookbook_dir, catalog_path=catalog)
        if added == 0 and store.count() > 0:
            click.echo("(All recipes already imported — nothing to do)")
        else:
            click.echo(f"Imported {added} new recipe(s).")

    click.echo(f"Total in store: {store.count()}")


# Alias for discoverability
cmd_code_rag.add_command(code_rag_import, name="index")


@cmd_code_rag.command("add")
@click.argument("description")
@click.argument("spl_file", type=click.Path(dir_okay=False))
@click.option("--storage-dir", default=None, help="Code-RAG DB directory (default from config).")
def code_rag_add(description: str, spl_file: str, storage_dir: str | None) -> None:
    """Add a (DESCRIPTION, SPL_FILE) pair to the Code-RAG store."""
    spl_source = _read_file(spl_file)
    store = _get_code_rag_store(storage_dir)
    doc_id = store.add_pair(description=description, spl_source=spl_source,
                            metadata={"source": "manual", "file": spl_file})
    click.echo(f"Added pair (id={doc_id}).  Total in store: {store.count()}")


@cmd_code_rag.command("query")
@click.argument("description")
@click.option("--top-k", default=4, show_default=True, help="Number of results.")
@click.option("--storage-dir", default=None, help="Code-RAG DB directory (default from config).")
@click.option("--show-spl", is_flag=True, default=False, help="Print full SPL source for each hit.")
def code_rag_query(description: str, top_k: int, storage_dir: str | None, show_spl: bool) -> None:
    """Retrieve the top-k most similar SPL examples for DESCRIPTION."""
    store = _get_code_rag_store(storage_dir)
    hits = store.retrieve(description, top_k=top_k)
    if not hits:
        click.echo("No results (store may be empty — run: spl2 code-rag index)")
        return
    for i, h in enumerate(hits, 1):
        label = h["name"] or h["description"][:60]
        click.echo(f"\n{i}. [{h['source']}]  score={h['score']:.4f}  {label}")
        click.echo(f"   {h['description']}")
        if show_spl:
            click.echo(f"\n```spl2\n{h['spl_source']}\n```")


@cmd_code_rag.command("count")
@click.option("--storage-dir", default=None, help="Code-RAG DB directory (default from config).")
def code_rag_count(storage_dir: str | None) -> None:
    """Show the number of (description, SPL) pairs in the Code-RAG store."""
    store = _get_code_rag_store(storage_dir)
    click.echo(f"Code-RAG pairs indexed: {store.count()}")


@cmd_code_rag.command("export")
@click.option("--output", "-o", default=".spl/code_rag/training_data.jsonl", show_default=True,
              help="Output JSONL file path.")
@click.option("--storage-dir", default=None, help="Code-RAG DB directory (default from config).")
def code_rag_export(output: str, storage_dir: str | None) -> None:
    """Export all pairs as JSONL for model fine-tuning."""
    store = _get_code_rag_store(storage_dir)
    n = store.export_jsonl(output)
    click.echo(f"Exported {n} pair(s) to {output}")


def _parse_log_for_pairs(text: str) -> list[dict]:
    """Extract (command, spl_source) pairs from a spl2 run log.

    Scans for ```bash and ```spl2 fence blocks and pairs them in order.
    Works on both per-recipe log files (clean) and tee'd run_all.py output
    (which prefixes normal lines with '     | ').
    """
    import re

    # Normalise: strip the '     | ' run_all.py prefix so both formats parse identically.
    # Pattern: optional leading whitespace + '|' + optional space at start of line.
    prefix_re = re.compile(r'^\s*\|\s?', re.MULTILINE)
    # Only strip if the majority of lines have the prefix (tee'd output)
    prefixed_lines = len(prefix_re.findall(text))
    total_lines = text.count("\n") + 1
    if total_lines > 0 and prefixed_lines / total_lines > 0.3:
        text = prefix_re.sub("", text)

    fence_re = re.compile(
        r'^[ \t]*```(\w+)\n(.*?)\n[ \t]*```',
        re.MULTILINE | re.DOTALL,
    )
    pairs: list[dict] = []
    pending_bash: str | None = None
    pending_prompt: str | None = None
    for m in fence_re.finditer(text):
        lang    = m.group(1)
        content = m.group(2).strip()
        if lang == "bash":
            pending_bash = content
            pending_prompt = None
        elif lang == "prompt" and pending_bash is not None:
            pending_prompt = content
        elif lang in ("spl2", "spl") and pending_bash is not None:
            pairs.append({
                "command": pending_bash,
                "prompt": pending_prompt,
                "spl_source": content,
            })
            pending_bash = None
            pending_prompt = None
        elif lang == "output":
            pending_bash = None
            pending_prompt = None
    return pairs


def _load_catalog_map(cookbook_dir: str) -> dict[str, str]:
    """Return {recipe_dir_or_stem → description} from cookbook catalog."""
    try:
        catalog_path = Path(cookbook_dir) / "cookbook_catalog.json"
        with catalog_path.open(encoding="utf-8") as f:
            catalog = json.load(f)
        result: dict[str, str] = {}
        for recipe in catalog.get("recipes", []):
            desc = recipe.get("description", "").strip()
            if not desc:
                continue
            # Key by relative recipe dir (e.g. "01_hello_world")
            d = recipe.get("dir", "")
            if d:
                result[d] = desc
                result[d.lstrip("0123456789_")] = desc  # also without leading id
        return result
    except Exception:
        return {}


def _description_from_spl(spl_source: str) -> str:
    """Derive a description from a PROMPT or WORKFLOW name in SPL source."""
    import re
    m = re.search(r'\b(?:PROMPT|WORKFLOW)\s+(\w+)', spl_source, re.IGNORECASE)
    if m:
        return m.group(1).replace("_", " ")
    return ""


def _description_from_command(cmd: str, catalog_map: dict[str, str]) -> str:
    """Derive a description from a `spl2 run <file>` bash command."""
    import re
    # Extract the .spl file path from the command
    m = re.search(r'spl2\s+run\s+(\S+\.spl)', cmd)
    if not m:
        return ""
    spl_path = m.group(1)

    # Try all sub-paths as catalog keys (handle relative/absolute paths)
    parts = Path(spl_path).parts
    for i in range(len(parts)):
        key = str(Path(*parts[i:]))
        # Try directory component
        for d in parts:
            if d in catalog_map:
                return catalog_map[d]
        if key in catalog_map:
            return catalog_map[key]

    # Try the file stem
    stem = Path(spl_path).stem
    if stem in catalog_map:
        return catalog_map[stem]

    return ""


@cmd_code_rag.command("parse-log")
@click.argument("log_files", nargs=-1, required=True, metavar="LOG_FILE...")
@click.option("--cookbook-dir", default="./cookbook", show_default=True,
              help="Cookbook directory for description lookup via catalog.")
@click.option("--source", default="log", show_default=True,
              help="Provenance tag stored with each imported pair.")
@click.option("--validate/--no-validate", default=True, show_default=True,
              help="Validate SPL syntax before importing.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would be imported without writing to the store.")
@click.option("--storage-dir", default=None, help="Code-RAG DB directory (default from config).")
def code_rag_parse_log(
    log_files: tuple[str, ...],
    cookbook_dir: str,
    source: str,
    validate: bool,
    dry_run: bool,
    storage_dir: str | None,
) -> None:
    """Parse spl2 run log files and import valid (description, SPL) pairs.

    Scans LOG_FILE(s) for ```spl2 blocks (SPL source) paired with the
    preceding ```bash block (run command), derives a description from the
    cookbook catalog or the PROMPT/WORKFLOW name, validates the SPL, and
    adds each valid pair to the Code-RAG store.

    \b
    Works on both per-recipe logs (.spl/logs/*.log) and tee'd run_all output:

    \b
      spl2 code-rag parse-log .spl/logs/run_*.log
      spl2 code-rag parse-log cookbook/out/run_all_20260320.md
      spl2 code-rag parse-log cookbook/out/run_all_20260320.md --dry-run
    """
    from spl2.text2spl import Text2SPL

    catalog_map = _load_catalog_map(cookbook_dir)
    store = None if dry_run else _get_code_rag_store(storage_dir)

    total_found = total_added = total_skipped = total_invalid = 0

    for log_path_str in log_files:
        log_path = Path(log_path_str)
        text = log_path.read_text(encoding="utf-8")
        pairs = _parse_log_for_pairs(text)
        click.echo(f"\n{log_path.name}: {len(pairs)} pair(s) found")

        for pair in pairs:
            total_found += 1
            spl_source = pair["spl_source"]
            cmd = pair["command"]

            # Derive description: prompt block → catalog → SPL name → file stem
            prompt_val = pair.get("prompt") or ""
            description = (
                prompt_val
                or _description_from_command(cmd, catalog_map)
                or _description_from_spl(spl_source)
                or (Path(cmd.split()[2]).stem.replace("_", " ") if len(cmd.split()) > 2 else "")
            )
            if not description:
                click.echo(f"  [skip] no description — cmd: {cmd[:60]}")
                total_skipped += 1
                continue

            if validate:
                valid, message = Text2SPL.validate_output(spl_source)
                if not valid:
                    click.echo(f"  [invalid] {message[:80]} — {description[:50]}")
                    total_invalid += 1
                    continue

            if dry_run:
                click.echo(f"  [dry-run] would add: {description[:70]}")
            elif store is not None:
                store.add_pair(
                    description=description,
                    spl_source=spl_source,
                    metadata={"source": source, "log_file": log_path.name},
                )
                click.echo(f"  [added] {description[:70]}")
            total_added += 1

    click.echo(
        f"\nDone: found={total_found}  "
        f"{'would add' if dry_run else 'added'}={total_added}  "
        f"skipped={total_skipped}  invalid={total_invalid}"
    )
    if store is not None:
        click.echo(f"Total in store: {store.count()}")


# ── spl2 text2spl / compile ──────────────────────────────────────────────────

@cli.command("text2spl", context_settings={"ignore_unknown_options": True})
@click.argument("description")
@click.option("--adapter", default=None, metavar="NAME",
              help="Compiler adapter (default: text2spl.adapter from config).")
@click.option("--model", "-m", default=None, metavar="MODEL",
              help="Compiler model (default: text2spl.model from config).")
@click.option("--mode", type=click.Choice(["auto", "prompt", "workflow"]),
              default=None,
              help="Generation mode: prompt, workflow, or auto (default from config).")
@click.option("--validate/--no-validate", default=True, show_default=True,
              help="Validate generated SPL code.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Write generated SPL code to FILE.")
@click.option("--execute", is_flag=True, default=False,
              help="Execute the generated code immediately.")
@click.option("--param", "-p", multiple=True, metavar="KEY=VALUE",
              help="Parameters for execution (use with --execute).")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def cmd_text2spl(description: str, adapter: str | None, model: str | None,
                 mode: str | None, validate: bool, output: str | None,
                 execute: bool, param: tuple[str, ...],
                 extra_args: tuple[str, ...]) -> None:
    """Compile natural language DESCRIPTION into SPL 2.0 code.

    Uses the dedicated text2spl compiler adapter/model from config
    (text2spl.adapter / text2spl.model) — independent of the runtime
    adapter used by `spl2 run`.

    \b
    Examples:
      spl2 text2spl "summarize a document"
      spl2 text2spl "build a review agent" --mode workflow
      spl2 text2spl "translate text to French" -o translate.spl
      spl2 text2spl "classify user intent" --execute text="Hello there"
      spl2 text2spl "..." --adapter ollama -m qwen2.5-coder  # override compiler
    """
    # text2spl has its own adapter/model config section, separate from runtime.
    # Priority: CLI flag > text2spl config section > global adapter fallback.
    adapter = adapter or _cfg_default("text2spl.adapter", None) or _cfg_default("adapter", "claude_cli")
    adapter = adapter or "claude_cli"
    model   = model   or _cfg_default("text2spl.model",   None) or None
    mode    = mode    or _cfg_default("text2spl.mode",    "auto") or "auto"

    # Set up logging
    log_path = _setup_logging(run_name="text2spl", adapter=adapter)
    from dd_logging import get_logger
    log = get_logger("cli.text2spl", "spl2")
    log.info("spl2 text2spl %r --adapter %s --mode %s", description, adapter, mode)

    from spl2.text2spl import Text2SPL
    from spl2.adapters import get_adapter as _get_adapter

    try:
        llm = _get_adapter(adapter)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    # Wire up Code-RAG if enabled in config
    code_rag = None
    if _cfg_default("code_rag.enabled", True):
        try:
            from spl2.code_rag import CodeRAGStore
            code_rag = CodeRAGStore(
                storage_dir=_cfg_default("code_rag.storage_dir", ".spl/code_rag"),
                collection_name=_cfg_default("code_rag.collection", CodeRAGStore.COLLECTION_NAME),
            )
            if code_rag.count() > 0:
                click.echo(f"Code-RAG: {code_rag.count()} examples indexed", err=True)
            else:
                click.echo("Code-RAG: store empty — run `spl2 code-rag index` to populate", err=True)
                code_rag = None
        except Exception as exc:
            log.warning("Code-RAG unavailable: %s", exc)

    compiler = Text2SPL(
        adapter=llm,
        max_retries=_cfg_default("text2spl.max_retries", 2),
        code_rag=code_rag,
        rag_top_k=_cfg_default("code_rag.top_k", 4),
        auto_capture=_cfg_default("code_rag.auto_capture", True),
    )

    try:
        spl_code = asyncio.run(compiler.compile(description, mode=mode))
    except Exception as exc:
        log.exception("Compilation failed: %s", exc)
        raise click.ClickException(f"Compilation failed: {exc}") from exc

    log.info("Generated %d bytes of SPL code", len(spl_code))

    # Validate
    if validate:
        valid, message = Text2SPL.validate_output(spl_code)
        if not valid:
            click.echo("--- Generated (invalid) ---", err=True)
            click.echo(spl_code, err=True)
            log.warning("Validation failed: %s", message)
            raise click.ClickException(f"Validation failed: {message}")
        if message != "OK":
            click.echo(f"Validation: {message}", err=True)

    # Output
    if output:
        Path(output).write_text(spl_code, encoding="utf-8")
        click.echo(f"Written to {output}")
    else:
        click.echo(spl_code)

    # Execute if requested
    if execute:
        params = _parse_params(param + extra_args)
        _ensure_workspace(".spl")
        from spl2.executor import Executor

        ast = _parse_source(spl_code)
        if model:
            from spl2.ast_nodes import PromptStatement
            for stmt in ast.statements:
                if isinstance(stmt, PromptStatement):
                    stmt.model = model
        from spl2.analyzer import Analyzer
        analysis = Analyzer().analyze(ast)

        executor = Executor(adapter_name=adapter, storage_dir=".spl")
        try:
            results = asyncio.run(executor.execute_program(analysis, params=params))
            for result in results:
                _print_result(result)
        finally:
            executor.close()

    click.echo(f"Log: {log_path}", err=True)


# Register alias: compile
cli.add_command(cmd_text2spl, name="compile")


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
