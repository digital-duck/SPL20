"""DeepSeek LLM adapter for SPL 2.0.

Uses the DeepSeek API (OpenAI-compatible).
Requires: pip install httpx
API key: DEEPSEEK_API_KEY environment variable
"""

from __future__ import annotations

import logging
import os

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


class DeepSeekAdapter(LLMAdapter):
    """LLM adapter for DeepSeek models via their OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEEPSEEK_URL,
        default_model: str = "deepseek-chat",
        timeout: int = 180,
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for DeepSeekAdapter. "
                "Install it with: pip install httpx"
            )
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "DeepSeek API key required. Pass api_key= or set DEEPSEEK_API_KEY."
            )
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._token_counter = TokenCounter(default_model)

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate a response via DeepSeek API."""
        model = model or self.default_model

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start = self._measure_time()
        response = await self._client.post(
            self.base_url, json=payload, headers=headers,
        )
        response.raise_for_status()
        latency_ms = self._elapsed_ms(start)

        data = response.json()

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "") or ""

        # DeepSeek reasoning models may return reasoning_content
        if not content.strip():
            content = message.get("reasoning_content", "") or ""

        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

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
        """List available DeepSeek models."""
        return [
            "deepseek-chat",
            "deepseek-reasoner",
        ]

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
