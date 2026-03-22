"""Tests for SPL 2.0 Parser.

Includes SPL 1.0 backward compatibility tests plus comprehensive SPL 2.0 tests.
"""

import pytest
from spl.lexer import Lexer
from spl.parser import Parser, ParseError
from spl.ast_nodes import (
    Program, PromptStatement, CreateFunctionStatement,
    ExplainStatement, ExecuteStatement,
    SystemRoleCall, ContextRef, RagQuery, MemoryGet,
    SelectItem, GenerateClause, StoreClause,
    # SPL 2.0 nodes
    WorkflowStatement, ProcedureStatement, DoBlock, ExceptionHandler,
    EvaluateStatement, WhenClause, SemanticCondition, ComparisonCondition,
    WhileStatement, CommitStatement, RetryStatement, RaiseStatement,
    AssignmentStatement, GenerateIntoStatement, CallStatement,
)


def parse(source: str) -> Program:
    """Helper: lex + parse."""
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


# ================================================================
# SPL 1.0 Backward Compatibility Tests
# ================================================================

class TestSPL1Compat:
    """All SPL 1.0 programs must parse identically in SPL 2.0."""

    def test_minimal_prompt(self):
        ast = parse("""
            PROMPT hello
            SELECT system_role("helpful")
            GENERATE response()
        """)
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, PromptStatement)
        assert stmt.name == "hello"

    def test_prompt_with_budget(self):
        ast = parse("""
            PROMPT test
            WITH BUDGET 5000 tokens
            SELECT system_role("test")
            GENERATE response()
        """)
        assert ast.statements[0].budget == 5000

    def test_prompt_with_model(self):
        ast = parse("""
            PROMPT test
            USING MODEL claude-sonnet-4-5
            SELECT system_role("test")
            GENERATE response()
        """)
        assert "claude" in ast.statements[0].model

    def test_select_system_role(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("You are an expert")
            GENERATE response()
        """)
        items = ast.statements[0].select_items
        assert isinstance(items[0].expression, SystemRoleCall)
        assert items[0].expression.description == "You are an expert"

    def test_select_context_ref(self):
        ast = parse("""
            PROMPT test
            SELECT context.user_data AS user LIMIT 500 tokens
            GENERATE response(user)
        """)
        items = ast.statements[0].select_items
        assert isinstance(items[0].expression, ContextRef)
        assert items[0].alias == "user"
        assert items[0].limit_tokens == 500

    def test_select_rag_query(self):
        ast = parse("""
            PROMPT test
            SELECT rag.query("search text", top_k=3) AS docs
            GENERATE response(docs)
        """)
        expr = ast.statements[0].select_items[0].expression
        assert isinstance(expr, RagQuery)
        assert expr.top_k == 3

    def test_select_memory_get(self):
        ast = parse("""
            PROMPT test
            SELECT memory.get("history") AS history
            GENERATE response(history)
        """)
        expr = ast.statements[0].select_items[0].expression
        assert isinstance(expr, MemoryGet)

    def test_multiple_select_items(self):
        ast = parse("""
            PROMPT test
            SELECT
                system_role("expert"),
                context.user AS user LIMIT 500 tokens,
                rag.query("docs", top_k=5) AS docs LIMIT 2000 tokens
            GENERATE response(user, docs)
        """)
        assert len(ast.statements[0].select_items) == 3

    def test_generate_with_options(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("test")
            GENERATE response()
            WITH OUTPUT BUDGET 2000 tokens, TEMPERATURE 0.3, FORMAT markdown
        """)
        gen = ast.statements[0].generate_clause
        assert gen.output_budget == 2000
        assert gen.temperature == 0.3
        assert gen.output_format == "markdown"

    def test_where_clause(self):
        ast = parse("""
            PROMPT test
            SELECT context.user AS user
            WHERE user.active = 1 AND user.role = "admin"
            GENERATE response(user)
        """)
        where = ast.statements[0].where_clause
        assert len(where.conditions) == 2

    def test_cte(self):
        ast = parse("""
            PROMPT test
            WITH compressed AS (
                SELECT context.data AS data LIMIT 500 tokens
            )
            SELECT compressed
            GENERATE response(compressed)
        """)
        assert len(ast.statements[0].ctes) == 1

    def test_store_clause(self):
        ast = parse("""
            PROMPT test
            SELECT system_role("test")
            GENERATE response()
            STORE RESULT IN memory.output
        """)
        assert ast.statements[0].store_clause.key == "output"

    def test_explain(self):
        ast = parse("EXPLAIN PROMPT hello")
        assert isinstance(ast.statements[0], ExplainStatement)

    def test_create_function(self):
        ast = parse("""
            CREATE FUNCTION compress(text, max_tokens)
            RETURNS text
            AS $$ SELECT text LIMIT max_tokens tokens $$
        """)
        stmt = ast.statements[0]
        assert isinstance(stmt, CreateFunctionStatement)
        assert stmt.name == "compress"

    def test_multiple_statements(self):
        ast = parse("""
            PROMPT first
            SELECT system_role("test")
            GENERATE response();

            PROMPT second
            SELECT system_role("test2")
            GENERATE response2()
        """)
        assert len(ast.statements) == 2

    def test_hello_world_example(self):
        source = """
        PROMPT hello_world
        WITH BUDGET 2000 tokens
        USING MODEL claude-sonnet-4-5
        SELECT
            system_role("You are a friendly assistant"),
            context.user_input AS input LIMIT 500 tokens
        GENERATE
            greeting(input)
        WITH OUTPUT BUDGET 1000 tokens
        """
        ast = parse(source)
        stmt = ast.statements[0]
        assert stmt.name == "hello_world"
        assert stmt.budget == 2000
        assert len(stmt.select_items) == 2
        assert stmt.generate_clause.output_budget == 1000


