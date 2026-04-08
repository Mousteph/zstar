import yaml
from pathlib import Path
from typing import Any, Dict


def read_yaml_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data or {}
