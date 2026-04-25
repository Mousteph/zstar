from pathlib import Path

from zstar.config import AppConfig, clear_config_cache, load_config

BackendSettings = AppConfig


def get_settings(file_path: str | Path | None = None) -> AppConfig:
    return load_config(file_path)


get_settings.cache_clear = clear_config_cache  # type: ignore[attr-defined]
