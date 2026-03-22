"""SPL 2.0 Python tool registry.

Tools are plain Python callables (sync or async) registered under a name and
invokable from SPL workflows via the CALL statement:

    CALL my_tool(@arg1, @arg2) INTO @result

Usage — decorator style (global registry):

    from spl.tools import spl_tool

    @spl_tool
    def calc_growth_rate(pop_prev: str, pop_curr: str) -> str:
        prev = float(pop_prev.replace(",", ""))
        curr = float(pop_curr.replace(",", ""))
        return f"{((curr - prev) / prev) * 100:.4f}"

Usage — programmatic (per-executor):

    executor.register_tool("calc_growth_rate", calc_growth_rate)

Usage — load all tools from a module file via CLI:

    spl run my.spl --tools tools/my_tools.py
"""

from __future__ import annotations
import importlib.util
import sys
from typing import Callable

# Global registry — populated by @spl_tool
_GLOBAL_TOOLS: dict[str, Callable] = {}


def spl_tool(fn: Callable | None = None, *, name: str | None = None):
    """Decorator that registers a Python callable in the global SPL tool registry.

    Can be used with or without arguments:

        @spl_tool
        def my_tool(x: str) -> str: ...

        @spl_tool(name="my_tool")
        def my_tool_impl(x: str) -> str: ...
    """
    if fn is None:
        # Called as @spl_tool(name="...") — return the actual decorator
        def decorator(f: Callable) -> Callable:
            _GLOBAL_TOOLS[name or f.__name__] = f
            return f
        return decorator

    # Called as @spl_tool (no parentheses)
    _GLOBAL_TOOLS[name or fn.__name__] = fn
    return fn


def load_tools_module(path: str) -> dict[str, Callable]:
    """Import a Python module from a file path and return all @spl_tool functions.

    Any function decorated with @spl_tool in the module is automatically
    registered in _GLOBAL_TOOLS when imported. This function also collects
    and returns them for convenience.
    """
    spec = importlib.util.spec_from_file_location("_spl_tools", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tools module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_spl_tools"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return dict(_GLOBAL_TOOLS)


def get_global_tools() -> dict[str, Callable]:
    """Return a copy of the global tool registry."""
    return dict(_GLOBAL_TOOLS)
