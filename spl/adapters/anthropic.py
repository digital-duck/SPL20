"""Anthropic (Claude) LLM adapter for SPL 2.0.

Uses the Anthropic Messages API directly.
Requires: pip install anthropic
API key: ANTHROPIC_API_KEY environment variable
"""

from __future__ import annotations

import logging
import os

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class AnthropicAdapter(LLMAdapter):
    """LLM adapter for Anthropic's Claude models via the Messages API."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        timeout: int = 180,
    ):
        if anthropic is None:
            raise ImportError(
                "anthropic is required for AnthropicAdapter. "
                "Install it with: pip install anthropic"
            )
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Pass api_key= or set ANTHROPIC_API_KEY."
            )
        self.default_model = default_model
        self.default_max_tokens = max_tokens
        self._client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            timeout=timeout,
        )
        self._token_counter = TokenCounter(default_model)

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate a response via Anthropic Messages API."""
        model = model or self.default_model

        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        start = self._measure_time()
        response = await self._client.messages.create(**kwargs)
        latency_ms = self._elapsed_ms(start)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens

        counter = TokenCounter(model)
        cost_usd = counter.estimate_cost(input_tokens, output_tokens)

        return GenerationResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens using TokenCounter."""
        if model:
            counter = TokenCounter(model)
            return counter.count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """List available Anthropic Claude models."""
        return [
            "claude-opus-4-0-20250514",
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250514",
            "claude-3-5-haiku-20241022",
        ]

    async def close(self):
        """Close the underlying client."""
        await self._client.close()
