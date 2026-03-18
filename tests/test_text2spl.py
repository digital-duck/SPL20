"""Tests for SPL 2.0 text2spl — natural language to SPL compiler."""

import asyncio
import pytest
from spl2.text2spl import Text2SPL, SPL2_SYSTEM_PROMPT, _MODE_INSTRUCTIONS
from spl2.adapters.echo import EchoAdapter


class TestText2SPLValidation:
    """Test the validate_output static method (no LLM needed)."""

    def test_valid_prompt(self):
        valid, msg = Text2SPL.validate_output("""
            PROMPT hello
            SELECT system_role('assistant') AS role
            GENERATE summarize(role)
        """)
        assert valid is True
        assert "OK" in msg

    def test_valid_workflow(self):
        valid, msg = Text2SPL.validate_output("""
            WORKFLOW greet
                INPUT @name TEXT
                OUTPUT @greeting TEXT
            DO
                @greeting := 'Hello'
                COMMIT @greeting
            END
        """)
        assert valid is True

    def test_invalid_syntax(self):
        valid, msg = Text2SPL.validate_output("INVALID GARBAGE CODE")
        assert valid is False
        assert "error" in msg.lower()

    def test_empty_input(self):
        valid, msg = Text2SPL.validate_output("")
        # Empty should parse as valid (no statements)
        assert valid is True

    def test_strip_fences(self):
        assert Text2SPL._strip_fences("```spl\nPROMPT hello\n```") == "PROMPT hello"
        assert Text2SPL._strip_fences("PROMPT hello") == "PROMPT hello"
        assert Text2SPL._strip_fences("```\ncode\n```") == "code"


class TestText2SPLCompile:
    """Test the compile method using echo adapter."""

    def test_compile_returns_string(self):
        adapter = EchoAdapter()
        compiler = Text2SPL(adapter)
        result = asyncio.run(compiler.compile("summarize a document"))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_compile_auto_mode(self):
        adapter = EchoAdapter()
        compiler = Text2SPL(adapter)
        result = asyncio.run(compiler.compile("do something", mode="auto"))
        assert isinstance(result, str)

    def test_compile_prompt_mode(self):
        adapter = EchoAdapter()
        compiler = Text2SPL(adapter)
        result = asyncio.run(compiler.compile("summarize text", mode="prompt"))
        assert isinstance(result, str)

    def test_compile_workflow_mode(self):
        adapter = EchoAdapter()
        compiler = Text2SPL(adapter)
        result = asyncio.run(compiler.compile("build agent", mode="workflow"))
        assert isinstance(result, str)

    def test_compile_invalid_mode(self):
        adapter = EchoAdapter()
        compiler = Text2SPL(adapter)
        with pytest.raises(ValueError, match="Invalid mode"):
            asyncio.run(compiler.compile("test", mode="invalid"))


class TestText2SPLConfig:
    def test_system_prompt_has_examples(self):
        assert "Example 1" in SPL2_SYSTEM_PROMPT
        assert "WORKFLOW" in SPL2_SYSTEM_PROMPT
        assert "PROMPT" in SPL2_SYSTEM_PROMPT
        assert "EVALUATE" in SPL2_SYSTEM_PROMPT

    def test_mode_instructions(self):
        assert "prompt" in _MODE_INSTRUCTIONS
        assert "workflow" in _MODE_INSTRUCTIONS
        assert "auto" in _MODE_INSTRUCTIONS
