from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from typing import Literal
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, field_validator


DEFAULT_CONFIG_FILE = "config.yaml"


class ConfigError(RuntimeError):
    """Raised when application configuration cannot be loaded or validated."""


def _example_config_path() -> str:
    return DEFAULT_CONFIG_FILE


def _validate_http_url(value: str, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            f"{field_name} must be an HTTP(S) URL. "
            f"Expected format: https://host[:port]. Example: http://localhost:3000"
        )
    return value


class BackendConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = Field(..., min_length=1)
    port: StrictInt = Field(..., ge=1, le=65535)
    allow_origins: tuple[str, ...] = Field(..., min_length=1)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        if value.strip() != value or not value.strip():
            raise ValueError("host must be a non-empty hostname or IP address. Example: 0.0.0.0")
        return value

    @field_validator("allow_origins")
    @classmethod
    def validate_allow_origins(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for origin in value:
            _validate_http_url(origin, "backend.allow_origins")
        return value


class FrontendConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = Field(..., min_length=1)
    port: StrictInt = Field(..., ge=1, le=65535)
    backend_proxy_url: str = Field(..., min_length=1)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        if value.strip() != value or not value.strip():
            raise ValueError("host must be a non-empty hostname or IP address. Example: 0.0.0.0")
        return value

    @field_validator("backend_proxy_url")
    @classmethod
    def validate_backend_proxy_url(cls, value: str) -> str:
        return _validate_http_url(value, "frontend.backend_proxy_url")


class PathsConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    strategies_dir: Path = Field(...)
    data_dir: Path = Field(...)

    @field_validator("strategies_dir")
    @classmethod
    def validate_strategies_dir(cls, value: Path, info: Any) -> Path:
        base_dir = Path(info.context["base_dir"]) if info.context and "base_dir" in info.context else Path.cwd()
        resolved = value if value.is_absolute() else base_dir / value
        resolved = resolved.resolve()

        if not resolved.exists():
            raise ValueError(
                "paths.strategies_dir must point to an existing directory. "
                "Expected format: relative or absolute path. Example: strategies"
            )
        if not resolved.is_dir():
            raise ValueError(
                "paths.strategies_dir must point to a directory. "
                "Expected format: relative or absolute path. Example: strategies"
            )

        return resolved

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, value: Path, info: Any) -> Path:
        base_dir = Path(info.context["base_dir"]) if info.context and "base_dir" in info.context else Path.cwd()
        resolved = value if value.is_absolute() else base_dir / value
        resolved = resolved.resolve()

        if not resolved.exists():
            resolved.mkdir(parents=True, exist_ok=True)

        if not resolved.is_dir():
            raise ValueError(
                "paths.data_dir must point to a directory. "
                "Expected format: relative or absolute path. Example: data"
            )

        return resolved


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LoggingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    level: LogLevel = "DEBUG"
    directory: Path = Field(default=Path("logs"))
    filename: str = Field(default="app.log", min_length=1)
    max_bytes: StrictInt = Field(default=10 * 1024 * 1024, ge=1)
    backup_count: StrictInt = Field(default=5, ge=1)
    stdout: bool = Field(default=True)

    @field_validator("directory")
    @classmethod
    def validate_directory(cls, value: Path, info: Any) -> Path:
        base_dir = Path(info.context["base_dir"]) if info.context and "base_dir" in info.context else Path.cwd()
        resolved = value if value.is_absolute() else base_dir / value
        return resolved.resolve()

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise ValueError("filename must be non-empty. Example: app.log")
        if Path(candidate).name != candidate:
            raise ValueError("filename must be a base file name without directories. Example: app.log")
        return candidate

    @property
    def file_path(self) -> Path:
        return self.directory / self.filename


class AppConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    backend: BackendConfig
    frontend: FrontendConfig
    paths: PathsConfig
    logging: LoggingConfig