# ================================================================
# SPL 2.0 New Statement Tests
# ================================================================

class TestWorkflow:
    """Test WORKFLOW statement parsing."""

    def test_minimal_workflow(self):
        ast = parse("""
            WORKFLOW simple
            DO
              COMMIT @result
            END
        """)
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, WorkflowStatement)
        assert stmt.name == "simple"

    def test_workflow_with_input_output(self):
        ast = parse("""
            WORKFLOW analyze
            INPUT: @task text
            OUTPUT: @result text
            DO
              COMMIT @result
            END
        """)
        stmt = ast.statements[0]
        assert len(stmt.inputs) == 1
        assert stmt.inputs[0].name == "task"
        assert stmt.inputs[0].param_type == "text"
        assert len(stmt.outputs) == 1
        assert stmt.outputs[0].name == "result"

    def test_workflow_multiple_params(self):
        ast = parse("""
            WORKFLOW multi
            INPUT: @task text, @context text
            OUTPUT: @result text, @score text
            DO
              COMMIT @result
            END
        """)
        stmt = ast.statements[0]
        assert len(stmt.inputs) == 2
        assert len(stmt.outputs) == 2

    def test_workflow_with_exception(self):
        ast = parse("""
            WORKFLOW safe
            INPUT: @task text
            DO
              COMMIT @task
            EXCEPTION
              WHEN HallucinationDetected THEN
                COMMIT @task WITH status = 'fallback'
            END
        """)
        stmt = ast.statements[0]
        assert len(stmt.exception_handlers) == 1
        assert stmt.exception_handlers[0].exception_type == "HallucinationDetected"

    def test_workflow_with_security(self):
        ast = parse("""
            WORKFLOW secure
            INPUT: @data text
            SECURITY: CLASSIFICATION: confidential
            DO
              COMMIT @data
            END
        """)
        stmt = ast.statements[0]
        assert stmt.security == {'classification': 'confidential'}

    def test_workflow_with_labels(self):
        ast = parse("""
            WORKFLOW labeled
            LABELS: { 'team': 'data-science', 'priority': 'high' }
            DO
              COMMIT @labeled
            END
        """)
        stmt = ast.statements[0]
        assert stmt.labels == {'team': 'data-science', 'priority': 'high'}


