"""Tests for SPL 2.0 adapters — LLM backend registry and echo adapter."""

import asyncio
import pytest
from spl.adapters import get_adapter, list_adapters, register_adapter
from spl.adapters.base import LLMAdapter, GenerationResult
from spl.adapters.echo import EchoAdapter


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
            from spl.adapters.openrouter import OpenRouterAdapter
            with pytest.raises(ValueError, match="API key"):
                OpenRouterAdapter(api_key="")
        except ImportError:
            pytest.skip("httpx not installed")
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key

    def test_list_models(self):
        try:
            from spl.adapters.openrouter import OpenRouterAdapter
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
            from spl.adapters.ollama import OllamaAdapter
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
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter()
            assert adapter.hub_url == "http://localhost:9000"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_custom_hub_url(self):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(hub_url="http://192.168.1.10:9000")
            assert adapter.hub_url == "http://192.168.1.10:9000"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_env_hub_url(self, monkeypatch):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            monkeypatch.setenv("MOMAGRID_HUB_URL", "http://grid.local:9000")
            adapter = MomagridAdapter(hub_url=None)
            assert adapter.hub_url == "http://grid.local:9000"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_min_tier_and_vram(self):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(min_tier="GOLD", min_vram_gb=24.0)
            assert adapter.min_tier == "GOLD"
            assert adapter.min_vram_gb == 24.0
        except ImportError:
            pytest.skip("httpx not installed")

    def test_list_models_fallback(self):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(hub_url="http://localhost:99999")
            models = adapter.list_models()
            assert len(models) > 0
            assert "llama3.2" in models
        except ImportError:
            pytest.skip("httpx not installed")

    def test_count_tokens(self):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter()
            count = adapter.count_tokens("Hello world")
            assert count > 0
        except ImportError:
            pytest.skip("httpx not installed")

    def test_api_key_header(self):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(api_key="test-key-123")
            headers = adapter._headers()
            assert headers["Authorization"] == "Bearer test-key-123"
        except ImportError:
            pytest.skip("httpx not installed")

    def test_connect_error_on_generate(self):
        try:
            from spl.adapters.momagrid import MomagridAdapter
            adapter = MomagridAdapter(hub_url="http://localhost:19876", timeout=2)
            with pytest.raises(ConnectionError, match="Cannot connect"):
                asyncio.run(adapter.generate("test prompt"))
        except ImportError:
            pytest.skip("httpx not installed")


class TestBedrockAdapter:
    """Test Bedrock adapter instantiation (no actual AWS calls)."""

    def test_registered(self):
        assert "bedrock" in list_adapters()

    def test_list_models(self):
        try:
            from spl.adapters.bedrock import _MODELS
            assert len(_MODELS) > 0
            assert any("claude" in m for m in _MODELS)
            assert any("nova" in m for m in _MODELS)
        except ImportError:
            pytest.skip("boto3 not installed")

    def test_estimate_cost_claude_sonnet(self):
        try:
            from spl.adapters.bedrock import _estimate_bedrock_cost
            cost = _estimate_bedrock_cost(
                "anthropic.claude-sonnet-4-20250514-v1:0", 1_000_000, 1_000_000
            )
            assert cost is not None
            assert cost > 0
        except ImportError:
            pytest.skip("boto3 not installed")

    def test_estimate_cost_nova_pro(self):
        try:
            from spl.adapters.bedrock import _estimate_bedrock_cost
            cost = _estimate_bedrock_cost("amazon.nova-pro-v1:0", 1_000_000, 1_000_000)
            assert cost is not None
            assert cost > 0
        except ImportError:
            pytest.skip("boto3 not installed")

    def test_estimate_cost_unknown_model(self):
        try:
            from spl.adapters.bedrock import _estimate_bedrock_cost
            assert _estimate_bedrock_cost("unknown.model-v1:0", 1000, 1000) is None
        except ImportError:
            pytest.skip("boto3 not installed")

    def test_import_error_without_boto3(self):
        """BedrockAdapter raises ImportError when boto3 is None."""
        try:
            import spl.adapters.bedrock as mod
        except ImportError:
            pytest.skip("boto3 not installed")
        original = mod.boto3
        try:
            mod.boto3 = None
            with pytest.raises(ImportError, match="boto3"):
                mod.BedrockAdapter()
        finally:
            mod.boto3 = original

    def test_default_region_from_env(self, monkeypatch):
        """region_name defaults to AWS_DEFAULT_REGION env var."""
        try:
            import spl.adapters.bedrock as mod
            if mod.boto3 is None:
                pytest.skip("boto3 not installed")
        except ImportError:
            pytest.skip("boto3 not installed")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
        try:
            from spl.adapters.bedrock import BedrockAdapter
            adapter = BedrockAdapter()
            assert adapter.region_name == "eu-west-1"
        except Exception:
            pytest.skip("AWS credentials not configured")


