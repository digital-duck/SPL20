"""OpenAI LLM adapter for SPL 2.0.

Uses the OpenAI Chat Completions API directly.
Requires: pip install openai
API key: OPENAI_API_KEY environment variable
"""

from __future__ import annotations

import logging
import os

from spl2.adapters.base import LLMAdapter, GenerationResult
from spl2.token_counter import TokenCounter

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMAdapter):
    """LLM adapter for OpenAI models via the Chat Completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gpt-4o",
        timeout: int = 180,
    ):
        if openai is None:
            raise ImportError(
                "openai is required for OpenAIAdapter. "
                "Install it with: pip install openai"
            )
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key= or set OPENAI_API_KEY."
            )
        self.default_model = default_model
        self._client = openai.AsyncOpenAI(
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
        """Generate a response via OpenAI Chat Completions API."""
        model = model or self.default_model

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = self._measure_time()
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        latency_ms = self._elapsed_ms(start)

        choice = response.choices[0] if response.choices else None
        content = choice.message.content or "" if choice else ""

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else (input_tokens + output_tokens)

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
        """Count tokens using TokenCounter (with tiktoken if available)."""
        if model:
            counter = TokenCounter(model)
            return counter.count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """List available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
            "o3",
            "o3-mini",
        ]

    async def close(self):
        """Close the underlying client."""
        await self._client.close()
