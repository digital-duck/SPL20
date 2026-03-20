"""SPL 2.0 configuration management via dd-config.

Configuration lives at ~/.spl/config.yaml with smart defaults.
"""

from __future__ import annotations

from pathlib import Path

from dd_config import Config

SPL_HOME = Path.home() / ".spl"
CONFIG_PATH = SPL_HOME / "config.yaml"
LOG_DIR = SPL_HOME / "logs"

# Smart defaults for SPL 2.0
DEFAULTS: dict = {
    "adapter": "echo",
    "model": "",
    "cache": False,
    "cache_ttl": 3600,
    "storage_dir": ".spl",
    "log_level": "info",
    "log_console": False,
    # ── text2spl compiler ─────────────────────────────────────────────────────
    # Separate adapter/model from the runtime adapter used by `spl2 run`.
    # During development, claude_cli + claude-sonnet-4-6 is the recommended
    # compiler (subscription billing, zero VRAM, highest code quality).
    # Future options: ollama + qwen2.5-coder, or a fine-tuned SPL specialty model.
    "text2spl": {
        "adapter": "claude_cli",          # dedicated compiler adapter
        "model":   "claude-sonnet-4-6",   # dedicated compiler model
        "mode":    "auto",
        "validate": True,
        "max_retries": 2,
    },
    # ── code_rag ───────────────────────────────────────────────────────────────
    # Code-RAG: ChromaDB-backed store of (description, SPL source) pairs.
    # When enabled, text2spl retrieves semantically similar examples at compile
    # time instead of using static hand-written examples.
    # auto_capture: automatically add every validated compile result to the DB.
    "code_rag": {
        "enabled":      True,
        "storage_dir":  ".spl/code_rag",
        "collection":   "spl_code_rag",
        "top_k":        4,
        "auto_capture": True,
    },
    "adapters": {
        "ollama": {
            "base_url": "http://localhost:11434",
            "default_model": "llama3.2",
            "timeout": 120,
        },
        "openrouter": {
            "default_model": "anthropic/claude-sonnet-4-5",
            "timeout": 180,
        },
        "anthropic": {
            "default_model": "claude-sonnet-4-20250514",
            "timeout": 180,
        },
        "openai": {
            "default_model": "gpt-4o",
            "timeout": 180,
        },
        "google": {
            "default_model": "gemini-2.5-flash",
            "timeout": 180,
        },
        "deepseek": {
            "default_model": "deepseek-chat",
            "timeout": 180,
        },
        "qwen": {
            "default_model": "qwen-plus",
            "timeout": 180,
        },
    },
}


def load_config() -> Config:
    """Load SPL config from ~/.spl/config.yaml, creating defaults if missing."""
    if CONFIG_PATH.exists():
        cfg = Config.load(str(CONFIG_PATH))
        # Merge defaults for any missing keys
        defaults_cfg = Config.from_dict(DEFAULTS)
        merged = defaults_cfg.merge(cfg)
        return merged
    else:
        return Config.from_dict(DEFAULTS)


def save_config(cfg: Config) -> None:
    """Save SPL config to ~/.spl/config.yaml."""
    SPL_HOME.mkdir(parents=True, exist_ok=True)
    cfg.save(str(CONFIG_PATH))


def ensure_defaults() -> Config:
    """Create ~/.spl/config.yaml with defaults if it doesn't exist. Return config."""
    cfg = load_config()
    if not CONFIG_PATH.exists():
        save_config(cfg)
    return cfg
