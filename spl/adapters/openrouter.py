"""OpenRouter LLM adapter for SPL 2.0."""

from __future__ import annotations

import json
import logging
import os
import re
import time

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterAdapter(LLMAdapter):
    """LLM adapter that routes requests through OpenRouter."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = OPENROUTER_URL,
        default_model: str = "anthropic/claude-sonnet-4-5",
        timeout: int = 180,
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for OpenRouterAdapter. "
                "Install it with: pip install httpx"
            )
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Pass api_key= or set OPENROUTER_API_KEY."
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
        """Generate a response via OpenRouter API."""
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
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/digital-duck/SPL",
            "X-Title": "SPL Engine",
        }

        start = self._measure_time()
        response = await self._client.post(
            self.base_url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

        data = self._parse_response(response.text)
        latency_ms = self._elapsed_ms(start)

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "") or ""

        # Reasoning model fallback: check reasoning fields if content is empty
        if not content.strip():
            content = (
                message.get("reasoning")
                or message.get("reasoning_content")
                or ""
            )

        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        # Estimate cost
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

    def _parse_response(self, text: str) -> dict:
        """Parse JSON response with 3-pass error recovery.

        Pass 1: Normal JSON parse.
        Pass 2: Strip ASCII control characters and retry.
        Pass 3: Regex extraction for truncated/malformed responses.
        """
        # Pass 1: normal parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Pass 2: strip ASCII control characters (0x00-0x1F except common whitespace)
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Pass 3: regex content extraction for truncated responses
        content_match = re.search(
            r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned
        )
        if content_match:
            extracted_content = content_match.group(1)
            # Unescape JSON string escapes
            try:
                extracted_content = json.loads(f'"{extracted_content}"')
            except json.JSONDecodeError:
                pass
            logger.warning("Used regex fallback to extract content from malformed response")
            return {
                "choices": [{"message": {"content": extracted_content}}],
                "usage": {},
            }

        raise ValueError(f"Failed to parse OpenRouter response after 3 passes: {text[:200]}")

    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens using TokenCounter."""
        if model:
            counter = TokenCounter(model)
            return counter.count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """List common OpenRouter models."""
        return [
            "anthropic/claude-sonnet-4-5",
            "anthropic/claude-haiku-3.5",
            "anthropic/claude-opus-4",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-2.0-flash-001",
            "google/gemini-2.5-pro-preview",
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-chat-v3-0324",
            "mistralai/mistral-large",
        ]

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
