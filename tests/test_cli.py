"""Tests for SPL 2.0 CLI (click-based)."""

import os
import tempfile
import pytest
from click.testing import CliRunner
from spl2.cli import cli, _parse_params


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


@pytest.fixture
def runner():
    return CliRunner()


class TestParseParams:
    def test_basic_param(self):
        assert _parse_params(("key=value",)) == {"key": "value"}

    def test_multiple_params(self):
        result = _parse_params(("a=1", "b=2"))
        assert result == {"a": "1", "b": "2"}

    def test_value_with_equals(self):
        result = _parse_params(("q=what is 2+2=4?",))
        assert result == {"q": "what is 2+2=4?"}

    def test_invalid_param(self):
        from click import BadParameter
        with pytest.raises(BadParameter):
            _parse_params(("no_equals_sign",))


class TestCLIHelp:
    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Agentic Workflow Orchestration" in result.output

    def test_no_command_shows_help(self, runner):
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_run_help(self, runner):
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "--adapter" in result.output
        assert "--param" in result.output

    def test_memory_help(self, runner):
        result = runner.invoke(cli, ["memory", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "get" in result.output

    def test_rag_help(self, runner):
        result = runner.invoke(cli, ["rag", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "query" in result.output


class TestCLIExplain:
    def test_explain_hello_world(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["explain", path])
        assert result.exit_code == 0
        assert "Plan" in result.output

    def test_explain_self_refine(self, runner):
        path = os.path.join(EXAMPLES_DIR, "self_refine.spl")
        result = runner.invoke(cli, ["explain", path])
        assert result.exit_code == 0
        assert "Plan" in result.output


class TestCLIParse:
    def test_parse_hello_world(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["parse", path])
        assert result.exit_code == 0
        assert "Parsed OK" in result.output

    def test_parse_json_output(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["parse", path, "--json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["type"] == "Program"

    def test_validate_alias(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["validate", path])
        assert result.exit_code == 0
        assert "Parsed OK" in result.output

    def test_syntax_alias(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["syntax", path])
        assert result.exit_code == 0
        assert "Parsed OK" in result.output


class TestCLIRun:
    def test_run_hello_world(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["run", path])
        assert result.exit_code == 0
        assert "=" * 10 in result.output

    def test_execute_alias(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["execute", path])
        assert result.exit_code == 0
        assert "=" * 10 in result.output

    def test_run_with_param(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["run", path, "-p", "user_input=hello"])
        assert result.exit_code == 0

    def test_run_unknown_adapter(self, runner):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        result = runner.invoke(cli, ["run", path, "--adapter", "nonexistent"])
        assert result.exit_code != 0
        assert "Unknown adapter" in result.output


class TestCLIAdapters:
    def test_adapters_command(self, runner):
        result = runner.invoke(cli, ["adapters"])
        assert result.exit_code == 0
        assert "echo" in result.output
        assert "ollama" in result.output
        assert "momagrid" in result.output
        assert "Available LLM adapters" in result.output


class TestCLIInit:
    def test_init_creates_workspace(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                result = runner.invoke(cli, ["init"])
                assert result.exit_code == 0
                assert "Initialised" in result.output
                assert os.path.exists(".spl/memory.db")

    def test_init_already_exists(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            with runner.isolated_filesystem(temp_dir=tmpdir):
                os.makedirs(".spl")
                result = runner.invoke(cli, ["init"])
                assert result.exit_code == 0
                assert "already exists" in result.output


class TestCLIMemory:
    def test_memory_set_get_list_delete(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            sd = tmpdir
            result = runner.invoke(cli, ["memory", "set", "greeting", "hello world",
                                         "--storage-dir", sd])
            assert result.exit_code == 0
            assert "Set" in result.output

            result = runner.invoke(cli, ["memory", "get", "greeting",
                                         "--storage-dir", sd])
            assert result.exit_code == 0
            assert "hello world" in result.output

            result = runner.invoke(cli, ["memory", "list", "--storage-dir", sd])
            assert result.exit_code == 0
            assert "greeting" in result.output

            result = runner.invoke(cli, ["memory", "delete", "greeting",
                                         "--storage-dir", sd])
            assert result.exit_code == 0
            assert "Deleted" in result.output

    def test_memory_get_missing_key(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, ["memory", "get", "nonexistent",
                                         "--storage-dir", tmpdir])
            assert result.exit_code != 0
            assert "Key not found" in result.output

    def test_memory_no_subcommand(self, runner):
        result = runner.invoke(cli, ["memory"])
        assert result.exit_code == 0  # click shows help
        assert "list" in result.output


class TestCLIRag:
    def test_rag_add_count_query(self, runner):
        try:
            from spl2.storage.vector import VectorStore
        except ImportError:
            pytest.skip("numpy or faiss-cpu not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            sd = tmpdir
            result = runner.invoke(cli, ["rag", "add",
                                         "Python is a programming language",
                                         "--storage-dir", sd])
            assert result.exit_code == 0
            assert "Added document" in result.output

            result = runner.invoke(cli, ["rag", "count", "--storage-dir", sd])
            assert result.exit_code == 0
            assert "1" in result.output

            result = runner.invoke(cli, ["rag", "query", "programming",
                                         "--storage-dir", sd])
            assert result.exit_code == 0
            assert "Python" in result.output or "score" in result.output

    def test_rag_no_subcommand(self, runner):
        result = runner.invoke(cli, ["rag"])
        assert result.exit_code == 0
        assert "add" in result.output


class TestCLIVersion:
    def test_version_command(self, runner):
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "spl2 2.0.0" in result.output

    def test_version_flag(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "2.0.0" in result.output


class TestCLIEdgeCases:
    def test_file_not_found(self, runner):
        result = runner.invoke(cli, ["parse", "/nonexistent/file.spl"])
        assert result.exit_code != 0
        assert "File not found" in result.output

    def test_invalid_command(self, runner):
        result = runner.invoke(cli, ["bogus"])
        assert result.exit_code != 0
