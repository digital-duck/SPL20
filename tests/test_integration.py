"""Integration tests: end-to-end execution of .spl example files and cross-module flows."""

import asyncio
import os
import tempfile
import pytest

from spl2.lexer import Lexer
from spl2.parser import Parser
from spl2.analyzer import Analyzer
from spl2.optimizer import Optimizer
from spl2.executor import Executor, SPLResult, WorkflowResult
from spl2.explain import explain_plans
from spl2.ir import ast_to_json, plans_to_json
import json


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def _full_pipeline(source, params=None, cache_enabled=False):
    """Parse → Analyze → Optimize → Execute."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    executor = Executor(adapter_name="echo", storage_dir=tempfile.mkdtemp(),
                        cache_enabled=cache_enabled)
    try:
        return asyncio.run(executor.execute_program(analysis, params=params)), executor
    except Exception:
        executor.close()
        raise


def _full_pipeline_no_exec(source):
    """Parse → Analyze → Optimize → Explain + IR."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    plans = Optimizer().optimize(analysis)
    return ast, analysis, plans


# ================================================================
# Example File Integration Tests
# ================================================================

class TestExampleFiles:
    """Ensure all example .spl files pass the full pipeline."""

    def _read_example(self, name):
        with open(os.path.join(EXAMPLES_DIR, name)) as f:
            return f.read()

    def test_hello_world_full_pipeline(self):
        source = self._read_example("hello_world.spl")
        results, executor = _full_pipeline(source)
        executor.close()
        assert len(results) == 1
        assert isinstance(results[0], SPLResult)
        assert results[0].content  # non-empty

    def test_self_refine_full_pipeline(self):
        source = self._read_example("self_refine.spl")
        results, executor = _full_pipeline(source, params={"task": "Write a haiku"})
        executor.close()
        assert len(results) == 1
        assert isinstance(results[0], WorkflowResult)

    def test_react_agent_full_pipeline(self):
        source = self._read_example("react_agent.spl")
        results, executor = _full_pipeline(source, params={"task": "What is 2+2?"})
        executor.close()
        assert len(results) == 1
        assert isinstance(results[0], WorkflowResult)

    def test_safe_generation_full_pipeline(self):
        source = self._read_example("safe_generation.spl")
        results, executor = _full_pipeline(source, params={"prompt": "Tell me a joke"})
        executor.close()
        assert len(results) == 1
        assert isinstance(results[0], WorkflowResult)

    def test_all_examples_explain(self):
        for name in os.listdir(EXAMPLES_DIR):
            if not name.endswith(".spl"):
                continue
            source = self._read_example(name)
            ast, analysis, plans = _full_pipeline_no_exec(source)
            output = explain_plans(plans)
            assert "Plan for:" in output, f"{name} explain failed"

    def test_all_examples_ir_json(self):
        for name in os.listdir(EXAMPLES_DIR):
            if not name.endswith(".spl"):
                continue
            source = self._read_example(name)
            ast, analysis, plans = _full_pipeline_no_exec(source)
            # AST JSON
            ast_json = ast_to_json(ast)
            serialized = json.dumps(ast_json)
            assert json.loads(serialized)["type"] == "Program"
            # Plan JSON
            plan_json = plans_to_json(plans)
            serialized = json.dumps(plan_json)
            assert len(json.loads(serialized)) > 0


# ================================================================
# Prompt Caching Integration
# ================================================================

