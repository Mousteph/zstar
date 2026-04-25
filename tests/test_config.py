from __future__ import annotations

from pathlib import Path

import pytest

from zstar.api.settings import get_settings
from zstar.config import ConfigError, clear_config_cache, load_config


def _write_config(path: Path, strategies_dir: Path, **overrides: str) -> Path:
    backend_port = overrides.get("backend_port", "8000")
    backend_origin = overrides.get("backend_origin", "http://localhost:3000")
    frontend_proxy = overrides.get("frontend_proxy", "http://backend:8000")
    extra = overrides.get("extra", "")

    path.write_text(
        "\n".join(
            [
                "backend:",
                '  host: "0.0.0.0"',
                f"  port: {backend_port}",
                "  allow_origins:",
                f'    - "{backend_origin}"',
                "frontend:",
                '  host: "0.0.0.0"',
                "  port: 3000",
                f'  backend_proxy_url: "{frontend_proxy}"',
                "paths:",
                f'  strategies_dir: "{strategies_dir}"',
                '  default_strategy_name: "default_strategy"',
                extra,
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_load_config_reads_valid_yaml(tmp_path):
    clear_config_cache()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = _write_config(tmp_path / "config.yaml", strategies_dir)

    config = load_config(config_path)

    assert config.backend.host == "0.0.0.0"
    assert config.backend.port == 8000
    assert config.backend.allow_origins == ("http://localhost:3000",)
    assert config.frontend.backend_proxy_url == "http://backend:8000"
    assert config.paths.strategies_dir == strategies_dir.resolve()


def test_load_config_raises_clear_error_for_missing_file(tmp_path):
    clear_config_cache()
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigError, match="Configuration file"):
        load_config(missing_path)

    try:
        load_config(missing_path)
    except ConfigError as exc:
        message = str(exc)

    assert str(missing_path) in message
    assert "config.yaml" in message
    assert "python -m zstar.api config.yaml" in message


def test_load_config_raises_clear_error_for_missing_required_field(tmp_path):
    clear_config_cache()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "backend:",
                '  host: "0.0.0.0"',
                "  allow_origins:",
                '    - "http://localhost:3000"',
                "frontend:",
                '  host: "0.0.0.0"',
                "  port: 3000",
                '  backend_proxy_url: "http://backend:8000"',
                "paths:",
                f'  strategies_dir: "{strategies_dir}"',
                '  default_strategy_name: "default_strategy"',
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path)

    message = str(exc_info.value)
    assert "backend.port" in message
    assert "Expected integer from 1 to 65535" in message
    assert "Example: 8000" in message


def test_load_config_rejects_invalid_url_port_path_and_unknown_fields(tmp_path):
    clear_config_cache()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = _write_config(
        tmp_path / "config.yaml",
        strategies_dir,
        backend_port="70000",
        backend_origin="localhost:3000",
        frontend_proxy="backend:8000",
        extra="unknown: true",
    )

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path)

    message = str(exc_info.value)
    assert "backend.port" in message
    assert "backend.allow_origins" in message
    assert "frontend.backend_proxy_url" in message
    assert "unknown" in message


def test_load_config_rejects_string_ports(tmp_path):
    clear_config_cache()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = _write_config(tmp_path / "config.yaml", strategies_dir, backend_port='"8000"')

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path)

    message = str(exc_info.value)
    assert "backend.port" in message
    assert "Expected integer from 1 to 65535" in message


def test_load_config_rejects_missing_strategies_dir(tmp_path):
    clear_config_cache()
    config_path = _write_config(tmp_path / "config.yaml", tmp_path / "missing-strategies")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_path)

    assert "paths.strategies_dir" in str(exc_info.value)
    assert "Example: strategies" in str(exc_info.value)


def test_loaded_config_is_immutable(tmp_path):
    clear_config_cache()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = _write_config(tmp_path / "config.yaml", strategies_dir)
    config = load_config(config_path)

    with pytest.raises(Exception):
        config.backend.port = 9000

    with pytest.raises(Exception):
        config.backend.allow_origins += ("https://example.com",)


def test_load_config_caches_by_resolved_path(tmp_path):
    clear_config_cache()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = _write_config(tmp_path / "config.yaml", strategies_dir)

    first = load_config(config_path)
    second = load_config(config_path)

    assert first is second


def test_get_settings_shim_uses_canonical_config_loader(tmp_path):
    get_settings.cache_clear()
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    config_path = _write_config(tmp_path / "config.yaml", strategies_dir)

    settings = get_settings(config_path)

    assert settings.backend.port == 8000
    assert settings.paths.default_strategy_name == "default_strategy"
