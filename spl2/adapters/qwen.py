"""Qwen (Alibaba Cloud) LLM adapter for SPL 2.0.

Uses the DashScope API (OpenAI-compatible endpoint).
Requires: pip install httpx
API key: DASHSCOPE_API_KEY environment variable
"""

from __future__ import annotations

import logging
import os

from spl2.adapters.base import LLMAdapter, GenerationResult
from spl2.token_counter import TokenCounter

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

DASHSCOPE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"


class QwenAdapter(LLMAdapter):
    """LLM adapter for Qwen models via Alibaba's DashScope API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DASHSCOPE_URL,
        default_model: str = "qwen-plus",
        timeout: int = 180,
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for QwenAdapter. "
                "Install it with: pip install httpx"
            )
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "DashScope API key required. Pass api_key= or set DASHSCOPE_API_KEY."
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
        """Generate a response via DashScope OpenAI-compatible API."""
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
        """List available Qwen models."""
        return [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen-long",
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
            "qwen2.5-coder-32b-instruct",
        ]

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
