"""Google Vertex AI LLM adapter for SPL 2.0.

Uses the google-genai SDK pointed at the Vertex AI backend.
Requires: pip install google-genai

Auth — Application Default Credentials (ADC), in priority order:
  1. GOOGLE_APPLICATION_CREDENTIALS env var (path to service account JSON)
  2. gcloud auth application-default login  (local development)
  3. Attached service account / Workload Identity  (GCE, GKE, Cloud Run, etc.)

Config:
  project  — GCP project ID  (kwarg or GOOGLE_CLOUD_PROJECT env var)
  location — region           (kwarg or GOOGLE_CLOUD_LOCATION env var, default: us-central1)
"""

from __future__ import annotations

import logging
import os

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    from google import genai
    from google.genai import types
    _GenerateContentConfig = types.GenerateContentConfig
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]
    _GenerateContentConfig = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class VertexAdapter(LLMAdapter):
    """LLM adapter for Google Vertex AI (Gemini models via google-genai SDK)."""

    def __init__(
        self,
        project: str | None = None,
        location: str | None = None,
        default_model: str = "gemini-2.5-flash",
        timeout: int = 180,
    ):
        if genai is None:
            raise ImportError(
                "google-genai is required for VertexAdapter. "
                "Install it with: pip install google-genai"
            )
        self.project = project or os.environ.get("GOOGLE_CLOUD_PROJECT", "")
        if not self.project:
            raise ValueError(
                "GCP project ID required. Pass project= or set GOOGLE_CLOUD_PROJECT."
            )
        self.location = location or os.environ.get(
            "GOOGLE_CLOUD_LOCATION", "us-central1"
        )
        self.default_model = default_model
        self.timeout = timeout
        self._client = genai.Client(
            vertexai=True,
            project=self.project,
            location=self.location,
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
        """Generate a response via Google Vertex AI."""
        model = model or self.default_model

        config = _GenerateContentConfig(  # type: ignore[misc]
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        if system:
            config.system_instruction = system  # type: ignore[union-attr]

        start = self._measure_time()
        response = await self._client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        latency_ms = self._elapsed_ms(start)

        content = response.text or ""

        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0
        total_tokens = (
            usage.total_token_count if usage else input_tokens + output_tokens
        )

        cost_usd = TokenCounter(model).estimate_cost(input_tokens, output_tokens)

        logger.debug(
            "Vertex AI %s — %d in / %d out tokens, %.0f ms",
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
        """Count tokens using TokenCounter."""
        if model:
            return TokenCounter(model).count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """List available Gemini models on Vertex AI."""
        return [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
