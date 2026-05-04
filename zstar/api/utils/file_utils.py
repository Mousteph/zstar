from pathlib import Path
from typing import Optional

from zstar.api.constants import CSV_FILE_SUFFIX, PYTHON_FILE_SUFFIX
from zstar.config import load_config
from zstar.core.exceptions import CsvDataError, StrategyValidationError


def _configured_strategies_dir() -> Path:
    return load_config().paths.strategies_dir


def _configured_default_strategy_name() -> str:
    return load_config().paths.default_strategy_name


def _configured_data_dir() -> Path:
    return load_config().paths.data_dir


def list_strategy_filenames(strategies_dir: Optional[Path] = None) -> list[str]:
    target_dir = strategies_dir or _configured_strategies_dir()
    if not target_dir.exists():
        return []

    return sorted(
        file_path.stem
        for file_path in target_dir.iterdir()
        if file_path.is_file() and file_path.suffix == PYTHON_FILE_SUFFIX
    )


def list_csv_filenames(data_dir: Optional[Path] = None) -> list[str]:
    target_dir = data_dir or _configured_data_dir()
    if not target_dir.exists():
        return []

    return sorted(
        file_path.name
        for file_path in target_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() == CSV_FILE_SUFFIX
    )


def normalize_strategy_filename(strategy_filename: Optional[str]) -> str:
    if strategy_filename is None:
        return _configured_default_strategy_name()

    normalized = strategy_filename.strip()
    if not normalized:
        return _configured_default_strategy_name()

    if normalized.endswith(PYTHON_FILE_SUFFIX):
        normalized = normalized[: -len(PYTHON_FILE_SUFFIX)].strip()

    if not normalized:
        raise StrategyValidationError("Strategy filename cannot be empty.")

    if "/" in normalized or "\\" in normalized or Path(normalized).name != normalized:
        raise StrategyValidationError("Invalid strategy filename. Use a base filename without path separators.")

    return normalized


def resolve_strategy_file(strategy_filename: Optional[str], strategies_dir: Optional[Path] = None) -> Path:
    normalized_name = normalize_strategy_filename(strategy_filename)
    target_dir = strategies_dir or _configured_strategies_dir()
    strategy_path = (target_dir / f"{normalized_name}{PYTHON_FILE_SUFFIX}").resolve()
    strategies_root = target_dir.resolve()

    try:
        strategy_path.relative_to(strategies_root)
    except ValueError as exc:
        raise StrategyValidationError("Invalid strategy filename path.") from exc

    if not strategy_path.is_file():
        raise StrategyValidationError(f"Strategy file '{normalized_name}{PYTHON_FILE_SUFFIX}' was not found.")

    return strategy_path


def normalize_csv_filename(filename: str) -> str:
    normalized = filename.strip()
    if not normalized:
        raise CsvDataError("CSV filename cannot be empty.")

    candidate = Path(normalized).name
    if candidate != normalized or Path(candidate).suffix.lower() != CSV_FILE_SUFFIX:
        raise CsvDataError("Uploaded file must be a .csv file name without directories.")

    return candidate


def ensure_data_dir(data_dir: Optional[Path] = None) -> Path:
    target_dir = (data_dir or _configured_data_dir()).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def resolve_csv_file(filename: str, data_dir: Optional[Path] = None) -> Path:
    normalized_name = normalize_csv_filename(filename)
    target_dir = ensure_data_dir(data_dir)
    csv_path = (target_dir / normalized_name).resolve()

    try:
        csv_path.relative_to(target_dir)
    except ValueError as exc:
        raise CsvDataError("Invalid CSV filename path.") from exc

    if not csv_path.is_file():
        raise CsvDataError(f"CSV file {normalized_name} was not found.")

    return csv_path
