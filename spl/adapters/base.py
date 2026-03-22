"""Abstract base class for LLM adapters."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class GenerationResult:
    """Result from an LLM generation call."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float | None = None


class LLMAdapter(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Generate a response from the LLM."""
        ...

    @abstractmethod
    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens in text for the given model."""
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this adapter."""
        ...

    def _measure_time(self):
        return time.perf_counter()

    def _elapsed_ms(self, start: float) -> float:
        return (time.perf_counter() - start) * 1000
