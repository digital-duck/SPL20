"""Tests for SPL 2.0 explain — execution plan rendering."""

import pytest
from spl2.lexer import Lexer
from spl2.parser import Parser
from spl2.analyzer import Analyzer
from spl2.optimizer import Optimizer
from spl2.explain import explain_plan, explain_plans


def _explain(source: str) -> str:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    plans = Optimizer().optimize(analysis)
    return explain_plans(plans)


class TestPromptExplain:
    def test_basic_prompt(self):
        output = _explain("""
            PROMPT hello
            SELECT system_role('You are helpful') AS role
            GENERATE summarize(role)
        """)
        assert "Execution Plan for: hello" in output
        assert "Token Allocation:" in output
        assert "Output Budget" in output

    def test_budget_display(self):
        output = _explain("""
            PROMPT budgeted
            WITH BUDGET 10000 TOKENS
            SELECT context.doc AS doc
            GENERATE summarize(doc) WITH OUTPUT BUDGET 3000 TOKENS
        """)
        assert "10,000 tokens" in output
        assert "3,000" in output

    def test_model_display(self):
        output = _explain("""
            PROMPT with_model
            USING MODEL 'claude-sonnet'
            SELECT context.doc AS doc
            GENERATE summarize(doc)
        """)
        assert "claude-sonnet" in output


class TestWorkflowExplain:
    def test_basic_workflow(self):
        output = _explain("""
            WORKFLOW greet
                INPUT @name TEXT
                OUTPUT @greeting TEXT
            DO
                @greeting := 'Hello'
                COMMIT @greeting
            END
        """)
        assert "Workflow Plan for: greet" in output
        assert "@name" in output
        assert "@greeting" in output
        assert "Execution Steps:" in output

    def test_workflow_with_generate(self):
        output = _explain("""
            WORKFLOW gen_wf
                INPUT @prompt TEXT
                OUTPUT @result TEXT
            DO
                GENERATE summarize(@prompt) INTO @result
                COMMIT @result
            END
        """)
        assert "LLM call" in output
        assert "GENERATE" in output

    def test_workflow_with_evaluate(self):
        output = _explain("""
            WORKFLOW eval_wf
                INPUT @text TEXT
                OUTPUT @result TEXT
            DO
                EVALUATE @text
                    WHEN 'positive' THEN
                        @result := 'good'
                    OTHERWISE
                        @result := 'neutral'
                END
                COMMIT @result
            END
        """)
        assert "EVALUATE" in output
        assert "WHEN" in output
        assert "semantic" in output

    def test_workflow_with_exceptions(self):
        output = _explain("""
            WORKFLOW safe_wf
                INPUT @input TEXT
                OUTPUT @result TEXT
            DO
                GENERATE summarize(@input) INTO @result
                COMMIT @result
            EXCEPTION
                WHEN HallucinationDetected THEN
                    @result := 'fallback'
            END
        """)
        assert "Exception Handlers:" in output
        assert "HallucinationDetected" in output

    def test_multiple_plans(self):
        output = _explain("""
            PROMPT p1
            SELECT system_role('helper') AS role
            GENERATE summarize(role)

            WORKFLOW w1
                INPUT @x TEXT
                OUTPUT @y TEXT
            DO
                @y := 'done'
                COMMIT @y
            END
        """)
        assert "Execution Plan for: p1" in output
        assert "Workflow Plan for: w1" in output
