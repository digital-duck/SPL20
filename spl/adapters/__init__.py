"""LLM adapter registry and factory for SPL 2.0.

Provider resolution order:
  1. dd-llm bridge  — preferred for providers dd-llm supports natively
                      (anthropic, openai, ollama, openrouter, claude_cli, google)
  2. Bespoke adapters — fallback when dd-llm is not installed, or for providers
                        dd-llm does not cover (echo, momagrid, deepseek, qwen,
                        bedrock, vertex, azure_openai)
"""

import inspect
import logging

from spl.adapters.base import LLMAdapter, GenerationResult

_log = logging.getLogger("spl.adapters")
_ADAPTER_REGISTRY: dict[str, type[LLMAdapter]] = {}

# Providers handled by dd-llm; "google" maps to dd-llm's "gemini" backend.
_DD_LLM_PROVIDERS: dict[str, str] = {
    "anthropic":  "anthropic",
    "openai":     "openai",
    "ollama":     "ollama",
    "openrouter": "openrouter",
    "claude_cli": "claude_cli",
    "google":     "gemini",
}


def register_adapter(name: str, adapter_cls):
    """Register an LLM adapter by name (class or factory callable)."""
    _ADAPTER_REGISTRY[name] = adapter_cls


def get_adapter(name: str, **kwargs) -> LLMAdapter:
    """Get an LLM adapter instance by name."""
    if name not in _ADAPTER_REGISTRY:
        available = ", ".join(sorted(_ADAPTER_REGISTRY.keys())) or "(none)"
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    entry = _ADAPTER_REGISTRY[name]
    # Support both class constructors and factory callables.
    if inspect.isclass(entry):
        sig = inspect.signature(entry.__init__)
        supported = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return entry(**supported)
    return entry(**kwargs)


def list_adapters() -> list[str]:
    """List registered adapter names."""
    return list(_ADAPTER_REGISTRY.keys())


def _register_dd_llm_adapters() -> bool:
    """Register dd-llm bridged adapters. Returns True on success."""
    try:
        from spl.adapters.dd_llm_bridge import DDLLMBridge
        for spl_name, dd_name in _DD_LLM_PROVIDERS.items():
            register_adapter(spl_name, lambda p=dd_name, **kw: DDLLMBridge(p, **kw))
        _log.debug("dd-llm bridge registered for: %s", ", ".join(_DD_LLM_PROVIDERS))
        return True
    except ImportError:
        _log.debug("dd-llm not found; falling back to bespoke adapters")
        return False


def _register_bespoke_adapters():
    """Register bespoke SPL adapter implementations as fallback."""
    _candidates = [
        ("claude_cli",  "spl.adapters.claude_cli",  "ClaudeCLIAdapter"),
        ("openrouter",  "spl.adapters.openrouter",  "OpenRouterAdapter"),
        ("ollama",      "spl.adapters.ollama",       "OllamaAdapter"),
        ("anthropic",   "spl.adapters.anthropic",    "AnthropicAdapter"),
        ("openai",      "spl.adapters.openai",       "OpenAIAdapter"),
        ("google",      "spl.adapters.google",       "GoogleAdapter"),
    ]
    for name, mod_path, cls_name in _candidates:
        if name in _ADAPTER_REGISTRY:
            continue   # already registered (dd-llm bridge took precedence)
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            register_adapter(name, getattr(mod, cls_name))
        except (ImportError, AttributeError):
            pass


def _register_builtin_adapters():
    """Register all available adapters."""
    # ── Always-available SPL-specific adapters ────────────────────────────
    for name, mod_path, cls_name in [
        ("echo",        "spl.adapters.echo",        "EchoAdapter"),
        ("momagrid",    "spl.adapters.momagrid",     "MomagridAdapter"),
        ("deepseek",    "spl.adapters.deepseek",     "DeepSeekAdapter"),
        ("qwen",        "spl.adapters.qwen",         "QwenAdapter"),
        ("bedrock",     "spl.adapters.bedrock",      "BedrockAdapter"),
        ("vertex",      "spl.adapters.vertex",       "VertexAdapter"),
        ("azure_openai","spl.adapters.azure_openai", "AzureOpenAIAdapter"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            register_adapter(name, getattr(mod, cls_name))
        except (ImportError, AttributeError):
            pass

    # ── Prefer dd-llm bridge; fall back to bespoke implementations ────────
    if not _register_dd_llm_adapters():
        _register_bespoke_adapters()


_register_builtin_adapters()
