"""Google Gemini LLM adapter for SPL 2.0.

Uses the Google GenAI SDK (google-genai).
Requires: pip install google-genai
API key: GOOGLE_API_KEY environment variable
"""

from __future__ import annotations

import logging
import os

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class GoogleAdapter(LLMAdapter):
    """LLM adapter for Google Gemini models via the GenAI SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gemini-2.5-flash",
        timeout: int = 180,
    ):
        if genai is None:
            raise ImportError(
                "google-genai is required for GoogleAdapter. "
                "Install it with: pip install google-genai"
            )
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Pass api_key= or set GOOGLE_API_KEY."
            )
        self.default_model = default_model
        self._client = genai.Client(api_key=self.api_key)
        self._token_counter = TokenCounter(default_model)

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate a response via Google Gemini API."""
        model = model or self.default_model

        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        if system:
            config.system_instruction = system

        start = self._measure_time()
        response = await self._client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        latency_ms = self._elapsed_ms(start)

        content = response.text or ""

        # Extract token counts from usage metadata
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0
        total_tokens = usage.total_token_count if usage else (input_tokens + output_tokens)

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
        """List available Google Gemini models."""
        return [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]

    async def close(self):
        """Close the underlying client."""
        pass  # google-genai client does not require explicit close
