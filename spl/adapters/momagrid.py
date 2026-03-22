"""Momagrid LLM adapter for SPL 2.0.

Submits tasks to a Momagrid hub for decentralized AI inference.
See: https://github.com/digital-duck/momagrid
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Terminal states — stop polling when we see one of these.
_TERMINAL_STATES = {"COMPLETE", "FAILED"}
# Active states — task is still in progress.
_ACTIVE_STATES = {"PENDING", "DISPATCHED", "IN_FLIGHT", "FORWARDED"}


class MomagridAdapter(LLMAdapter):
    """LLM adapter that dispatches inference to a Momagrid hub.

    Submits tasks via POST /tasks and polls GET /tasks/{id} for results.
    The hub handles agent selection, hardware-aware routing, and retries.
    """

    def __init__(
        self,
        hub_url: str | None = None,
        default_model: str = "llama3.2",
        timeout: int = 300,
        poll_interval: float = 2.0,
        min_tier: str = "BRONZE",
        min_vram_gb: float = 0.0,
        api_key: str | None = None,
    ):
        if httpx is None:
            raise ImportError(
                "httpx is required for MomagridAdapter. "
                "Install it with: pip install httpx"
            )
        self.hub_url = (
            hub_url
            or os.environ.get("MOMAGRID_HUB_URL")
            or "http://localhost:9000"
        )
        self.default_model = default_model
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.min_tier = min_tier
        self.min_vram_gb = min_vram_gb
        self.api_key = api_key or os.environ.get("MOMAGRID_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=timeout + 30)
        self._token_counter = TokenCounter(default_model)

    def _headers(self) -> dict[str, str]:
        """Build request headers, including API key if set."""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def generate(
        self,
        prompt: str,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> GenerationResult:
        """Submit a task to the Momagrid hub and wait for completion."""
        model = model or self.default_model
        task_id = str(uuid.uuid4())

        payload = {
            "task_id": task_id,
            "model": model,
            "prompt": prompt,
            "system": system or "",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "min_tier": self.min_tier,
            "min_vram_gb": self.min_vram_gb,
            "timeout_s": self.timeout,
            "priority": 1,
        }

        start = self._measure_time()

        # Submit task
        try:
            resp = await self._client.post(
                f"{self.hub_url}/tasks",
                json=payload,
                headers=self._headers(),
            )
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Momagrid hub at {self.hub_url}. "
                "Make sure the hub is running: mg hub --listen :9000"
            )

        if resp.status_code == 429:
            raise RuntimeError("Momagrid hub rate limit exceeded. Try again later.")
        if resp.status_code == 503:
            raise RuntimeError("Momagrid hub queue is full. Try again later.")
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(
                f"Momagrid task submission failed (HTTP {resp.status_code}): "
                f"{resp.text}"
            )

        submitted = resp.json()
        task_id = submitted.get("task_id", task_id)
        logger.info("Task %s submitted to Momagrid hub", task_id)

        # Poll for completion
        result = await self._poll_task(task_id)
        latency_ms = self._elapsed_ms(start)

        if result["state"] == "FAILED":
            error_msg = result.get("error", "Unknown error")
            raise RuntimeError(f"Momagrid task {task_id} failed: {error_msg}")

        content = result.get("content", "")
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        agent_latency_ms = result.get("latency_ms", latency_ms)

        logger.info(
            "Task %s completed by agent %s in %.0fms (%d tokens)",
            task_id,
            result.get("agent_name", "unknown"),
            agent_latency_ms,
            output_tokens,
        )

        return GenerationResult(
            content=content,
            model=result.get("model", model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            cost_usd=0.0,  # Momagrid uses reward credits, not USD
        )

    async def _poll_task(self, task_id: str) -> dict:
        """Poll GET /tasks/{task_id} until terminal state or timeout."""
        deadline = asyncio.get_event_loop().time() + self.timeout
        url = f"{self.hub_url}/tasks/{task_id}"

        while asyncio.get_event_loop().time() < deadline:
            try:
                resp = await self._client.get(url, headers=self._headers())
                resp.raise_for_status()
            except httpx.ConnectError:
                raise ConnectionError(
                    f"Lost connection to Momagrid hub at {self.hub_url} "
                    f"while polling task {task_id}"
                )

            data = resp.json()
            state = data.get("state", "")

            if state == "COMPLETE":
                # Result is nested under "result" key in TaskStatusResponse
                return data.get("result", data)
            if state == "FAILED":
                result = data.get("result", data)
                return {"state": "FAILED", "error": result.get("error", "Task failed")}

            logger.debug("Task %s state: %s, polling...", task_id, state)
            await asyncio.sleep(self.poll_interval)

        raise TimeoutError(
            f"Momagrid task {task_id} timed out after {self.timeout}s. "
            f"Check hub status: GET {self.hub_url}/health"
        )

    def count_tokens(self, text: str, model: str = "") -> int:
        """Count tokens using TokenCounter."""
        if model:
            counter = TokenCounter(model)
            return counter.count(text)
        return self._token_counter.count(text)

    def list_models(self) -> list[str]:
        """Query hub agents to determine available models, with fallback."""
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(
                    f"{self.hub_url}/agents",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                agents = resp.json().get("agents", [])
                models = set()
                for agent in agents:
                    for m in agent.get("models", []):
                        models.add(m)
                if models:
                    return sorted(models)
        except Exception:
            logger.debug("Could not query Momagrid hub for models, using fallback")

        # Fallback: common Ollama models (since agents run Ollama)
        return [
            "llama3.2",
            "llama3.1",
            "llama3",
            "mistral",
            "codellama",
            "phi3",
            "gemma2",
            "qwen2.5",
            "deepseek-r1",
        ]

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()

    # ---- Momagrid-specific helpers ----

    async def grid_health(self) -> dict:
        """Check hub health: GET /health."""
        resp = await self._client.get(
            f"{self.hub_url}/health",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def grid_agents(self) -> list[dict]:
        """List online agents: GET /agents."""
        resp = await self._client.get(
            f"{self.hub_url}/agents",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json().get("agents", [])
