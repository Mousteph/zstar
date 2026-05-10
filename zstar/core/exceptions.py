from functools import wraps
from contextlib import contextmanager


class ZStarError(RuntimeError):
    """Base exception for all errors raised by ZStar."""


@contextmanager
def zstar_error(error_cls: type[ZStarError], message: str | None = None):
    try:
        yield
    except error_cls:
        raise
    except Exception as exc:
        raise error_cls(message or str(exc)) from exc


def func_errors(error_cls: type[ZStarError], message: str | None = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_cls:
                raise
            except Exception as exc:
                raise error_cls(message or str(exc)) from exc
        return wrapper
    return decorator


class BacktestServiceError(ZStarError):
    error_code = "BACKTEST_SERVICE_ERROR"
    status_code = 400


class StrategyExecutionError(BacktestServiceError):
    error_code = "STRATEGY_EXECUTION_ERROR"
    status_code = 400


class StrategyValidationError(BacktestServiceError):
    error_code = "STRATEGY_VALIDATION_ERROR"
    status_code = 400


class IntervalNotSupportedError(BacktestServiceError):
    error_code = "INTERVAL_NOT_SUPPORTED_ERROR"
    status_code = 400

class MarketDataDownloadError(BacktestServiceError):
    error_code = "MARKET_DATA_DOWNLOAD_ERROR"
    status_code = 400


class CsvDataError(BacktestServiceError):
    error_code = "CSV_DATA_ERROR"
    status_code = 400


class BacktestExecutionError(BacktestServiceError):
    error_code = "BACKTEST_EXECUTION_ERROR"
    status_code = 400
