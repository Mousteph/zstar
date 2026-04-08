from pathlib import Path
from pydantic import BaseModel, Field

from zstar.utils import read_yaml_file
from typing import List
from functools import lru_cache


DEFAULT_ALLOW_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


class BackendSettings(BaseModel):
    backend_allow_origins: List[str] = Field(default_factory=lambda: DEFAULT_ALLOW_ORIGINS.copy())
    backend_host: str = Field(default="localhost")
    backend_port: int = Field(default=8000)


@lru_cache()
def get_settings(file_path: str) -> BackendSettings:
    setting = read_yaml_file(Path(file_path))

    return BackendSettings.model_validate(setting)
