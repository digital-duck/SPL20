"""dd-llm bridge adapter for SPL 2.0.

Wraps any synchronous dd-llm adapter in SPL 2.0's async LLMAdapter interface.
Eliminates bespoke provider implementations for providers already in dd-llm:
  anthropic, openai, ollama, openrouter, claude_cli, gemini (→ google).

The bridge is transparent to the executor — it presents the same
``async generate()`` interface as any other LLMAdapter.
"""

from __future__ import annotations

import asyncio
import logging

from spl.adapters.base import LLMAdapter, GenerationResult

_log = logging.getLogger("spl.adapters.bridge")


class DDLLMBridge(LLMAdapter):
    """Async wrapper around a synchronous dd-llm adapter.

    dd-llm uses a synchronous ``call()`` interface; SPL 2.0's executor uses
    ``await adapter.generate()``.  This bridge runs dd-llm's sync call in a
    thread pool via ``asyncio.to_thread()`` so the event loop is never blocked.

    Parameters
    ----------
    provider : str
        dd-llm provider name — e.g. ``"anthropic"``, ``"ollama"``, ``"openai"``.
    **kwargs
        Forwarded verbatim to ``dd_llm.get_adapter(provider, **kwargs)``.
    """

    def __init__(self, provider: str, **kwargs) -> None:
        import dd_llm
        self._provider_name = provider
        self._impl = dd_llm.get_adapter(provider, **kwargs)
        _log.debug("DDLLMBridge: loaded provider=%r via dd-llm", provider)

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate via dd-llm; runs in a thread pool to keep the event loop free."""
        result = await asyncio.to_thread(
            self._impl.call,
            prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
        )
        if not result.success:
            last_err = (
                result.error_history[-1].get("error", "unknown")
                if result.error_history
                else "unknown"
            )
            raise RuntimeError(
                f"dd-llm [{self._provider_name}] failed: {last_err}"
            )
        return GenerationResult(
            content=result.content,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.input_tokens + result.output_tokens,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        from spl.token_counter import TokenCounter
        return TokenCounter(model or "default").count(text)

    def list_models(self) -> list[str]:
        return self._impl.list_models()
