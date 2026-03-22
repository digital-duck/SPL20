"""Tests for SPL 2.0 Lexer.

Includes all SPL 1.0 backward compatibility tests plus new SPL 2.0 token tests.
"""

import pytest
from spl.lexer import Lexer, LexerError
from spl.tokens import TokenType


class TestLexerSPL1Compat:
    """SPL 1.0 backward compatibility tests."""

    def test_simple_prompt(self):
        tokens = Lexer('PROMPT hello').tokenize()
        assert tokens[0].type == TokenType.PROMPT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "hello"
        assert tokens[2].type == TokenType.EOF

    def test_keywords_case_insensitive(self):
        tokens = Lexer('prompt HELLO select WHERE').tokenize()
        assert tokens[0].type == TokenType.PROMPT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[2].type == TokenType.SELECT
        assert tokens[3].type == TokenType.WHERE

    def test_string_literals(self):
        tokens = Lexer('"hello world" \'single quotes\'').tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == "single quotes"

    def test_integer_literal(self):
        tokens = Lexer("42 1000").tokenize()
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == "42"

    def test_float_literal(self):
        tokens = Lexer("3.14 0.7").tokenize()
        assert tokens[0].type == TokenType.FLOAT
        assert tokens[0].value == "3.14"

    def test_operators(self):
        tokens = Lexer(". , ( ) = != > < >= <=").tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [
            TokenType.DOT, TokenType.COMMA,
            TokenType.LPAREN, TokenType.RPAREN,
            TokenType.EQ, TokenType.NEQ,
            TokenType.GT, TokenType.LT,
            TokenType.GTE, TokenType.LTE,
        ]

    def test_comments_skipped(self):
        source = """
        -- This is a comment
        PROMPT hello
        -- Another comment
        SELECT
        """
        tokens = Lexer(source).tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert types == [TokenType.PROMPT, TokenType.IDENTIFIER, TokenType.SELECT]

    def test_dollar_dollar(self):
        tokens = Lexer('$$ body $$').tokenize()
        assert tokens[0].type == TokenType.DOLLAR_DOLLAR
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == ' body '

    def test_dot_notation(self):
        tokens = Lexer("context.user").tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[1].type == TokenType.DOT
        assert tokens[2].type == TokenType.IDENTIFIER

    def test_with_budget(self):
        tokens = Lexer("WITH BUDGET 8000 TOKENS").tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.WITH, TokenType.BUDGET, TokenType.INTEGER, TokenType.TOKENS]

    def test_line_tracking(self):
        tokens = Lexer("PROMPT\nhello").tokenize()
        assert tokens[0].line == 1
        assert tokens[1].line == 2

    def test_at_symbol(self):
        tokens = Lexer("@user_data").tokenize()
        assert tokens[0].type == TokenType.AT
        assert tokens[1].type == TokenType.IDENTIFIER

    def test_unterminated_string(self):
        with pytest.raises(LexerError, match="Unterminated"):
            Lexer('"hello').tokenize()

    def test_full_prompt_query(self):
        source = """
        PROMPT hello_world
        WITH BUDGET 2000 tokens
        USING MODEL claude-sonnet-4-5
        SELECT
            system_role("You are helpful"),
            context.input AS user_input LIMIT 500 tokens
        GENERATE
            response(user_input)
        WITH OUTPUT BUDGET 1000 tokens;
        """
        tokens = Lexer(source).tokenize()
        assert tokens[-1].type == TokenType.EOF
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.PROMPT in types
        assert TokenType.SELECT in types
        assert TokenType.GENERATE in types


