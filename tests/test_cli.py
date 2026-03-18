"""Tests for SPL 2.0 CLI."""

import os
import pytest
from spl2.cli import main, _parse_params


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


class TestParseParams:
    def test_basic_param(self):
        assert _parse_params(["key=value"]) == {"key": "value"}

    def test_multiple_params(self):
        result = _parse_params(["a=1", "b=2"])
        assert result == {"a": "1", "b": "2"}

    def test_value_with_equals(self):
        result = _parse_params(["q=what is 2+2=4?"])
        assert result == {"q": "what is 2+2=4?"}

    def test_invalid_param(self):
        with pytest.raises(ValueError, match="Invalid param format"):
            _parse_params(["no_equals_sign"])


class TestCLIExplain:
    def test_explain_hello_world(self, capsys):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        main(["explain", path])
        out = capsys.readouterr().out
        assert "Execution Plan" in out or "Workflow Plan" in out

    def test_explain_self_refine(self, capsys):
        path = os.path.join(EXAMPLES_DIR, "self_refine.spl")
        main(["explain", path])
        out = capsys.readouterr().out
        assert "Plan" in out


class TestCLIParse:
    def test_parse_hello_world(self, capsys):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        main(["parse", path])
        out = capsys.readouterr().out
        assert "Parsed OK" in out

    def test_parse_json_output(self, capsys):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        main(["parse", path, "--json"])
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert data["type"] == "Program"


class TestCLIRun:
    def test_run_hello_world(self, capsys):
        path = os.path.join(EXAMPLES_DIR, "hello_world.spl")
        main(["run", path])
        out = capsys.readouterr().out
        assert "=" * 10 in out  # separator line


class TestCLIEdgeCases:
    def test_no_command(self):
        with pytest.raises(SystemExit):
            main([])

    def test_file_not_found(self):
        with pytest.raises(SystemExit):
            main(["parse", "/nonexistent/file.spl"])
