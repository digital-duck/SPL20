"""Echo adapter: returns the prompt as the response. Useful for testing."""

from __future__ import annotations
from spl2.adapters.base import LLMAdapter, GenerationResult


class EchoAdapter(LLMAdapter):
    """Echo adapter that returns the prompt as the response.

    Useful for testing and development without an LLM backend.
    """

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        start = self._measure_time()
        content = f"[Echo] {prompt[:max_tokens * 4]}"
        latency = self._elapsed_ms(start)
        input_tokens = len(prompt) // 4
        output_tokens = len(content) // 4
        return GenerationResult(
            content=content,
            model=model or "echo",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency,
            cost_usd=0.0,
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        return len(text) // 4

    def list_models(self) -> list[str]:
        return ["echo"]
