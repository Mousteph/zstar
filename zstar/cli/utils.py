from pathlib import Path


def read_strategy_code(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Failed to read strategy file: {exc}") from exc


def resolve_output_path(value: str) -> Path:
    path = Path(value).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    return path
