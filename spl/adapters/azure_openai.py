"""Azure OpenAI LLM adapter for SPL 2.0.

Uses the openai SDK with the AzureOpenAI client.
Requires: pip install openai

Env vars:
  AZURE_OPENAI_ENDPOINT    — https://<resource>.openai.azure.com/
  AZURE_OPENAI_API_KEY     — API key from the Azure portal
  AZURE_OPENAI_API_VERSION — API version (default: 2025-01-01-preview)

The `model` parameter is your Azure deployment name (e.g. "gpt-4o"),
which may differ from the underlying OpenAI model name.

Managed Identity / Azure AD auth:
  Pass api_key=None and set AZURE_OPENAI_API_KEY="" to use keyless auth.
  Install azure-identity and inject a token provider via the openai SDK
  directly (not yet supported as a kwarg here — use the raw client if needed).
"""

from __future__ import annotations

import logging
import os

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import openai
    _AsyncAzureOpenAI = openai.AsyncAzureOpenAI
except ImportError:
    openai = None  # type: ignore[assignment]
    _AsyncAzureOpenAI = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_DEFAULT_API_VERSION = "2025-01-01-preview"


class AzureOpenAIAdapter(LLMAdapter):
    """LLM adapter for Azure OpenAI Service via the Chat Completions API."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        default_model: str = "gpt-4o",
        timeout: int = 180,
    ):
        if openai is None:
            raise ImportError(
                "openai is required for AzureOpenAIAdapter. "
                "Install it with: pip install openai"
            )
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        if not self.endpoint:
            raise ValueError(
                "Azure OpenAI endpoint required. "
                "Pass endpoint= or set AZURE_OPENAI_ENDPOINT."
            )
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Azure OpenAI API key required. "
                "Pass api_key= or set AZURE_OPENAI_API_KEY."
            )
        self.api_version = api_version or os.environ.get(
            "AZURE_OPENAI_API_VERSION", _DEFAULT_API_VERSION
        )
        self.default_model = default_model
        self._client = _AsyncAzureOpenAI(  # type: ignore[misc]
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
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
        """Generate a response via Azure OpenAI Chat Completions.

        `model` is the Azure deployment name, not the underlying model name.
        """
        model = model or self.default_model

        messages: list[dict] = []
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
        total_tokens = usage.total_tokens if usage else input_tokens + output_tokens

        cost_usd = TokenCounter(model).estimate_cost(input_tokens, output_tokens)

        logger.debug(
            "Azure OpenAI %s — %d in / %d out tokens, %.0f ms",
            model,
            input_tokens,
            output_tokens,
            latency_ms,
        )

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
            return TokenCounter(model).count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """List common Azure OpenAI deployment names.

        These must match the deployment names in your Azure OpenAI resource.
        """
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-35-turbo",
            "o1",
            "o1-mini",
            "o3",
            "o3-mini",
        ]

    async def close(self):
        """Close the underlying client."""
        await self._client.close()