class TestProcedure:
    """Test PROCEDURE statement parsing."""

    def test_minimal_procedure(self):
        ast = parse("""
            PROCEDURE greet(name)
            RETURNS text
            DO
              COMMIT @name
            END
        """)
        stmt = ast.statements[0]
        assert isinstance(stmt, ProcedureStatement)
        assert stmt.name == "greet"
        assert len(stmt.parameters) == 1
        assert stmt.return_type == "text"

    def test_procedure_no_return(self):
        ast = parse("""
            PROCEDURE log_event(event)
            DO
              COMMIT @event
            END
        """)
        stmt = ast.statements[0]
        assert stmt.return_type is None

    def test_procedure_with_exception(self):
        ast = parse("""
            PROCEDURE safe_gen(prompt)
            RETURNS text
            DO
              GENERATE response(@prompt) INTO @result
              COMMIT @result
            EXCEPTION
              WHEN RefusalToAnswer THEN
                COMMIT @prompt WITH status = 'refused'
              WHEN OTHERS THEN
                RAISE BudgetExceeded 'out of budget'
            END
        """)
        stmt = ast.statements[0]
        assert len(stmt.exception_handlers) == 2
        assert stmt.exception_handlers[0].exception_type == "RefusalToAnswer"
        assert stmt.exception_handlers[1].exception_type == "OTHERS"


class TestDoBlock:
    """Test DO ... END block parsing."""

    def test_simple_do_block(self):
        ast = parse("""
            WORKFLOW w
            DO
              @x := 1
              @y := 2
            END
        """)
        stmt = ast.statements[0]
        assert len(stmt.body) == 2

    def test_do_block_with_exception(self):
        ast = parse("""
            WORKFLOW w
            DO
              @x := 1
            EXCEPTION
              WHEN OTHERS THEN
                COMMIT @x
            END
        """)
        stmt = ast.statements[0]
        assert len(stmt.body) == 1
        assert len(stmt.exception_handlers) == 1


class TestEvaluate:
    """Test EVALUATE statement parsing."""

    def test_evaluate_semantic(self):
        ast = parse("""
            WORKFLOW w
            DO
              EVALUATE @summary
                WHEN 'coherent' THEN
                  COMMIT @summary
                WHEN 'incomplete' THEN
                  RETRY WITH temperature = 0.1
              END
            END
        """)
        stmt = ast.statements[0]
        eval_stmt = stmt.body[0]
        assert isinstance(eval_stmt, EvaluateStatement)
        assert len(eval_stmt.when_clauses) == 2
        assert isinstance(eval_stmt.when_clauses[0].condition, SemanticCondition)
        assert eval_stmt.when_clauses[0].condition.semantic_value == "coherent"

    def test_evaluate_deterministic(self):
        ast = parse("""
            WORKFLOW w
            DO
              EVALUATE @score
                WHEN > 0.8 THEN
                  COMMIT @result
                WHEN <= 0.8 THEN
                  RETRY
              END
            END
        """)
        eval_stmt = ast.statements[0].body[0]
        assert isinstance(eval_stmt.when_clauses[0].condition, ComparisonCondition)
        assert eval_stmt.when_clauses[0].condition.operator == ">"

    def test_evaluate_with_otherwise(self):
        ast = parse("""
            WORKFLOW w
            DO
              EVALUATE @action
                WHEN 'search' THEN
                  COMMIT @action
                WHEN 'calculate' THEN
                  COMMIT @action
                OTHERWISE
                  COMMIT @action WITH status = 'unknown'
              END
            END
        """)
        eval_stmt = ast.statements[0].body[0]
        assert len(eval_stmt.when_clauses) == 2
        assert len(eval_stmt.otherwise_statements) == 1


class TestWhile:
    """Test WHILE statement parsing."""

    def test_simple_while(self):
        ast = parse("""
            WORKFLOW w
            DO
              @i := 0
              WHILE @i < 5 DO
                @i := @i + 1
              END
            END
        """)
        while_stmt = ast.statements[0].body[1]
        assert isinstance(while_stmt, WhileStatement)
        assert len(while_stmt.body) == 1

    def test_while_with_body(self):
        ast = parse("""
            WORKFLOW w
            DO
              @iteration := 0
              WHILE @iteration < 3 DO
                GENERATE critique(@current) INTO @feedback
                GENERATE refined(@current, @feedback) INTO @current
                @iteration := @iteration + 1
              END
            END
        """)
        while_stmt = ast.statements[0].body[1]
        assert len(while_stmt.body) == 3


