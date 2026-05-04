from pathlib import Path
from typing import Optional

from zstar.api.constants import CSV_FILE_SUFFIX
from zstar.config import load_config
from zstar.core.exceptions import CsvDataError


def _configured_data_dir() -> Path:
    return load_config().paths.data_dir


def list_csv_filenames(data_dir: Optional[Path] = None) -> list[str]:
    target_dir = data_dir or _configured_data_dir()
    if not target_dir.exists():
        return []

    return sorted(
        file_path.name
        for file_path in target_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() == CSV_FILE_SUFFIX
    )


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