FIELD_HINTS = {
    "backend": "Expected object with host, port, and allow_origins. Example: backend: {host: '0.0.0.0', port: 8000, allow_origins: ['http://localhost:3000']}",
    "backend.host": "Expected non-empty hostname or IP address. Example: 0.0.0.0",
    "backend.port": "Expected integer from 1 to 65535. Example: 8000",
    "backend.allow_origins": "Expected non-empty list of HTTP(S) origins. Example: ['http://localhost:3000']",
    "frontend": "Expected object with host, port, and backend_proxy_url. Example: frontend: {host: '0.0.0.0', port: 3000, backend_proxy_url: 'http://backend:8000'}",
    "frontend.host": "Expected non-empty hostname or IP address. Example: 0.0.0.0",
    "frontend.port": "Expected integer from 1 to 65535. Example: 3000",
    "frontend.backend_proxy_url": "Expected HTTP(S) URL. Example: http://backend:8000",
    "paths": "Expected object with strategies_dir and data_dir. Example: paths: {strategies_dir: 'strategies', data_dir: 'data'}",
    "paths.strategies_dir": "Expected existing directory path. Example: strategies",
    "paths.data_dir": "Expected existing directory path. Example: data",
    "logging": "Expected object with level, directory, filename, max_bytes, backup_count, and stdout.",
    "logging.level": "Expected one of: DEBUG, INFO, WARNING, ERROR, CRITICAL. Example: INFO",
    "logging.directory": "Expected relative or absolute path. Example: logs",
    "logging.filename": "Expected filename without directories. Example: app.log",
    "logging.max_bytes": "Expected positive integer. Example: 10485760",
    "logging.backup_count": "Expected positive integer. Example: 5",
    "logging.stdout": "Expected boolean. Example: true",
}


def _field_name(location: tuple[Any, ...]) -> str:
    return ".".join(str(part) for part in location)


def _format_validation_error(error: ValidationError, path: Path) -> ConfigError:
    lines = [f"Invalid configuration in '{path}'."]
    for item in error.errors():
        field = _field_name(item["loc"])
        hint = FIELD_HINTS.get(field, "Check the config schema in config.yaml.")
        lines.append(f"- Field '{field}': {item['msg']}. {hint}")
    return ConfigError("\n".join(lines))


def _read_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(
            f"Configuration file '{path}' was not found. "
            f"Create config.yaml or pass a config path explicitly. Example: python -m zstar.api {_example_config_path()}"
        )
    if not path.is_file():
        raise ConfigError(
            f"Configuration path '{path}' is not a file. "
            "Expected a YAML file. Example: config.yaml"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigError(
            f"Configuration file '{path}' is not valid YAML. "
            "Expected a YAML object. Example field: backend.port: 8000"
        ) from exc

    if data is None:
        raise ConfigError(
            f"Configuration file '{path}' is empty. "
            "Expected backend, frontend, paths, and optional logging sections. Example: config.yaml"
        )
    if not isinstance(data, dict):
        raise ConfigError(
            f"Configuration file '{path}' must contain a YAML object. "
            "Expected top-level fields: backend, frontend, paths, and optional logging."
        )

    return data


def _resolve_config_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser().resolve()

    default_path = Path(DEFAULT_CONFIG_FILE)
    return default_path.resolve()


@lru_cache()
def _load_config_from_resolved_path(resolved_path: str) -> AppConfig:
    path = Path(resolved_path)
    data = _read_config_file(path)
    data.setdefault("logging", {})
    try:
        return AppConfig.model_validate(data, context={"base_dir": path.parent})
    except ValidationError as exc:
        raise _format_validation_error(exc, path) from exc


def load_config(path: str | Path | None = None) -> AppConfig:
    resolved_path = _resolve_config_path(path)
    return _load_config_from_resolved_path(str(resolved_path))


def clear_config_cache() -> None:
    _load_config_from_resolved_path.cache_clear()


load_config.cache_clear = clear_config_cache  # type: ignore[attr-defined]
