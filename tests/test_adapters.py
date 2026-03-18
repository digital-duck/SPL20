"""Tests for SPL 2.0 adapters — LLM backend registry and echo adapter."""

import asyncio
import pytest
from spl2.adapters import get_adapter, list_adapters, register_adapter
from spl2.adapters.base import LLMAdapter, GenerationResult
from spl2.adapters.echo import EchoAdapter


class TestAdapterRegistry:
    def test_list_includes_builtin(self):
        adapters = list_adapters()
        assert "echo" in adapters
        assert "claude_cli" in adapters

    def test_get_echo_adapter(self):
        adapter = get_adapter("echo")
        assert isinstance(adapter, EchoAdapter)

    def test_get_unknown_adapter(self):
        with pytest.raises(ValueError, match="Unknown adapter"):
            get_adapter("nonexistent_adapter_xyz")

    def test_openrouter_registered(self):
        assert "openrouter" in list_adapters()

    def test_ollama_registered(self):
        assert "ollama" in list_adapters()


class TestEchoAdapter:
    def test_generate(self):
        adapter = EchoAdapter()
        result = asyncio.run(adapter.generate("Hello world"))
        assert isinstance(result, GenerationResult)
        assert "[Echo]" in result.content
        assert "Hello world" in result.content
        assert result.model == "echo"
        assert result.cost_usd == 0.0
        assert result.input_tokens > 0
        assert result.output_tokens > 0

    def test_generate_with_system(self):
        adapter = EchoAdapter()
        result = asyncio.run(adapter.generate("test", system="Be helpful"))
        assert isinstance(result, GenerationResult)

    def test_count_tokens(self):
        adapter = EchoAdapter()
        count = adapter.count_tokens("Hello world")
        assert count > 0

    def test_list_models(self):
        models = EchoAdapter().list_models()
        assert "echo" in models

    def test_max_tokens_truncation(self):
        adapter = EchoAdapter()
        result = asyncio.run(adapter.generate("x" * 10000, max_tokens=10))
        # Echo adapter respects max_tokens * 4 chars
        assert len(result.content) <= 10 * 4 + 20  # [Echo] prefix + truncated


class TestOpenRouterAdapter:
    """Test OpenRouter adapter instantiation (no actual API calls)."""

    def test_requires_api_key(self):
        """Without API key, should raise ValueError."""
        import os
        old_key = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            from spl2.adapters.openrouter import OpenRouterAdapter
            with pytest.raises(ValueError, match="API key"):
                OpenRouterAdapter(api_key="")
        except ImportError:
            pytest.skip("httpx not installed")
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key

    def test_list_models(self):
        try:
            from spl2.adapters.openrouter import OpenRouterAdapter
            adapter = OpenRouterAdapter(api_key="test-key")
            models = adapter.list_models()
            assert len(models) > 0
            assert any("claude" in m for m in models)
        except ImportError:
            pytest.skip("httpx not installed")


class TestOllamaAdapter:
    """Test Ollama adapter instantiation (no actual server needed)."""

    def test_list_models_fallback(self):
        try:
            from spl2.adapters.ollama import OllamaAdapter
            adapter = OllamaAdapter(base_url="http://localhost:99999")
            models = adapter.list_models()
            assert len(models) > 0
            assert "llama3.2" in models
        except ImportError:
            pytest.skip("httpx not installed")


class TestMomagridAdapter:
    """Test Momagrid adapter instantiation and config (no hub needed)."""

    def test_registered(self):
        assert "momagrid" in list_adapters()

    def test_default_hub_url(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter()
            assert adapter.hub_url == "http://localhost:9000"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_custom_hub_url(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(hub_url="http://192.168.1.10:9000")
            assert adapter.hub_url == "http://192.168.1.10:9000"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_env_hub_url(self, monkeypatch):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            monkeypatch.setenv("MOMAGRID_HUB_URL", "http://grid.local:9000")
            adapter = MomagridAdapter(hub_url=None)
            assert adapter.hub_url == "http://grid.local:9000"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_min_tier_and_vram(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(min_tier="GOLD", min_vram_gb=24.0)
            assert adapter.min_tier == "GOLD"
            assert adapter.min_vram_gb == 24.0
        except ImportError:
            pytest.skip("httpx not installed")

    def test_list_models_fallback(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(hub_url="http://localhost:99999")
            models = adapter.list_models()
            assert len(models) > 0
            assert "llama3.2" in models
        except ImportError:
            pytest.skip("httpx not installed")

    def test_count_tokens(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter()
            count = adapter.count_tokens("Hello world")
            assert count > 0
        except ImportError:
            pytest.skip("httpx not installed")

    def test_api_key_header(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(api_key="test-key-123")
            headers = adapter._headers()
            assert headers["Authorization"] == "Bearer test-key-123"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_connect_error_on_generate(self):
        try:
            from spl2.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(hub_url="http://localhost:19876", timeout=2)
            with pytest.raises(ConnectionError, match="Cannot connect"):
                asyncio.run(adapter.generate("test prompt"))
        except ImportError:
            pytest.skip("httpx not installed")
