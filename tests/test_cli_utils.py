from pathlib import Path

import pytest

from zstar.cli.utils import read_strategy_code, resolve_output_path


def test_read_strategy_code_reads_utf8_file(tmp_path):
    strategy_path = tmp_path / "strategy.py"
    strategy_path.write_text("print('hello')", encoding="utf-8")

    assert read_strategy_code(strategy_path) == "print('hello')"


def test_read_strategy_code_raises_runtime_error_for_missing_file(tmp_path):
    missing_path = tmp_path / "missing.py"

    with pytest.raises(RuntimeError, match="Failed to read strategy file"):
        read_strategy_code(missing_path)


def test_resolve_output_path_creates_parent_directories(tmp_path):
    relative_output = tmp_path / "nested" / "reports" / "kpis.json"

    resolved = resolve_output_path(str(relative_output))

    assert isinstance(resolved, Path)
    assert resolved.parent.exists() is True
    assert resolved == relative_output.resolve()
