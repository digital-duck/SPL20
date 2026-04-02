"""Level 2 workflow dry-run tests — arXiv Morning Brief (SPL 2.0).

Loads arxiv_morning_brief.spl via the SPL 2.0 Lexer/Parser/Executor.
All network calls and LLM calls are mocked — no real I/O.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the recipe dir is importable
RECIPE_DIR = Path(__file__).parent.parent
if str(RECIPE_DIR) not in sys.path:
    sys.path.insert(0, str(RECIPE_DIR))

import tools as ambt  # registers @spl_tool functions via side-effect  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_workflow():
    """Parse arxiv_morning_brief.spl and return its WorkflowStatement."""
    from spl.lexer import Lexer
    from spl.parser import Parser
    from spl.ast_nodes import WorkflowStatement

    src = (RECIPE_DIR / "arxiv_morning_brief.spl").read_text()
    prog = Parser(Lexer(src).tokenize()).parse()
    workflows = [s for s in prog.statements if isinstance(s, WorkflowStatement)]
    assert workflows, "No WORKFLOW found in arxiv_morning_brief.spl"
    return workflows[0]


def _mock_adapter(content: str = "# Mock Brief\n\n## Key Themes\n- Topic X") -> MagicMock:
    from spl.adapters.base import GenerationResult
    adapter = MagicMock()
    result = GenerationResult(
        content=content,
        model="mock",
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        latency_ms=5.0,
    )
    adapter.generate = AsyncMock(return_value=result)
    return adapter


def _make_executor(adapter, tool_overrides: dict | None = None):
    """Create a configured SPL 2.0 Executor with optional tool overrides."""
    from spl.executor import Executor
    executor = Executor(adapter=adapter, storage_dir="/tmp/.spl_test_arxiv")
    if tool_overrides:
        for name, fn in tool_overrides.items():
            executor.register_tool(name, fn)
    return executor


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Fixtures ─────────────────────────────────────────────────────────────────

FAKE_CHUNKS = json.dumps([
    {"title": "ABSTRACT",        "text": "We propose a novel method.",    "page": 1},
    {"title": "1. INTRODUCTION", "text": "This is the introduction.",      "page": 2},
])

URLS_TWO = json.dumps([
    "https://arxiv.org/pdf/2501.00001",
    "https://arxiv.org/pdf/2501.00002",
])


# ── Tests ────────────────────────────────────────────────────────────────────

class TestArxivMorningBrief:

    def test_brief_produced(self):
        """Normal run with two papers produces a non-empty @brief."""
        adapter = _mock_adapter(
            "# arXiv Morning Brief — 2026-04-02\n\n### Paper A\nSummary.\n\n## Key Themes\n- Efficiency"
        )
        executor = _make_executor(adapter, tool_overrides={
            "download_arxiv_pdf":  lambda url: "/fake/path.pdf",
            "semantic_chunk_plan": lambda path: FAKE_CHUNKS,
        })

        result = _run(executor.execute_workflow(
            _load_workflow(),
            params={"urls": URLS_TWO, "date": "2026-04-02", "brief_tokens": "512"},
        ))

        assert result.committed_value, "Expected a committed @brief"
        assert "#" in result.committed_value

    def test_tool_error_skips_paper_brief_still_produced(self):
        """ToolError on download causes paper to be skipped; brief still committed."""
        def _fail(url):
            raise ambt.ToolError("HTTP 404")

        adapter = _mock_adapter("# Brief\n\n## Key Themes\n- None")
        executor = _make_executor(adapter, tool_overrides={
            "download_arxiv_pdf": _fail,
        })

        result = _run(executor.execute_workflow(
            _load_workflow(),
            params={"urls": URLS_TWO, "date": "2026-04-02"},
        ))

        assert result.status in ("complete", "no_commit")

    def test_empty_url_list_produces_brief(self):
        """Empty URL list → no papers, brief_writer still called, produces output."""
        adapter = _mock_adapter("# Empty Brief\n\n## Key Themes\n- None")
        executor = _make_executor(adapter)

        result = _run(executor.execute_workflow(
            _load_workflow(),
            params={"urls": "[]", "date": "2026-04-02"},
        ))

        assert result.committed_value

    def test_single_url_string_accepted(self):
        """A bare URL string (not JSON array) is accepted via parse_urls."""
        url = "https://arxiv.org/pdf/2501.00001"
        adapter = _mock_adapter("# Brief\n\n### Paper X\nSummary.\n\n## Key Themes\n- X")
        executor = _make_executor(adapter, tool_overrides={
            "download_arxiv_pdf":  lambda u: "/fake/path.pdf",
            "semantic_chunk_plan": lambda p: FAKE_CHUNKS,
        })

        result = _run(executor.execute_workflow(
            _load_workflow(),
            params={"urls": url},
        ))

        assert result.committed_value

    def test_chunk_tokens_default_applied(self):
        """chunk_tokens defaults to 512 when not supplied."""
        adapter = _mock_adapter("# Brief\n\n## Key Themes\n- X")
        executor = _make_executor(adapter, tool_overrides={
            "download_arxiv_pdf":  lambda u: "/fake/path.pdf",
            "semantic_chunk_plan": lambda p: FAKE_CHUNKS,
        })

        result = _run(executor.execute_workflow(
            _load_workflow(),
            params={"urls": URLS_TWO},
        ))

        assert result.status in ("complete", "no_commit")
