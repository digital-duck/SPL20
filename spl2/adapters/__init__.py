"""LLM adapter registry and factory for SPL 2.0."""

from spl2.adapters.base import LLMAdapter, GenerationResult

_ADAPTER_REGISTRY: dict[str, type[LLMAdapter]] = {}


def register_adapter(name: str, adapter_cls: type[LLMAdapter]):
    """Register an LLM adapter by name."""
    _ADAPTER_REGISTRY[name] = adapter_cls


def get_adapter(name: str, **kwargs) -> LLMAdapter:
    """Get an LLM adapter instance by name."""
    if name not in _ADAPTER_REGISTRY:
        available = ", ".join(_ADAPTER_REGISTRY.keys()) or "(none)"
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return _ADAPTER_REGISTRY[name](**kwargs)


def list_adapters() -> list[str]:
    """List registered adapter names."""
    return list(_ADAPTER_REGISTRY.keys())


def _register_builtin_adapters():
    """Register adapters that are available."""
    try:
        from spl2.adapters.echo import EchoAdapter
        register_adapter("echo", EchoAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.claude_cli import ClaudeCLIAdapter
        register_adapter("claude_cli", ClaudeCLIAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.openrouter import OpenRouterAdapter
        register_adapter("openrouter", OpenRouterAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.ollama import OllamaAdapter
        register_adapter("ollama", OllamaAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.momagrid import MomagridAdapter
        register_adapter("momagrid", MomagridAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.anthropic import AnthropicAdapter
        register_adapter("anthropic", AnthropicAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.openai import OpenAIAdapter
        register_adapter("openai", OpenAIAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.google import GoogleAdapter
        register_adapter("google", GoogleAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.deepseek import DeepSeekAdapter
        register_adapter("deepseek", DeepSeekAdapter)
    except ImportError:
        pass

    try:
        from spl2.adapters.qwen import QwenAdapter
        register_adapter("qwen", QwenAdapter)
    except ImportError:
        pass


_register_builtin_adapters()
