"""AWS Bedrock LLM adapter for SPL 2.0.

Uses the Bedrock Runtime Converse API, which works across all model families
(Anthropic Claude, Meta Llama, Amazon Nova, etc.).

Requires: pip install boto3

Credentials (in priority order):
  1. Explicit kwargs: aws_access_key_id / aws_secret_access_key
  2. Environment: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN
  3. Named profile: profile_name= (reads ~/.aws/credentials)
  4. IAM role (EC2/ECS/Lambda instance profile — no config needed)

Region: region_name= kwarg or AWS_DEFAULT_REGION env var (default: us-east-1)

Cross-region inference profiles (e.g. us.anthropic.claude-sonnet-4-...) are
supported — just pass the full profile ARN as model=.
"""

from __future__ import annotations

import asyncio
import logging
import os

from spl.adapters.base import LLMAdapter, GenerationResult
from spl.token_counter import TokenCounter

try:
    import boto3
    import botocore.config
    from botocore.exceptions import BotoCoreError, ClientError
    _BotocoreConfig = botocore.config.Config
except ImportError:
    boto3 = None  # type: ignore[assignment]
    _BotocoreConfig = None  # type: ignore[assignment]
    BotoCoreError = Exception  # type: ignore[assignment,misc]
    ClientError = Exception  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Bedrock model IDs accessible via the Converse API
_MODELS: list[str] = [
    # Anthropic Claude 4.x
    "anthropic.claude-opus-4-0-20250514-v1:0",
    "anthropic.claude-sonnet-4-20250514-v1:0",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
    # Anthropic Claude 3.5
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    # Anthropic Claude 3
    "anthropic.claude-3-opus-20240229-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    # Meta Llama 3
    "meta.llama3-70b-instruct-v1:0",
    "meta.llama3-8b-instruct-v1:0",
    # Amazon Nova
    "amazon.nova-pro-v1:0",
    "amazon.nova-lite-v1:0",
    "amazon.nova-micro-v1:0",
]

# Pricing per 1M tokens (input, output) in USD — approximate on-demand rates
# https://aws.amazon.com/bedrock/pricing/
_BEDROCK_PRICING: dict[str, tuple[float, float]] = {
    "anthropic.claude-opus-4": (15.0, 75.0),
    "anthropic.claude-sonnet-4": (3.0, 15.0),
    "anthropic.claude-haiku-4": (0.25, 1.25),
    "anthropic.claude-3-5-sonnet": (3.0, 15.0),
    "anthropic.claude-3-5-haiku": (0.80, 4.0),
    "anthropic.claude-3-opus": (15.0, 75.0),
    "anthropic.claude-3-sonnet": (3.0, 15.0),
    "anthropic.claude-3-haiku": (0.25, 1.25),
    "meta.llama3-70b": (2.65, 3.50),
    "meta.llama3-8b": (0.22, 0.22),
    "amazon.nova-pro": (0.80, 3.20),
    "amazon.nova-lite": (0.06, 0.24),
    "amazon.nova-micro": (0.035, 0.14),
}


def _estimate_bedrock_cost(
    model: str, input_tokens: int, output_tokens: int
) -> float | None:
    lower = model.lower()
    for prefix, (inp_price, out_price) in _BEDROCK_PRICING.items():
        if lower.startswith(prefix):
            cost = (
                input_tokens / 1_000_000 * inp_price
                + output_tokens / 1_000_000 * out_price
            )
            return round(cost, 6)
    return None


class BedrockAdapter(LLMAdapter):
    """LLM adapter for AWS Bedrock using the Converse API."""

    def __init__(
        self,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        profile_name: str | None = None,
        default_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        timeout: int = 180,
    ):
        if boto3 is None:
            raise ImportError(
                "boto3 is required for BedrockAdapter. "
                "Install it with: pip install boto3"
            )
        self.region_name = (
            region_name or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )
        self.default_model = default_model
        self.timeout = timeout

        session = boto3.Session(
            aws_access_key_id=(
                aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
            ),
            aws_secret_access_key=(
                aws_secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
            ),
            aws_session_token=(
                aws_session_token or os.environ.get("AWS_SESSION_TOKEN")
            ),
            region_name=self.region_name,
            profile_name=profile_name,
        )
        self._client = session.client(
            "bedrock-runtime",
            config=_BotocoreConfig(  # type: ignore[misc]
                read_timeout=timeout,
                connect_timeout=30,
            ),
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
        """Generate a response via AWS Bedrock Converse API."""
        model = model or self.default_model

        kwargs: dict = {
            "modelId": model,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system:
            kwargs["system"] = [{"text": system}]

        start = self._measure_time()
        try:
            response = await asyncio.to_thread(self._client.converse, **kwargs)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Bedrock API error: {exc}") from exc
        latency_ms = self._elapsed_ms(start)

        # Extract text from the response message
        content = ""
        output_msg = response.get("output", {}).get("message", {})
        for block in output_msg.get("content", []):
            if "text" in block:
                content += block["text"]

        usage = response.get("usage", {})
        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)
        total_tokens = input_tokens + output_tokens

        cost_usd = _estimate_bedrock_cost(model, input_tokens, output_tokens)

        logger.debug(
            "Bedrock %s — %d in / %d out tokens, %.0f ms",
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
        """List supported Bedrock model IDs."""
        return list(_MODELS)
