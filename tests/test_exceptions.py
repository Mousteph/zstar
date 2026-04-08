import pytest

from zstar.core.exceptions import (
    ZStarError,
    BacktestExecutionError,
    zstar_error,
    func_errors,
)


def test_zstar_error_context_wraps_non_domain_exceptions():
    with pytest.raises(BacktestExecutionError, match="wrapped"):
        with zstar_error(BacktestExecutionError, "wrapped"):
            raise ValueError("boom")


def test_zstar_error_context_does_not_double_wrap_same_error():
    with pytest.raises(BacktestExecutionError, match="original"):
        with zstar_error(BacktestExecutionError, "wrapped"):
            raise BacktestExecutionError("original")


def test_func_errors_decorator_wraps_unexpected_exceptions():
    @func_errors(BacktestExecutionError, "decorated")
    def _explode():
        raise RuntimeError("boom")

    with pytest.raises(BacktestExecutionError, match="decorated"):
        _explode()


def test_func_errors_decorator_does_not_wrap_same_error_type():
    @func_errors(BacktestExecutionError, "decorated")
    def _explode():
        raise BacktestExecutionError("already wrapped")

    with pytest.raises(BacktestExecutionError, match="already wrapped"):
        _explode()


def test_error_hierarchy_uses_zstar_base_class():
    assert issubclass(BacktestExecutionError, ZStarError)
