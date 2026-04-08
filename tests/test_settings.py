import pytest
from pydantic import ValidationError

import zstar.api.settings as settings_module
from zstar.api.settings import BackendSettings, DEFAULT_ALLOW_ORIGINS, get_settings


def test_settings_default_values():
    settings = BackendSettings()

    assert settings.backend_allow_origins == DEFAULT_ALLOW_ORIGINS
    assert settings.backend_host == "localhost"
    assert settings.backend_port == 8000


def test_settings_accepts_explicit_values():
    settings = BackendSettings(
        backend_allow_origins=["http://localhost:3000", "https://app.example.com"],
        backend_host="0.0.0.0",
        backend_port=9000,
    )

    assert settings.backend_allow_origins == [
        "http://localhost:3000",
        "https://app.example.com",
    ]
    assert settings.backend_host == "0.0.0.0"
    assert settings.backend_port == 9000


def test_settings_rejects_invalid_allow_origins_type():
    with pytest.raises(ValidationError):
        BackendSettings(backend_allow_origins="http://localhost:3000")


def test_get_settings_reads_yaml_and_uses_cache(monkeypatch):
    calls = {"count": 0}

    def _fake_read_yaml_file(_path):
        calls["count"] += 1
        return {
            "backend_allow_origins": ["http://localhost:3000"],
            "backend_host": "0.0.0.0",
            "backend_port": 9001,
        }

    get_settings.cache_clear()
    monkeypatch.setattr(settings_module, "read_yaml_file", _fake_read_yaml_file)

    first = get_settings("some/path.yaml")
    second = get_settings("some/path.yaml")

    assert first.backend_host == "0.0.0.0"
    assert first.backend_port == 9001
    assert second.backend_port == 9001
    assert calls["count"] == 1

    get_settings.cache_clear()
