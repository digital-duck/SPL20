"""Tests for SPL 2.0 executor — runtime execution of prompts and workflows."""

import asyncio
import pytest
from spl2.lexer import Lexer
from spl2.parser import Parser
from spl2.analyzer import Analyzer
from spl2.executor import (
    Executor, SPLResult, WorkflowResult, WorkflowState,
    HallucinationDetected, MaxIterationsReached, SPLWorkflowError,
    EXCEPTION_CLASSES,
)
from spl2.adapters.echo import EchoAdapter


def _analyze(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return Analyzer().analyze(ast)


def _run(source: str, params=None):
    analysis = _analyze(source)
    executor = Executor(adapter_name="echo", storage_dir="/tmp/.spl_test")
    try:
        return asyncio.run(executor.execute_program(analysis, params=params))
    finally:
        executor.close()


# ================================================================
# WorkflowState Tests
# ================================================================

class TestWorkflowState:
    def test_initial_state(self):
        state = WorkflowState()
        assert state.variables == {}
        assert state.committed is False

    def test_params_init(self):
        state = WorkflowState({"name": "Alice"})
        assert state.get_var("name") == "Alice"

    def test_set_get_var(self):
        state = WorkflowState()
        state.set_var("x", "hello")
        assert state.get_var("x") == "hello"
        assert state.get_var("missing") == ""


# ================================================================
# Exception Classes
# ================================================================

class TestExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(HallucinationDetected, SPLWorkflowError)
        assert issubclass(MaxIterationsReached, SPLWorkflowError)

    def test_exception_classes_registry(self):
        assert "HallucinationDetected" in EXCEPTION_CLASSES
        assert "RefusalToAnswer" in EXCEPTION_CLASSES
        assert len(EXCEPTION_CLASSES) == 8


# ================================================================
# Prompt Execution
# ================================================================

class TestPromptExecution:
    def test_basic_prompt(self):
        results = _run("""
            PROMPT hello
            SELECT system_role('You are helpful') AS role
            GENERATE summarize(role)
        """)
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SPLResult)
        assert result.content  # Echo adapter returns non-empty
        assert result.model == "echo"
        assert result.latency_ms >= 0

    def test_prompt_with_params(self):
        results = _run("""
            PROMPT qa
            SELECT context.question AS q
            GENERATE summarize(q)
        """, params={"question": "What is SPL?"})
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SPLResult)


# ================================================================
# Workflow Execution
# ================================================================

class TestWorkflowExecution:
    def test_assignment_and_commit(self):
        results = _run("""
            WORKFLOW simple
                INPUT @name TEXT
                OUTPUT @greeting TEXT
            DO
                @greeting := 'Hello world'
                COMMIT @greeting
            END
        """, params={"name": "Alice"})
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, WorkflowResult)
        assert result.status == "complete"
        assert result.committed_value == "Hello world"

    def test_generate_into(self):
        results = _run("""
            WORKFLOW gen
                INPUT @prompt TEXT
                OUTPUT @result TEXT
            DO
                GENERATE summarize(@prompt) INTO @result
                COMMIT @result
            END
        """, params={"prompt": "Test input"})
        result = results[0]
        assert isinstance(result, WorkflowResult)
        assert result.status == "complete"
        assert result.total_llm_calls >= 1
        assert result.committed_value  # Echo adapter returns something

    def test_evaluate_with_otherwise(self):
        results = _run("""
            WORKFLOW eval_wf
                INPUT @score TEXT
                OUTPUT @label TEXT
            DO
                EVALUATE @score
                    WHEN > 0.8 THEN
                        @label := 'high'
                    OTHERWISE
                        @label := 'low'
                END
                COMMIT @label
            END
        """, params={"score": "0.5"})
        result = results[0]
        assert result.committed_value == "low"

    def test_evaluate_high_score(self):
        results = _run("""
            WORKFLOW eval_wf
                INPUT @score TEXT
                OUTPUT @label TEXT
            DO
                EVALUATE @score
                    WHEN > 0.8 THEN
                        @label := 'high'
                    OTHERWISE
                        @label := 'low'
                END
                COMMIT @label
            END
        """, params={"score": "0.9"})
        result = results[0]
        assert result.committed_value == "high"

    def test_while_loop(self):
        results = _run("""
            WORKFLOW counter
                INPUT @n TEXT
                OUTPUT @count TEXT
            DO
                @count := '0'
                @i := '0'
                WHILE @i < 3 DO
                    @i := @i + '1'
                    @count := @i
                END
                COMMIT @count
            END
        """, params={"n": "3"})
        result = results[0]
        assert result.status == "complete"
        # Loop should have executed

    def test_raise_and_handle(self):
        results = _run("""
            WORKFLOW safe
                INPUT @input TEXT
                OUTPUT @result TEXT
            DO
                DO
                    RAISE HallucinationDetected 'test error'
                EXCEPTION
                    WHEN HallucinationDetected THEN
                        @result := 'caught'
                END
                COMMIT @result
            END
        """, params={"input": "test"})
        result = results[0]
        assert result.committed_value == "caught"

    def test_raise_unhandled(self):
        with pytest.raises(HallucinationDetected):
            _run("""
                WORKFLOW bad
                    INPUT @input TEXT
                    OUTPUT @result TEXT
                DO
                    RAISE HallucinationDetected 'oops'
                    COMMIT @result
                END
            """, params={"input": "test"})

    def test_do_block_exception_others(self):
        results = _run("""
            WORKFLOW catch_all
                INPUT @input TEXT
                OUTPUT @result TEXT
            DO
                DO
                    RAISE RefusalToAnswer 'nope'
                EXCEPTION
                    WHEN OTHERS THEN
                        @result := 'handled'
                END
                COMMIT @result
            END
        """, params={"input": "x"})
        result = results[0]
        assert result.committed_value == "handled"

    def test_no_commit_status(self):
        results = _run("""
            WORKFLOW no_commit
                INPUT @x TEXT
                OUTPUT @y TEXT
            DO
                @y := 'value'
            END
        """, params={"x": "test"})
        result = results[0]
        assert result.status == "no_commit"
        assert result.committed_value is None

    def test_workflow_output_variables(self):
        results = _run("""
            WORKFLOW vars
                INPUT @a TEXT
                OUTPUT @b TEXT
            DO
                @b := 'output_value'
                COMMIT @b
            END
        """, params={"a": "input"})
        result = results[0]
        assert "b" in result.output
        assert result.output["b"] == "output_value"


# ================================================================
# Workflow-level exception handlers
# ================================================================

class TestWorkflowExceptionHandlers:
    def test_workflow_level_handler(self):
        results = _run("""
            WORKFLOW wf_handler
                INPUT @x TEXT
                OUTPUT @result TEXT
            DO
                RAISE HallucinationDetected 'boom'
            EXCEPTION
                WHEN HallucinationDetected THEN
                    @result := 'workflow_caught'
                    COMMIT @result
            END
        """, params={"x": "test"})
        result = results[0]
        assert result.committed_value == "workflow_caught"
