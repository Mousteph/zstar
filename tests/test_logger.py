from __future__ import annotations

from pathlib import Path

from zstar.config import LoggingConfig
from zstar.logger import get_logger, set_log_context, clear_log_context, setup_logging


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_setup_logging_writes_iso8601_structured_log_line(tmp_path):
    config = LoggingConfig(
        level="DEBUG",
        directory=tmp_path / "logs",
        filename="app.log",
        max_bytes=10 * 1024 * 1024,
        backup_count=5,
        stdout=False,
    )
    log_file = setup_logging(config)
    logger = get_logger("zstar.tests.logger")

    set_log_context(request_id="req-123", user_action="POST /api/backtest/run")
    logger.info("backtest started")
    clear_log_context()

    lines = _read_lines(log_file)
    assert len(lines) == 1

    line = lines[0]
    assert " | INFO | zstar.tests.logger | backtest started " in line
    assert "request_id=req-123" in line
    assert "user_action=POST /api/backtest/run" in line
    assert "T" in line.split(" | ")[0]
    assert "+00:00" in line.split(" | ")[0]


def test_setup_logging_reconfiguration_prevents_duplicate_handlers(tmp_path):
    config = LoggingConfig(
        level="DEBUG",
        directory=tmp_path / "logs",
        filename="app.log",
        max_bytes=10 * 1024 * 1024,
        backup_count=5,
        stdout=False,
    )

    setup_logging(config)
    setup_logging(config)

    logger = get_logger("zstar.tests.logger")
    logger.info("single write")

    lines = _read_lines(config.file_path)
    assert len(lines) == 1
    assert "single write" in lines[0]
