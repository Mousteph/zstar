from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from zstar.config import LoggingConfig


_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")
_USER_ACTION: ContextVar[str] = ContextVar("user_action", default="-")


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = _REQUEST_ID.get()
        if not hasattr(record, "user_action"):
            record.user_action = _USER_ACTION.get()
        return True


class _Iso8601Formatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, _: str | None = None) -> str:
        return datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds")


class Logger:
    def __init__(self, name: str, extra: dict[str, Any] | None = None):
        self._logger = logging.getLogger(name)
        self._extra = dict(extra or {})

    def bind(self, **extra: Any) -> "Logger":
        bound = dict(self._extra)
        bound.update(extra)
        return Logger(self._logger.name, extra=bound)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exc_info"] = True
        self._log(logging.ERROR, message, *args, **kwargs)

    def _log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        extra = dict(self._extra)
        provided = kwargs.pop("extra", None)
        if isinstance(provided, dict):
            extra.update(provided)

        self._logger.log(level, message, *args, extra=extra, **kwargs)


def get_logger(name: str) -> Logger:
    return Logger(name)


def set_log_context(*, request_id: str | None = None, user_action: str | None = None) -> None:
    if request_id is not None:
        _REQUEST_ID.set(request_id)
    if user_action is not None:
        _USER_ACTION.set(user_action)


def clear_log_context() -> None:
    _REQUEST_ID.set("-")
    _USER_ACTION.set("-")


def setup_logging(config: LoggingConfig) -> Path:
    config.directory.mkdir(parents=True, exist_ok=True)

    formatter = _Iso8601Formatter(
        fmt=(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s "
            "| request_id=%(request_id)s user_action=%(user_action)s"
        )
    )
    context_filter = _ContextFilter()

    root_logger = logging.getLogger("zstar")
    root_logger.setLevel(getattr(logging, config.level))
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
        handler.close()
    root_logger.propagate = False

    file_handler = RotatingFileHandler(
        filename=config.file_path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)

    if config.stdout:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(context_filter)
        root_logger.addHandler(stream_handler)

    return config.file_path
