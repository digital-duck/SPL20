"""Tests for Recipe 49: Regulatory News Monitor (batch_size issue)."""

import asyncio
import os
import pytest
import json
from spl.lexer import Lexer
from spl.parser import Parser
from spl.analyzer import Analyzer
from spl.executor import Executor, WorkflowResult
from cookbook.tools.finance_helpers import read_news_feed, get_list_length

def _analyze(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return Analyzer().analyze(ast)

def _run_with_tools(source: str, params=None):
    analysis = _analyze(source)
    # Use a temporary storage dir to avoid polluting workspace
    import tempfile
    storage_dir = tempfile.mkdtemp()
    executor = Executor(adapter_name="echo", storage_dir=storage_dir)
    
    # Register the specific tools from finance_helpers
    executor.register_tool("read_news_feed", read_news_feed)
    executor.register_tool("get_list_length", get_list_length)
    
    try:
        results = asyncio.run(executor.execute_program(analysis, params=params))
        return results, executor
    except Exception:
        executor.close()
        raise

class TestRecipe49BatchSize:
    """Verify the fix for @batch_size calculation in Recipe 49."""

    def test_batch_size_is_correct(self):
        # The specific repro case that failed
        source = """
        WORKFLOW repro_workflow
        DO
          CALL read_news_feed('cookbook/49_regulatory_news_audit/data/news_feed.txt') INTO @news_batch
          CALL get_list_length(@news_batch) INTO @batch_size
          COMMIT @batch_size
        END
        """
        results, executor = _run_with_tools(source)
        try:
            assert len(results) == 1
            result = results[0]
            assert isinstance(result, WorkflowResult)
            # The expected batch size for the sample data is 5
            assert result.committed_value == "5"
            
            # Verify @news_batch is a valid JSON list of 5 items
            news_batch_raw = result.output.get("news_batch")
            news_batch = json.loads(news_batch_raw)
            assert isinstance(news_batch, list)
            assert len(news_batch) == 5
        finally:
            executor.close()

    def test_news_feed_content_parsing(self):
        """Ensure BATCH markers are correctly handled by the tool."""
        source = """
        WORKFLOW check_content
        DO
          CALL read_news_feed('cookbook/49_regulatory_news_audit/data/news_feed.txt') INTO @news_batch
          @first_item := @news_batch[0]
          COMMIT @first_item
        END
        """
        results, executor = _run_with_tools(source)
        try:
            result = results[0]
            # First item should not contain the word 'BATCH' but the text after it
            assert "Central Bank raises benchmark rates" in result.committed_value
            assert "BATCH" not in result.committed_value
        finally:
            executor.close()
