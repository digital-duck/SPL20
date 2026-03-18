"""Tests for SPL 2.0 IR — JSON serialization of AST and plans."""

import json
import pytest
from spl2.lexer import Lexer
from spl2.parser import Parser
from spl2.analyzer import Analyzer
from spl2.optimizer import Optimizer
from spl2.ir import ast_to_json, plan_to_json, plans_to_json


def _parse(source: str):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def _plans(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    return Optimizer().optimize(analysis)


class TestAstToJson:
    def test_prompt_serialization(self):
        ast = _parse("""
            PROMPT hello
            SELECT system_role('You are helpful') AS role
            GENERATE summarize(role)
        """)
        result = ast_to_json(ast)
        assert result["type"] == "Program"
        assert len(result["statements"]) == 1
        stmt = result["statements"][0]
        assert stmt["type"] == "Prompt"
        assert stmt["name"] == "hello"
        assert len(stmt["select_items"]) == 1

    def test_workflow_serialization(self):
        ast = _parse("""
            WORKFLOW greet
                INPUT @name TEXT
                OUTPUT @greeting TEXT
            DO
                @greeting := 'Hello'
                COMMIT @greeting
            END
        """)
        result = ast_to_json(ast)
        stmt = result["statements"][0]
        assert stmt["type"] == "Workflow"
        assert stmt["name"] == "greet"
        assert len(stmt["body"]) == 2
        assert stmt["body"][0]["type"] == "Assignment"
        assert stmt["body"][1]["type"] == "Commit"

    def test_procedure_serialization(self):
        ast = _parse("""
            PROCEDURE refine_text(input_text TEXT) RETURNS TEXT
            DO
                GENERATE improve(input_text) INTO @result
                COMMIT @result
            END
        """)
        result = ast_to_json(ast)
        stmt = result["statements"][0]
        assert stmt["type"] == "Procedure"
        assert stmt["name"] == "refine_text"

    def test_evaluate_serialization(self):
        ast = _parse("""
            WORKFLOW eval_wf
                INPUT @text TEXT
                OUTPUT @label TEXT
            DO
                EVALUATE @text
                    WHEN 'positive' THEN
                        @label := 'good'
                    OTHERWISE
                        @label := 'neutral'
                END
                COMMIT @label
            END
        """)
        result = ast_to_json(ast)
        body = result["statements"][0]["body"]
        eval_stmt = body[0]
        assert eval_stmt["type"] == "Evaluate"
        assert len(eval_stmt["when_clauses"]) == 1
        assert eval_stmt["otherwise"] is not None

    def test_json_roundtrip_valid(self):
        """Verify the JSON output is valid JSON (serializable)."""
        ast = _parse("""
            WORKFLOW complex
                INPUT @data TEXT
                OUTPUT @result TEXT
            DO
                @result := 'init'
                GENERATE summarize(@data) INTO @draft
                EVALUATE @draft
                    WHEN 'good' THEN
                        COMMIT @draft
                    OTHERWISE
                        @result := 'fallback'
                        COMMIT @result
                END
            EXCEPTION
                WHEN HallucinationDetected THEN
                    @result := 'error'
                    COMMIT @result
            END
        """)
        result = ast_to_json(ast)
        serialized = json.dumps(result)
        deserialized = json.loads(serialized)
        assert deserialized["type"] == "Program"

    def test_create_function_serialization(self):
        ast = _parse("""
            CREATE FUNCTION summarize(text TEXT) RETURNS TEXT
            AS $$ Summarize: {text} $$
        """)
        result = ast_to_json(ast)
        stmt = result["statements"][0]
        assert stmt["type"] == "CreateFunction"
        assert stmt["name"] == "summarize"


class TestPlanToJson:
    def test_prompt_plan_json(self):
        plans = _plans("""
            PROMPT hello
            SELECT system_role('You are helpful') AS role
            GENERATE summarize(role)
        """)
        result = plan_to_json(plans[0])
        assert result["type"] == "PromptPlan"
        assert result["prompt_name"] == "hello"
        assert "steps" in result
        assert "output_budget" in result

    def test_workflow_plan_json(self):
        plans = _plans("""
            WORKFLOW wf
                INPUT @x TEXT
                OUTPUT @y TEXT
            DO
                GENERATE summarize(@x) INTO @y
                COMMIT @y
            END
        """)
        result = plan_to_json(plans[0])
        assert result["type"] == "WorkflowPlan"
        assert result["workflow_name"] == "wf"
        assert result["total_estimated_llm_calls"] >= 1

    def test_plans_to_json(self):
        plans = _plans("""
            PROMPT p1
            SELECT system_role('hi') AS role
            GENERATE summarize(role)

            WORKFLOW w1
                INPUT @x TEXT
                OUTPUT @y TEXT
            DO
                @y := 'done'
                COMMIT @y
            END
        """)
        result = plans_to_json(plans)
        assert len(result) == 2
        types = [r["type"] for r in result]
        assert "PromptPlan" in types
        assert "WorkflowPlan" in types

    def test_plan_json_serializable(self):
        plans = _plans("""
            WORKFLOW wf
                INPUT @x TEXT
                OUTPUT @y TEXT
            DO
                GENERATE summarize(@x) INTO @y
                EVALUATE @y
                    WHEN 'good' THEN
                        COMMIT @y
                END
            END
        """)
        serialized = json.dumps(plans_to_json(plans))
        assert serialized  # Just verify it doesn't raise