class TestLexerSPL2New:
    """SPL 2.0 new token tests."""

    def test_assign_operator(self):
        tokens = Lexer("@x := 42").tokenize()
        assert tokens[0].type == TokenType.AT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[2].type == TokenType.ASSIGN
        assert tokens[2].value == ":="
        assert tokens[3].type == TokenType.INTEGER

    def test_colon(self):
        tokens = Lexer("INPUT:").tokenize()
        assert tokens[0].type == TokenType.INPUT
        assert tokens[1].type == TokenType.COLON

    def test_braces(self):
        tokens = Lexer("{ }").tokenize()
        assert tokens[0].type == TokenType.LBRACE
        assert tokens[1].type == TokenType.RBRACE

    def test_percent(self):
        tokens = Lexer("80 %").tokenize()
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[1].type == TokenType.PERCENT

    def test_workflow_keyword(self):
        tokens = Lexer("WORKFLOW my_flow").tokenize()
        assert tokens[0].type == TokenType.WORKFLOW
        assert tokens[1].type == TokenType.IDENTIFIER

    def test_evaluate_keyword(self):
        tokens = Lexer("EVALUATE @result").tokenize()
        assert tokens[0].type == TokenType.EVALUATE
        assert tokens[1].type == TokenType.AT

    def test_while_do_end(self):
        tokens = Lexer("WHILE DO END").tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.WHILE, TokenType.DO, TokenType.END]

    def test_when_then_otherwise(self):
        tokens = Lexer("WHEN THEN OTHERWISE").tokenize()
        types = [t.type for t in tokens[:-1]]
        assert types == [TokenType.WHEN, TokenType.THEN, TokenType.OTHERWISE]

    def test_exception_keywords(self):
        tokens = Lexer("EXCEPTION WHEN HallucinationDetected THEN").tokenize()
        assert tokens[0].type == TokenType.EXCEPTION
        assert tokens[1].type == TokenType.WHEN
        assert tokens[2].type == TokenType.IDENTIFIER  # HallucinationDetected is identifier
        assert tokens[3].type == TokenType.THEN

    def test_retry_raise(self):
        tokens = Lexer("RETRY RAISE").tokenize()
        assert tokens[0].type == TokenType.RETRY
        assert tokens[1].type == TokenType.RAISE

    def test_into_keyword(self):
        tokens = Lexer("INTO @result").tokenize()
        assert tokens[0].type == TokenType.INTO
        assert tokens[1].type == TokenType.AT

    def test_procedure_keyword(self):
        tokens = Lexer("PROCEDURE react_loop()").tokenize()
        assert tokens[0].type == TokenType.PROCEDURE

    def test_commit_keyword(self):
        """COMMIT is already in SPL 1.0 tokens but now used for output finalization."""
        tokens = Lexer("COMMIT @result").tokenize()
        assert tokens[0].type == TokenType.COMMIT

    def test_call_keyword(self):
        tokens = Lexer("CALL my_proc()").tokenize()
        assert tokens[0].type == TokenType.CALL

    def test_security_classification(self):
        tokens = Lexer("SECURITY : CLASSIFICATION : internal").tokenize()
        assert tokens[0].type == TokenType.SECURITY
        assert tokens[1].type == TokenType.COLON
        assert tokens[2].type == TokenType.CLASSIFICATION

    def test_others_keyword(self):
        tokens = Lexer("WHEN OTHERS THEN").tokenize()
        assert tokens[0].type == TokenType.WHEN
        assert tokens[1].type == TokenType.OTHERS
        assert tokens[2].type == TokenType.THEN

    def test_full_spl_workflow(self):
        source = """
        WORKFLOW iterative_refinement
          INPUT: @task text
          OUTPUT: @result text
        DO
          @iteration := 0
          GENERATE draft(@task) INTO @current
          WHILE @iteration < 5 DO
            GENERATE critique(@current) INTO @feedback
            @iteration := @iteration + 1
          END
          COMMIT @current WITH status = 'complete'
        EXCEPTION
          WHEN MaxIterationsReached THEN
            COMMIT @current WITH status = 'partial'
        END
        """
        tokens = Lexer(source).tokenize()
        assert tokens[-1].type == TokenType.EOF
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.WORKFLOW in types
        assert TokenType.DO in types
        assert TokenType.ASSIGN in types
        assert TokenType.WHILE in types
        assert TokenType.COMMIT in types
        assert TokenType.EXCEPTION in types
        assert TokenType.END in types
