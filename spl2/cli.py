"""SPL 2.0 Command-Line Interface.

Usage:
    spl2 run   <file.spl> [--adapter=echo] [--param key=value ...]
    spl2 explain <file.spl>
    spl2 parse  <file.spl> [--json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from spl2.lexer import Lexer
from spl2.parser import Parser
from spl2.analyzer import Analyzer
from spl2.optimizer import Optimizer
from spl2.executor import Executor, SPLResult, WorkflowResult
from spl2.explain import explain_plans


def main(argv: list[str] | None = None):
    """Entry point for the spl2 CLI."""
    parser = argparse.ArgumentParser(
        prog="spl2",
        description="SPL 2.0 — Structured Prompt Language for Agentic Workflows",
    )
    sub = parser.add_subparsers(dest="command")

    # --- run ---
    run_p = sub.add_parser("run", help="Execute an SPL file")
    run_p.add_argument("file", help="Path to .spl file")
    run_p.add_argument("--adapter", default="echo", help="LLM adapter (default: echo)")
    run_p.add_argument("--param", "-p", action="append", default=[],
                       metavar="KEY=VALUE", help="Pass parameter (repeatable)")
    run_p.add_argument("--cache", action="store_true", help="Enable prompt caching")

    # --- explain ---
    exp_p = sub.add_parser("explain", help="Show execution plan without running")
    exp_p.add_argument("file", help="Path to .spl file")

    # --- parse ---
    par_p = sub.add_parser("parse", help="Parse and validate an SPL file")
    par_p.add_argument("file", help="Path to .spl file")
    par_p.add_argument("--json", action="store_true", dest="as_json",
                       help="Output AST as JSON")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "run":
            _cmd_run(args)
        elif args.command == "explain":
            _cmd_explain(args)
        elif args.command == "parse":
            _cmd_parse(args)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# ================================================================
# Commands
# ================================================================

def _cmd_run(args):
    source = _read_file(args.file)
    params = _parse_params(args.param)

    analysis = _analyze(source)
    executor = Executor(
        adapter_name=args.adapter,
        cache_enabled=args.cache,
    )
    try:
        results = asyncio.run(executor.execute_program(analysis, params=params))
        for result in results:
            _print_result(result)
    finally:
        executor.close()


def _cmd_explain(args):
    source = _read_file(args.file)
    analysis = _analyze(source)
    optimizer = Optimizer()
    plans = optimizer.optimize(analysis)
    print(explain_plans(plans))


def _cmd_parse(args):
    source = _read_file(args.file)
    ast = _parse(source)

    if args.as_json:
        from spl2.ir import ast_to_json
        print(json.dumps(ast_to_json(ast), indent=2))
    else:
        analysis = Analyzer().analyze(ast)
        print(f"Parsed OK: {len(ast.statements)} statement(s)")
        for stmt in ast.statements:
            kind = type(stmt).__name__.replace("Statement", "")
            name = getattr(stmt, "name", "")
            print(f"  - {kind}: {name}")
        if analysis.warnings:
            print(f"\nWarnings ({len(analysis.warnings)}):")
            for w in analysis.warnings:
                print(f"  ! {w}")


# ================================================================
# Helpers
# ================================================================

def _read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def _parse(source: str):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def _analyze(source: str):
    ast = _parse(source)
    analyzer = Analyzer()
    return analyzer.analyze(ast)


def _parse_params(raw: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid param format '{item}', expected KEY=VALUE")
        key, value = item.split("=", 1)
        params[key.strip()] = value.strip()
    return params


def _print_result(result):
    if isinstance(result, SPLResult):
        print("=" * 60)
        print(f"Model: {result.model}")
        print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
        print(f"Latency: {result.latency_ms:.0f}ms")
        if result.cost_usd is not None:
            print(f"Cost: ${result.cost_usd:.6f}")
        print("-" * 60)
        print(result.content)
        print("=" * 60)
    elif isinstance(result, WorkflowResult):
        print("=" * 60)
        print(f"Status: {result.status}")
        print(f"LLM Calls: {result.total_llm_calls}")
        print(f"Tokens: {result.total_input_tokens} in / {result.total_output_tokens} out")
        print(f"Latency: {result.total_latency_ms:.0f}ms")
        if result.committed_value:
            print("-" * 60)
            print(f"Committed: {result.committed_value}")
        if result.output:
            print("-" * 60)
            print("Variables:")
            for k, v in result.output.items():
                val_preview = v[:200] if len(v) > 200 else v
                print(f"  @{k} = {val_preview}")
        print("=" * 60)


if __name__ == "__main__":
    main()
