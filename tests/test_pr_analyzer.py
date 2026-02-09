"""Tests for .github/scripts/pr_analyzer.py."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch
import importlib.util


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "pr_analyzer", Path(__file__).parent.parent / ".github" / "scripts" / "pr_analyzer.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_main_with_no_files():
    mod = _load_module()
    with patch("sys.stdin", StringIO("")), patch("sys.stdout", new_callable=StringIO) as out:
        assert mod.main() == 0
        text = out.getvalue()
        assert "Changed files:" in text
        assert "- (none)" in text


def test_main_with_multiple_files_and_whitespace():
    mod = _load_module()
    payload = "src/main.py\n\n  \n\tsrc/utils.py\n"
    with patch("sys.stdin", StringIO(payload)), patch("sys.stdout", new_callable=StringIO) as out:
        assert mod.main() == 0
        text = out.getvalue()
        assert "- src/main.py" in text
        assert "- \tsrc/utils.py" in text or "- src/utils.py" in text


def test_main_has_stdin_docstring_reference():
    mod = _load_module()
    assert mod.main.__doc__ is not None
    assert "stdin" in mod.main.__doc__.lower()
