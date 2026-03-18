"""Tests for SPL 2.0 optimizer — execution planning for prompts and workflows."""

import pytest
from spl2.lexer import Lexer
from spl2.parser import Parser
from spl2.analyzer import Analyzer
from spl2.optimizer import Optimizer, ExecutionPlan, WorkflowPlan


def _optimize(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    analysis = Analyzer().analyze(ast)
    return Optimizer().optimize(analysis)


# ================================================================
# Prompt Plan Tests (SPL 1.0 compat)
# ================================================================

class TestPromptPlan:
    def test_basic_prompt_plan(self):
        plans = _optimize("""
            PROMPT hello
            SELECT system_role('You are helpful') AS role
            GENERATE summarize(role)
        """)
        assert len(plans) == 1
        plan = plans[0]
        assert isinstance(plan, ExecutionPlan)
        assert plan.prompt_name == "hello"
        assert plan.output_budget > 0

    def test_budget_allocation(self):
        plans = _optimize("""
            PROMPT budgeted
            WITH BUDGET 10000 TOKENS
            USING MODEL 'gpt-4'
            SELECT
                system_role('assistant') AS role,
                context.question AS q LIMIT 2000 TOKENS
            GENERATE summarize(q) WITH OUTPUT BUDGET 3000 TOKENS
        """)
        plan = plans[0]
        assert plan.total_budget == 10000
        assert plan.output_budget == 3000
        assert plan.total_input_tokens > 0
        assert plan.estimated_cost is not None

    def test_multiple_select_items(self):
        plans = _optimize("""
            PROMPT multi
            SELECT
                system_role('helper') AS sys,
                context.doc AS doc LIMIT 5000 TOKENS,
                memory.get('prev') AS prev
            GENERATE summarize(doc)
        """)
        plan = plans[0]
        assert len(plan.steps) == 3
        ops = [s.operation for s in plan.steps]
        assert "system_role" in ops
        assert "load_context" in ops
        assert "memory_get" in ops


# ================================================================
# Workflow Plan Tests (SPL 2.0)
# ================================================================

class TestWorkflowPlan:
    def test_basic_workflow_plan(self):
        plans = _optimize("""
            WORKFLOW greet
                INPUT @name TEXT
                OUTPUT @greeting TEXT
            DO
                @greeting := 'Hello'
                COMMIT @greeting
            END
        """)
        assert len(plans) == 1
        plan = plans[0]
        assert isinstance(plan, WorkflowPlan)
        assert plan.workflow_name == "greet"
        assert "name" in plan.inputs
        assert "greeting" in plan.outputs

    def test_workflow_with_generate(self):
        plans = _optimize("""
            WORKFLOW gen_wf
                INPUT @prompt TEXT
                OUTPUT @result TEXT
            DO
                GENERATE summarize(@prompt) INTO @result
                COMMIT @result
            END
        """)
        plan = plans[0]
        assert plan.total_estimated_llm_calls >= 1

    def test_workflow_with_evaluate(self):
        plans = _optimize("""
            WORKFLOW eval_wf
                INPUT @text TEXT
                OUTPUT @result TEXT
            DO
                EVALUATE @text
                    WHEN 'positive' THEN
                        @result := 'good'
                    WHEN 'negative' THEN
                        @result := 'bad'
                    OTHERWISE
                        @result := 'neutral'
                END
                COMMIT @result
            END
        """)
        plan = plans[0]
        # Semantic evaluation should count as LLM call
        assert plan.total_estimated_llm_calls >= 1
        # Should have evaluate step with branches
        eval_steps = [s for s in plan.steps if s.step_type == "evaluate"]
        assert len(eval_steps) == 1
        assert len(eval_steps[0].branches) == 2  # two WHEN clauses

    def test_workflow_with_while(self):
        plans = _optimize("""
            WORKFLOW refine
                INPUT @draft TEXT
                OUTPUT @result TEXT
            DO
                @iterations := '0'
                WHILE @iterations < 3 DO
                    GENERATE improve(@draft) INTO @draft
                END
                COMMIT @draft
            END
        """)
        plan = plans[0]
        while_steps = [s for s in plan.steps if s.step_type == "while"]
        assert len(while_steps) == 1
        assert while_steps[0].estimated_llm_calls > 0

    def test_workflow_with_exception_handlers(self):
        plans = _optimize("""
            WORKFLOW safe_wf
                INPUT @prompt TEXT
                OUTPUT @result TEXT
            DO
                GENERATE summarize(@prompt) INTO @result
                COMMIT @result
            EXCEPTION
                WHEN HallucinationDetected THEN
                    @result := 'fallback'
                    COMMIT @result
            END
        """)
        plan = plans[0]
        assert len(plan.exception_handlers) == 1
        assert plan.exception_handlers[0].step_type == "exception_handler"

    def test_workflow_totals(self):
        plans = _optimize("""
            WORKFLOW multi_gen
                INPUT @input TEXT
                OUTPUT @output TEXT
            DO
                GENERATE summarize(@input) INTO @draft
                GENERATE refine(@draft) INTO @output
                COMMIT @output
            END
        """)
        plan = plans[0]
        assert plan.total_estimated_llm_calls >= 2
        assert plan.total_estimated_tokens > 0


class TestProcedurePlan:
    def test_basic_procedure(self):
        plans = _optimize("""
            PROCEDURE refine_text(input_text TEXT) RETURNS TEXT
            DO
                GENERATE improve(input_text) INTO @result
                COMMIT @result
            END
        """)
        assert len(plans) == 1
        plan = plans[0]
        assert isinstance(plan, WorkflowPlan)
        assert plan.workflow_name == "refine_text"
        assert "input_text" in plan.inputs