class TestAssignment:
    """Test assignment statement parsing."""

    def test_simple_assignment(self):
        ast = parse("""
            WORKFLOW w
            DO
              @x := 42
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, AssignmentStatement)
        assert stmt.variable == "x"

    def test_string_assignment(self):
        ast = parse("""
            WORKFLOW w
            DO
              @name := 'hello'
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, AssignmentStatement)

    def test_expression_assignment(self):
        ast = parse("""
            WORKFLOW w
            DO
              @total := @a + @b
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, AssignmentStatement)


class TestCommit:
    """Test COMMIT statement parsing."""

    def test_simple_commit(self):
        ast = parse("""
            WORKFLOW w
            DO
              COMMIT @result
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, CommitStatement)

    def test_commit_with_options(self):
        ast = parse("""
            WORKFLOW w
            DO
              COMMIT @result WITH status = 'complete', iterations = @i
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, CommitStatement)
        assert 'status' in stmt.options
        assert 'iterations' in stmt.options


class TestRetry:
    """Test RETRY statement parsing."""

    def test_simple_retry(self):
        ast = parse("""
            WORKFLOW w
            DO
              RETRY
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, RetryStatement)
        assert stmt.options == {}

    def test_retry_with_options(self):
        ast = parse("""
            WORKFLOW w
            DO
              RETRY WITH temperature = 0.1
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, RetryStatement)
        assert 'temperature' in stmt.options


class TestRaise:
    """Test RAISE statement parsing."""

    def test_simple_raise(self):
        ast = parse("""
            WORKFLOW w
            DO
              RAISE BudgetExceeded
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, RaiseStatement)
        assert stmt.exception_type == "BudgetExceeded"

    def test_raise_with_message(self):
        ast = parse("""
            WORKFLOW w
            DO
              RAISE HallucinationDetected 'detected in output'
            END
        """)
        stmt = ast.statements[0].body[0]
        assert stmt.message == "detected in output"


class TestGenerateInto:
    """Test GENERATE ... INTO @var statement parsing."""

    def test_generate_into(self):
        ast = parse("""
            WORKFLOW w
            DO
              GENERATE draft(@task) INTO @result
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, GenerateIntoStatement)
        assert stmt.generate_clause.function_name == "draft"
        assert stmt.target_variable == "result"

    def test_generate_into_with_options(self):
        ast = parse("""
            WORKFLOW w
            DO
              GENERATE response(@prompt) WITH OUTPUT BUDGET 500 tokens INTO @result
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, GenerateIntoStatement)
        assert stmt.generate_clause.output_budget == 500
        assert stmt.target_variable == "result"


