"""Tests for SPL 2.0 Semantic Analyzer."""

import pytest
from spl2 import parse, validate
from spl2.analyzer import AnalysisError, infer_condition_type
from spl2.ast_nodes import SemanticCondition, ComparisonCondition, Literal


class TestAnalyzerSPL1Compat:
    """SPL 1.0 analyzer backward compatibility."""

    def test_valid_prompt(self):
        result = validate("""
            PROMPT test
            WITH BUDGET 5000 tokens
            SELECT system_role("test")
            GENERATE response()
            WITH OUTPUT BUDGET 1000 tokens
        """)
        assert result.is_valid
        assert 'test' in result.defined_prompts

    def test_duplicate_prompt(self):
        with pytest.raises(AnalysisError, match="already defined"):
            validate("""
                PROMPT test
                SELECT system_role("test")
                GENERATE response();

                PROMPT test
                SELECT system_role("test2")
                GENERATE response2()
            """)

    def test_budget_warning(self):
        result = validate("""
            PROMPT test
            WITH BUDGET 1000 tokens
            SELECT context.data AS data LIMIT 800 tokens
            GENERATE response(data)
            WITH OUTPUT BUDGET 500 tokens
        """)
        assert len(result.warnings) > 0

    def test_temperature_validation(self):
        with pytest.raises(AnalysisError, match="Temperature"):
            validate("""
                PROMPT test
                SELECT system_role("test")
                GENERATE response()
                WITH TEMPERATURE 5.0
            """)


class TestAnalyzerSPL2:
    """SPL 2.0 analyzer tests."""

    def test_valid_workflow(self):
        result = validate("""
            WORKFLOW simple
            INPUT: @task text
            OUTPUT: @result text
            DO
              COMMIT @result
            END
        """)
        assert result.is_valid
        assert 'simple' in result.defined_workflows

    def test_duplicate_workflow(self):
        with pytest.raises(AnalysisError, match="already defined"):
            validate("""
                WORKFLOW test
                DO
                  COMMIT @x
                END;

                WORKFLOW test
                DO
                  COMMIT @y
                END
            """)

    def test_valid_procedure(self):
        result = validate("""
            PROCEDURE greet(name)
            RETURNS text
            DO
              COMMIT @name
            END
        """)
        assert result.is_valid
        assert 'greet' in result.defined_procedures

    def test_unknown_exception_warning(self):
        result = validate("""
            WORKFLOW test
            DO
              COMMIT @x
            EXCEPTION
              WHEN UnknownError THEN
                COMMIT @x
            END
        """)
        assert len(result.warnings) > 0
        assert "Unknown exception" in result.warnings[0].message

    def test_valid_exception_types(self):
        result = validate("""
            WORKFLOW test
            DO
              COMMIT @x
            EXCEPTION
              WHEN HallucinationDetected THEN
                COMMIT @x
              WHEN OTHERS THEN
                COMMIT @x
            END
        """)
        # No warnings about exception types
        exception_warnings = [w for w in result.warnings if "exception" in w.message.lower()]
        assert len(exception_warnings) == 0

    def test_security_classification_warning(self):
        result = validate("""
            WORKFLOW test
            INPUT: @data text
            SECURITY: CLASSIFICATION: topsecret
            DO
              COMMIT @data
            END
        """)
        assert any("classification" in w.message.lower() for w in result.warnings)

    def test_mixed_spl1_spl2(self):
        result = validate("""
            CREATE FUNCTION summarize(text)
            RETURNS text
            AS $$ Summarize: {text} $$;

            PROMPT hello
            SELECT system_role("test")
            GENERATE response();

            WORKFLOW flow
            INPUT: @task text
            DO
              COMMIT @task
            END
        """)
        assert result.is_valid
        assert len(result.defined_functions) == 1
        assert len(result.defined_prompts) == 1
        assert len(result.defined_workflows) == 1


class TestConditionTypeInference:
    """Test condition type inference."""

    def test_semantic_condition(self):
        cond = SemanticCondition(semantic_value="coherent")
        assert infer_condition_type(cond) == 'semantic'

    def test_comparison_condition(self):
        cond = ComparisonCondition(operator=">", right=Literal(value=0.8, literal_type="float"))
        assert infer_condition_type(cond) == 'deterministic'