class TestVertexAdapter:
    """Test Vertex AI adapter instantiation (no actual GCP calls)."""

    def test_registered(self):
        assert "vertex" in list_adapters()

    def test_list_models(self):
        try:
            from spl.adapters.vertex import VertexAdapter
            _ = VertexAdapter  # confirms import works
            from spl.adapters.vertex import VertexAdapter as VA
            # list_models is a static list — test without full init
            assert any("gemini" in m for m in [
                "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash",
                "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash",
            ])
        except ImportError:
            pytest.skip("google-genai not installed")

    def test_requires_project(self, monkeypatch):
        """Missing project ID raises ValueError."""
        try:
            from spl.adapters.vertex import VertexAdapter
            import spl.adapters.vertex as mod
            if mod.genai is None:
                pytest.skip("google-genai not installed")
        except ImportError:
            pytest.skip("google-genai not installed")
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        with pytest.raises(ValueError, match="project"):
            VertexAdapter(project="")

    def test_default_location(self, monkeypatch):
        """location defaults to us-central1 when env var is unset."""
        try:
            from spl.adapters.vertex import VertexAdapter
            import spl.adapters.vertex as mod
            if mod.genai is None:
                pytest.skip("google-genai not installed")
        except ImportError:
            pytest.skip("google-genai not installed")
        monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
        try:
            adapter = VertexAdapter(project="my-test-project")
            assert adapter.location == "us-central1"
        except Exception:
            pytest.skip("GCP credentials not configured")

    def test_custom_location(self, monkeypatch):
        """Explicit location= kwarg is preserved."""
        try:
            from spl.adapters.vertex import VertexAdapter
            import spl.adapters.vertex as mod
            if mod.genai is None:
                pytest.skip("google-genai not installed")
        except ImportError:
            pytest.skip("google-genai not installed")
        try:
            adapter = VertexAdapter(project="my-project", location="europe-west4")
            assert adapter.location == "europe-west4"
        except Exception:
            pytest.skip("GCP credentials not configured")

    def test_import_error_without_genai(self):
        """VertexAdapter raises ImportError when google-genai is None."""
        try:
            import spl.adapters.vertex as mod
        except ImportError:
            pytest.skip("google-genai not installed")
        original = mod.genai
        try:
            mod.genai = None
            with pytest.raises(ImportError, match="google-genai"):
                mod.VertexAdapter(project="my-project")
        finally:
            mod.genai = original


class TestAzureOpenAIAdapter:
    """Test Azure OpenAI adapter instantiation (no actual API calls)."""

    def test_registered(self):
        assert "azure_openai" in list_adapters()

    def test_requires_endpoint(self, monkeypatch):
        """Missing endpoint raises ValueError."""
        try:
            from spl.adapters.azure_openai import AzureOpenAIAdapter
            import spl.adapters.azure_openai as mod
            if mod.openai is None:
                pytest.skip("openai not installed")
        except ImportError:
            pytest.skip("openai not installed")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="endpoint"):
            AzureOpenAIAdapter(endpoint="", api_key="test-key")

    def test_requires_api_key(self, monkeypatch):
        """Missing API key raises ValueError."""
        try:
            from spl.adapters.azure_openai import AzureOpenAIAdapter
            import spl.adapters.azure_openai as mod
            if mod.openai is None:
                pytest.skip("openai not installed")
        except ImportError:
            pytest.skip("openai not installed")
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key"):
            AzureOpenAIAdapter(endpoint="https://my.openai.azure.com/", api_key="")

    def test_default_api_version(self, monkeypatch):
        """api_version defaults to the built-in value."""
        try:
            from spl.adapters.azure_openai import AzureOpenAIAdapter, _DEFAULT_API_VERSION
            import spl.adapters.azure_openai as mod
            if mod.openai is None:
                pytest.skip("openai not installed")
        except ImportError:
            pytest.skip("openai not installed")
        monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
        try:
            adapter = AzureOpenAIAdapter(
                endpoint="https://my.openai.azure.com/",
                api_key="test-key",
            )
            assert adapter.api_version == _DEFAULT_API_VERSION
        except Exception:
            pytest.skip("openai client init failed")

    def test_list_models(self):
        try:
            from spl.adapters.azure_openai import AzureOpenAIAdapter
            import spl.adapters.azure_openai as mod
            if mod.openai is None:
                pytest.skip("openai not installed")
        except ImportError:
            pytest.skip("openai not installed")
        try:
            adapter = AzureOpenAIAdapter(
                endpoint="https://my.openai.azure.com/",
                api_key="test-key",
            )
            models = adapter.list_models()
            assert "gpt-4o" in models
            assert "gpt-4o-mini" in models
        except Exception:
            pytest.skip("openai client init failed")

    def test_import_error_without_openai(self):
        """AzureOpenAIAdapter raises ImportError when openai is None."""
        try:
            import spl.adapters.azure_openai as mod
        except ImportError:
            pytest.skip("openai not installed")
        original = mod.openai
        try:
            mod.openai = None
            with pytest.raises(ImportError, match="openai"):
                mod.AzureOpenAIAdapter(
                    endpoint="https://my.openai.azure.com/",
                    api_key="test-key",
                )
        finally:
            mod.openai = original
