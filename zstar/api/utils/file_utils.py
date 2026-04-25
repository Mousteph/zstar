from pathlib import Path
from typing import Optional

from zstar.api.constants import DEFAULT_STRATEGY_NAME, PYTHON_FILE_SUFFIX, STRATEGIES_DIR
from zstar.core.exceptions import StrategyValidationError


def list_strategy_filenames(strategies_dir: Optional[Path] = None) -> list[str]:
    target_dir = strategies_dir or STRATEGIES_DIR
    if not target_dir.exists():
        return []

    return sorted(
        file_path.stem
        for file_path in target_dir.iterdir()
        if file_path.is_file() and file_path.suffix == PYTHON_FILE_SUFFIX
    )


def normalize_strategy_filename(strategy_filename: Optional[str]) -> str:
    if strategy_filename is None:
        return DEFAULT_STRATEGY_NAME

    normalized = strategy_filename.strip()
    if not normalized:
        return DEFAULT_STRATEGY_NAME

    if normalized.endswith(PYTHON_FILE_SUFFIX):
        normalized = normalized[: -len(PYTHON_FILE_SUFFIX)].strip()

    if not normalized:
        raise StrategyValidationError("Strategy filename cannot be empty.")

    if "/" in normalized or "\\" in normalized or Path(normalized).name != normalized:
        raise StrategyValidationError("Invalid strategy filename. Use a base filename without path separators.")

    return normalized


def resolve_strategy_file(strategy_filename: Optional[str], strategies_dir: Optional[Path] = None) -> Path:
    normalized_name = normalize_strategy_filename(strategy_filename)
    target_dir = strategies_dir or STRATEGIES_DIR
    strategy_path = (target_dir / f"{normalized_name}{PYTHON_FILE_SUFFIX}").resolve()
    strategies_root = target_dir.resolve()

    try:
        strategy_path.relative_to(strategies_root)
    except ValueError as exc:
        raise StrategyValidationError("Invalid strategy filename path.") from exc

    if not strategy_path.is_file():
        raise StrategyValidationError(f"Strategy file '{normalized_name}{PYTHON_FILE_SUFFIX}' was not found.")

    return strategy_path