class TestCall:
    """Test CALL statement parsing."""

    def test_simple_call(self):
        ast = parse("""
            WORKFLOW w
            DO
              CALL my_proc(@arg1, @arg2) INTO @result
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, CallStatement)
        assert stmt.procedure_name == "my_proc"
        assert len(stmt.arguments) == 2
        assert stmt.target_variable == "result"

    def test_call_no_into(self):
        ast = parse("""
            WORKFLOW w
            DO
              CALL log_event(@msg)
            END
        """)
        stmt = ast.statements[0].body[0]
        assert isinstance(stmt, CallStatement)
        assert stmt.target_variable is None


# ================================================================
# Integration Tests: Full SPL 2.0 Patterns
# ================================================================

class TestIntegrationPatterns:
    """Test parsing of complete SPL 2.0 workflow patterns."""

    def test_self_refine_pattern(self):
        """Test the iterative self-refinement pattern."""
        source = """
        WORKFLOW self_refine
          INPUT: @task text
          OUTPUT: @result text
        DO
          @iteration := 0

          GENERATE draft(@task) INTO @current

          WHILE @iteration < 5 DO
            GENERATE critique(@current) INTO @feedback
            GENERATE refined(@current, @feedback) INTO @current
            @iteration := @iteration + 1
          END

          COMMIT @current WITH iterations = @iteration
        EXCEPTION
          WHEN MaxIterationsReached THEN
            COMMIT @current WITH status = 'partial'
        END
        """
        ast = parse(source)
        stmt = ast.statements[0]
        assert isinstance(stmt, WorkflowStatement)
        assert stmt.name == "self_refine"
        assert len(stmt.inputs) == 1
        assert len(stmt.outputs) == 1
        # Body: assignment, generate_into, while
        assert len(stmt.body) == 4  # @iteration, GENERATE, WHILE, COMMIT
        assert isinstance(stmt.body[0], AssignmentStatement)
        assert isinstance(stmt.body[1], GenerateIntoStatement)
        assert isinstance(stmt.body[2], WhileStatement)
        assert isinstance(stmt.body[3], CommitStatement)
        # Exception handlers
        assert len(stmt.exception_handlers) == 1

    def test_evaluate_with_actions(self):
        """Test EVALUATE with different action branches."""
        source = """
        WORKFLOW router
          INPUT: @task text
        DO
          GENERATE classify(@task) INTO @category

          EVALUATE @category
            WHEN 'search' THEN
              GENERATE search_response(@task) INTO @answer
              COMMIT @answer
            WHEN 'calculate' THEN
              CALL calculator(@task) INTO @answer
              COMMIT @answer
            OTHERWISE
              GENERATE general_response(@task) INTO @answer
              COMMIT @answer
          END
        END
        """
        ast = parse(source)
        stmt = ast.statements[0]
        eval_stmt = stmt.body[1]
        assert isinstance(eval_stmt, EvaluateStatement)
        assert len(eval_stmt.when_clauses) == 2
        assert len(eval_stmt.otherwise_statements) == 2

    def test_exception_handling_pattern(self):
        """Test comprehensive exception handling."""
        source = """
        WORKFLOW safe_generation
          INPUT: @prompt text
          OUTPUT: @result text
        DO
          GENERATE response(@prompt) INTO @result
          COMMIT @result
        EXCEPTION
          WHEN HallucinationDetected THEN
            GENERATE response(@prompt) INTO @result
            COMMIT @result WITH status = 'conservative'
          WHEN RefusalToAnswer THEN
            COMMIT @prompt WITH status = 'refused'
          WHEN OTHERS THEN
            RAISE BudgetExceeded 'unhandled error'
        END
        """
        ast = parse(source)
        stmt = ast.statements[0]
        assert len(stmt.exception_handlers) == 3

    def test_mixed_spl1_and_spl(self):
        """Test mixing SPL 1.0 and SPL 2.0 statements in same program."""
        source = """
        CREATE FUNCTION summarize(text)
        RETURNS text
        AS $$ Summarize the following: {text} $$;

        PROMPT hello
        SELECT system_role("You are helpful")
        GENERATE response()
        WITH OUTPUT BUDGET 1000 tokens;

        WORKFLOW refine
          INPUT: @task text
        DO
          GENERATE draft(@task) INTO @result
          COMMIT @result
        END
        """
        ast = parse(source)
        assert len(ast.statements) == 3
        assert isinstance(ast.statements[0], CreateFunctionStatement)
        assert isinstance(ast.statements[1], PromptStatement)
        assert isinstance(ast.statements[2], WorkflowStatement)

    def test_nested_control_flow(self):
        """Test nested WHILE and EVALUATE."""
        source = """
        WORKFLOW nested
        DO
          @i := 0
          WHILE @i < 3 DO
            GENERATE step(@i) INTO @output
            EVALUATE @output
              WHEN 'done' THEN
                COMMIT @output
              WHEN 'continue' THEN
                @i := @i + 1
            END
          END
        END
        """
        ast = parse(source)
        stmt = ast.statements[0]
        while_stmt = stmt.body[1]
        assert isinstance(while_stmt, WhileStatement)
        # While body: GENERATE INTO, EVALUATE
        assert isinstance(while_stmt.body[0], GenerateIntoStatement)
        assert isinstance(while_stmt.body[1], EvaluateStatement)