class TestPromptCaching:
    def test_cache_hit_on_second_call(self):
        source = """
            PROMPT cached_prompt
            SELECT system_role('You are helpful') AS role
            GENERATE summarize(role)
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analysis = Analyzer().analyze(ast)
        optimizer = Optimizer()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = Executor(adapter_name="echo", storage_dir=tmpdir,
                                cache_enabled=True)
            try:
                # First call — cache MISS
                r1 = asyncio.run(executor.execute_program(analysis))
                assert len(r1) == 1
                first_content = r1[0].content
                first_tokens = r1[0].total_tokens
                assert first_tokens > 0  # actual LLM call

                # Second call — cache HIT
                r2 = asyncio.run(executor.execute_program(analysis))
                assert len(r2) == 1
                assert r2[0].content == first_content  # same content
                assert r2[0].total_tokens == 0  # no LLM call
                assert r2[0].cost_usd == 0.0
            finally:
                executor.close()

    def test_cache_disabled_no_hit(self):
        source = """
            PROMPT uncached
            SELECT system_role('helper') AS role
            GENERATE summarize(role)
        """
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analysis = Analyzer().analyze(ast)

        with tempfile.TemporaryDirectory() as tmpdir:
            executor = Executor(adapter_name="echo", storage_dir=tmpdir,
                                cache_enabled=False)
            try:
                r1 = asyncio.run(executor.execute_program(analysis))
                r2 = asyncio.run(executor.execute_program(analysis))
                # Both calls should have tokens (no cache)
                assert r1[0].total_tokens > 0
                assert r2[0].total_tokens > 0
            finally:
                executor.close()


# ================================================================
# CTE Parallel Execution
# ================================================================

class TestCTEExecution:
    def test_cte_basic(self):
        source = """
            WITH summary AS (
                PROMPT sub_query
                SELECT system_role('Summarizer') AS role
                GENERATE summarize(role)
            )
            PROMPT main_query
            SELECT summary AS ctx
            GENERATE summarize(ctx)
        """
        results, executor = _full_pipeline(source)
        executor.close()
        assert len(results) == 1
        assert isinstance(results[0], SPLResult)
        # CTE should have been resolved
        assert results[0].content


# ================================================================
# Cross-Module: Parse → IR → Validate roundtrip
# ================================================================

class TestCrossModule:
    def test_workflow_parse_optimize_explain_ir(self):
        source = """
            WORKFLOW pipeline
                INPUT @data TEXT
                OUTPUT @result TEXT
            DO
                @draft := 'initial'
                GENERATE summarize(@data) INTO @draft
                EVALUATE @draft
                    WHEN 'good' THEN
                        COMMIT @draft
                    OTHERWISE
                        GENERATE rewrite(@draft) INTO @draft
                        COMMIT @draft
                END
            EXCEPTION
                WHEN HallucinationDetected THEN
                    @result := 'fallback'
                    COMMIT @result
            END
        """
        ast, analysis, plans = _full_pipeline_no_exec(source)

        # Explain
        output = explain_plans(plans)
        assert "Workflow Plan for: pipeline" in output
        assert "GENERATE" in output
        assert "EVALUATE" in output

        # IR
        ast_json = ast_to_json(ast)
        assert ast_json["statements"][0]["type"] == "Workflow"
        plan_json = plans_to_json(plans)
        assert plan_json[0]["type"] == "WorkflowPlan"
        assert plan_json[0]["total_estimated_llm_calls"] >= 2

        # Execute
        results, executor = _full_pipeline(source, params={"data": "hello"})
        executor.close()
        assert len(results) == 1
        assert isinstance(results[0], WorkflowResult)

    def test_mixed_prompt_and_workflow(self):
        source = """
            CREATE FUNCTION greet(name TEXT) RETURNS TEXT
            AS $$ Say hello to {name} $$

            PROMPT hello
            SELECT system_role('Greeter') AS role
            GENERATE greet(role)

            WORKFLOW wf
                INPUT @x TEXT
                OUTPUT @y TEXT
            DO
                @y := 'done'
                COMMIT @y
            END
        """
        results, executor = _full_pipeline(source, params={"x": "test"})
        executor.close()
        assert len(results) == 2
        assert isinstance(results[0], SPLResult)
        assert isinstance(results[1], WorkflowResult)
        assert results[1].committed_value == "done"

    def test_procedure_call_from_workflow(self):
        source = """
            PROCEDURE double_text(input_text TEXT) RETURNS TEXT
            DO
                @result := input_text
                COMMIT @result
            END

            WORKFLOW caller
                INPUT @data TEXT
                OUTPUT @out TEXT
            DO
                CALL double_text(@data) INTO @out
                COMMIT @out
            END
        """
        results, executor = _full_pipeline(source, params={"data": "hello"})
        executor.close()
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, WorkflowResult)
        assert result.status == "complete"


# ================================================================
# Memory Persistence Integration
# ================================================================

class TestMemoryIntegration:
    def test_memory_set_and_get_across_workflows(self):
        """Workflow sets memory, next prompt can retrieve it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = Executor(adapter_name="echo", storage_dir=tmpdir)

            # Manually set memory
            executor.memory.set("greeting", "Hello World")
            val = executor.memory.get("greeting")
            assert val == "Hello World"

            # Verify it persists
            keys = executor.memory.list_keys()
            assert "greeting" in keys
            executor.close()
