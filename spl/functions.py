"""SPL 2.0 built-in and user-defined function registry."""

from __future__ import annotations
import json
import os
from typing import Any, Callable
from spl.ast_nodes import CreateFunctionStatement, ProcedureStatement


class FunctionRegistry:
    """Registry for SPL functions and procedures (built-in and user-defined)."""

    def __init__(self):
        self._functions: dict[str, CreateFunctionStatement] = {}
        self._procedures: dict[str, ProcedureStatement] = {}
        self._builtins: dict[str, Callable[..., Any]] = {}
        self._tools: dict[str, Callable[..., Any]] = {}  # Python Callables invokable via CALL
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in SPL functions."""
        self._builtins["summarize"] = self._builtin_summarize
        self._builtins["len"] = self._builtin_len
        self._builtins["upper"] = self._builtin_upper
        self._builtins["lower"] = self._builtin_lower
        self._builtins["truncate"] = self._builtin_truncate
        # List operations (canonical names)
        self._builtins["list"] = FunctionRegistry._builtin_list
        self._builtins["get"] = FunctionRegistry._builtin_get
        self._builtins["append"] = FunctionRegistry._builtin_append
        self._builtins["count"] = FunctionRegistry._builtin_count
        self._builtins["join"] = FunctionRegistry._builtin_join
        # list_* aliases — preferred in SPL 2.0 for readability
        self._builtins["list_append"] = FunctionRegistry._builtin_append
        self._builtins["list_concat"] = FunctionRegistry._builtin_join
        self._builtins["list_count"] = FunctionRegistry._builtin_count
        self._builtins["list_get"] = FunctionRegistry._builtin_get
        # Map operations
        self._builtins["map"] = FunctionRegistry._builtin_map
        self._builtins["map_get"] = FunctionRegistry._builtin_map_get
        self._builtins["map_set"] = FunctionRegistry._builtin_map_set
        self._builtins["map_keys"] = FunctionRegistry._builtin_map_keys
        self._builtins["map_values"] = FunctionRegistry._builtin_map_values
        self._builtins["map_merge"] = FunctionRegistry._builtin_map_merge
        self._builtins["map_has"] = FunctionRegistry._builtin_map_has
        self._builtins["map_delete"] = FunctionRegistry._builtin_map_delete
        # File I/O — deterministic, zero tokens
        self._builtins["write_file"] = FunctionRegistry._builtin_write_file
        self._builtins["read_file"] = FunctionRegistry._builtin_read_file

    def register(self, func_stmt: CreateFunctionStatement):
        """Register a user-defined function."""
        self._functions[func_stmt.name] = func_stmt

    def register_procedure(self, proc_stmt: ProcedureStatement):
        """Register a user-defined procedure."""
        self._procedures[proc_stmt.name] = proc_stmt

    def register_tool(self, name: str, fn: Callable):
        """Register a Python Callable as a CALL-able tool.

        The Callable receives all CALL arguments as strings and must return a str.
        Both sync and async Callables are supported.
        """
        self._tools[name] = fn

    def get(self, name: str) -> CreateFunctionStatement | None:
        """Get a user-defined function by name."""
        return self._functions.get(name)

    def get_procedure(self, name: str) -> ProcedureStatement | None:
        """Get a user-defined procedure by name."""
        return self._procedures.get(name)

    def get_tool(self, name: str) -> Callable | None:
        """Get a registered Python tool by name."""
        return self._tools.get(name)

    def is_builtin(self, name: str) -> bool:
        return name.lower() in self._builtins

    def call_builtin(self, name: str, *args) -> str:
        func = self._builtins.get(name.lower())
        if func is None:
            raise ValueError(f"Unknown built-in function: {name}")
        return func(*args)

    # === Built-in Implementations ===

    @staticmethod
    def _builtin_summarize(text: str, max_tokens: int = 200) -> str:
        if not text:
            return ""
        sentences = text.replace('\n', ' ').split('. ')
        result = []
        token_count = 0
        for sentence in sentences:
            est_tokens = len(sentence) // 4
            if token_count + est_tokens > max_tokens:
                break
            result.append(sentence)
            token_count += est_tokens
        return '. '.join(result)

    @staticmethod
    def _builtin_len(text: str) -> str:
        return str(len(text) // 4)

    @staticmethod
    def _builtin_upper(text: str) -> str:
        return text.upper()

    @staticmethod
    def _builtin_lower(text: str) -> str:
        return text.lower()

    @staticmethod
    def _builtin_truncate(text: str, max_chars: int = 1000) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    # === List Built-ins ===

    @staticmethod
    def _builtin_list(*args) -> str:
        """LIST() → empty JSON array; LIST(a,b,...) → JSON array of args."""
        return json.dumps(list(args))

    @staticmethod
    def _builtin_get(collection: str, index: str) -> str:
        """GET(list, index) — return item at index from a JSON array or comma-separated string."""
        idx = int(str(index).strip())
        # Try JSON first
        try:
            items = json.loads(collection)
            if isinstance(items, list):
                return str(items[idx])
        except (json.JSONDecodeError, ValueError, IndexError):
            pass
        # Fallback: comma-separated
        items_csv = [s.strip().strip('"\'') for s in str(collection).split(",")]
        if 0 <= idx < len(items_csv):
            return items_csv[idx]
        return ""

    @staticmethod
    def _builtin_append(collection: str, item: str) -> str:
        """APPEND(list, item) — append item to a JSON array; return updated array."""
        try:
            items = json.loads(collection)
            if isinstance(items, list):
                items.append(item)
                return json.dumps(items)
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: start a new list
        return json.dumps([collection, item]) if collection.strip() else json.dumps([item])

    @staticmethod
    def _builtin_count(collection: str) -> str:
        """COUNT(list) — return number of items in a JSON array or comma-separated string."""
        try:
            items = json.loads(collection)
            if isinstance(items, list):
                return str(len(items))
        except (json.JSONDecodeError, ValueError):
            pass
        return str(len([s for s in str(collection).split(",") if s.strip()]))

    @staticmethod
    def _builtin_join(collection: str, separator: str = ", ") -> str:
        """JOIN(list, sep) — join a JSON array into a single string."""
        try:
            items = json.loads(collection)
            if isinstance(items, list):
                return separator.join(str(i) for i in items)
        except (json.JSONDecodeError, ValueError):
            pass
        return str(collection)

    # === Map Built-ins ===

    @staticmethod
    def _builtin_map(*args) -> str:
        """MAP() → empty JSON object; MAP('k1','v1','k2','v2',...) → JSON object."""
        if len(args) % 2 != 0:
            raise ValueError("map() requires an even number of arguments (key-value pairs)")
        obj = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
        return json.dumps(obj)

    @staticmethod
    def _builtin_map_get(mapping: str, key: str, default: str = "") -> str:
        """MAP_GET(map, key [, default]) — return value for key, or default if missing."""
        try:
            obj = json.loads(mapping)
            if isinstance(obj, dict):
                return str(obj.get(key, default))
        except (json.JSONDecodeError, ValueError):
            pass
        return default

    @staticmethod
    def _builtin_map_set(mapping: str, key: str, value: str) -> str:
        """MAP_SET(map, key, value) — return updated map with key set to value."""
        try:
            obj = json.loads(mapping) if mapping.strip() else {}
            if not isinstance(obj, dict):
                obj = {}
        except (json.JSONDecodeError, ValueError):
            obj = {}
        obj[key] = value
        return json.dumps(obj)

    @staticmethod
    def _builtin_map_keys(mapping: str) -> str:
        """MAP_KEYS(map) — return JSON array of keys."""
        try:
            obj = json.loads(mapping)
            if isinstance(obj, dict):
                return json.dumps(list(obj.keys()))
        except (json.JSONDecodeError, ValueError):
            pass
        return json.dumps([])

    @staticmethod
    def _builtin_map_values(mapping: str) -> str:
        """MAP_VALUES(map) — return JSON array of values."""
        try:
            obj = json.loads(mapping)
            if isinstance(obj, dict):
                return json.dumps(list(obj.values()))
        except (json.JSONDecodeError, ValueError):
            pass
        return json.dumps([])

    @staticmethod
    def _builtin_map_merge(*mappings: str) -> str:
        """MAP_MERGE(map1, map2, ...) — merge maps left to right; later keys win."""
        result: dict = {}
        for mapping in mappings:
            try:
                obj = json.loads(mapping)
                if isinstance(obj, dict):
                    result.update(obj)
            except (json.JSONDecodeError, ValueError):
                pass
        return json.dumps(result)

    @staticmethod
    def _builtin_map_has(mapping: str, key: str) -> str:
        """MAP_HAS(map, key) — return 'true' if key exists, 'false' otherwise."""
        try:
            obj = json.loads(mapping)
            if isinstance(obj, dict):
                return "true" if key in obj else "false"
        except (json.JSONDecodeError, ValueError):
            pass
        return "false"

    @staticmethod
    def _builtin_map_delete(mapping: str, key: str) -> str:
        """MAP_DELETE(map, key) — return map with key removed."""
        try:
            obj = json.loads(mapping)
            if isinstance(obj, dict):
                obj.pop(key, None)
                return json.dumps(obj)
        except (json.JSONDecodeError, ValueError):
            pass
        return mapping

    # === File I/O Built-ins ===

    @staticmethod
    def _builtin_write_file(path: str, content: str) -> str:
        """write_file(path, content) — write content to a file, creating parent dirs as needed.
        Returns 'written: <path>' on success.
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"written: {path}"

    @staticmethod
    def _builtin_read_file(path: str) -> str:
        """read_file(path) — read a file and return its content as a string.
        Returns empty string if the file does not exist.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

