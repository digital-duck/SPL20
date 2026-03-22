"""Ollama LLM adapter for SPL 2.0."""

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


class OllamaAdapter(LLMAdapter):
    """LLM adapter for locally-running Ollama models."""

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str = "llama3.2",
        timeout: int = 120,
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for OllamaAdapter. "
                "Install it with: pip install httpx"
            )
        self.base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        )
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
        """Generate a response via Ollama's OpenAI-compatible endpoint."""
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

        url = f"{self.base_url}/v1/chat/completions"

        start = self._measure_time()
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: ollama serve"
            )

        data = response.json()
        latency_ms = self._elapsed_ms(start)

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "") or ""

        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

        return GenerationResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=0.0,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens using TokenCounter."""
        if model:
            counter = TokenCounter(model)
            return counter.count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """List available Ollama models by querying the API, with fallback."""
        try:
            # Synchronous request for model listing
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    return sorted(models)
        except Exception:
            logger.debug("Could not query Ollama API for models, using curated list")

        # Fallback curated list
        return [
            "llama3.2",
            "llama3.1",
            "llama3",
            "mistral",
            "mixtral",
            "codellama",
            "phi3",
            "gemma2",
            "qwen2.5",
            "deepseek-r1",
        ]

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()
