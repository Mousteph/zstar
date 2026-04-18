import json

from fastapi.testclient import TestClient

from zstar.api.ai_assistant import assistant_router
from zstar.api.start_backend import app
from zstar.llm.models import StrategyGeneration

client = TestClient(app)


def _parse_stream_events(response_text: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in response_text.splitlines() if line.strip()]


def test_generate_assistant_stream_rejects_blank_message():
    response = client.post("/api/ai-assistant/generate-stream", json={"message": "   "})

    assert response.status_code == 422


def test_generate_assistant_stream_rejects_missing_message():
    response = client.post("/api/ai-assistant/generate-stream", json={})

    assert response.status_code == 422


def test_generate_assistant_stream_rejects_unexpected_fields():
    response = client.post(
        "/api/ai-assistant/generate-stream",
        json={
            "message": "Hello",
            "unexpected": "field",
        },
    )

    assert response.status_code == 422


def test_generate_assistant_stream_emits_status_then_final(monkeypatch):
    class DummyGenerator:
        def get_strategy_code(
            self,
            user_prompt: str,
            model: str | None = None,
            progress_callback=None,
        ) -> StrategyGeneration:
            if progress_callback is not None:
                progress_callback("generate_code", "Generating code...", "running")
                progress_callback("generate_code", "Generating code...", "done")
                progress_callback("validate_syntax_1", "Validating syntax...", "running")
                progress_callback("validate_syntax_1", "Validating syntax...", "done")

            return StrategyGeneration(
                name="SMA crossover",
                summary=f"Generated from: {user_prompt}",
                assumptions=[],
                code="print('generated')",
            )

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post("/api/ai-assistant/generate-stream", json={"message": "Generate a strategy"})

    assert response.status_code == 200
    events = _parse_stream_events(response.text)
    assert len(events) >= 3
    assert events[0]["type"] == "status"
    assert events[0]["state"] == "running"
    assert events[-1]["type"] == "final"
    assert events[-1]["is_strategy_generation"] is True
    assert events[-1]["strategy_code"] == "print('generated')"
    assert "## Summary" in str(events[-1]["markdown"])
    assert "## Strategy Code" in str(events[-1]["markdown"])


def test_generate_assistant_stream_passes_optional_model(monkeypatch):
    captured: dict[str, str | None] = {"model": None}

    class DummyGenerator:
        def get_strategy_code(
            self,
            user_prompt: str,
            model: str | None = None,
            progress_callback=None,
        ) -> StrategyGeneration:
            captured["model"] = model
            return StrategyGeneration(
                name="SMA",
                summary="Summary",
                assumptions=[],
                code="print('ok')",
            )

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post(
        "/api/ai-assistant/generate-stream",
        json={"message": "Generate strategy", "model": "qwen2.5-coder:7b"},
    )

    assert response.status_code == 200
    assert captured["model"] == "qwen2.5-coder:7b"


def test_generate_assistant_stream_emits_retry_events(monkeypatch):
    class DummyGenerator:
        def get_strategy_code(
            self,
            user_prompt: str,
            model: str | None = None,
            progress_callback=None,
        ) -> StrategyGeneration:
            if progress_callback is not None:
                progress_callback("generate_code", "Generating code...", "running")
                progress_callback("generate_code", "Generating code...", "done")
                progress_callback("validate_syntax_1", "Validating syntax...", "running")
                progress_callback("validate_syntax_1", "Validating syntax...", "done")
                progress_callback(
                    "retry_generation_1",
                    "Validation failed (1). Retrying (1/2)...",
                    "running",
                )
                progress_callback(
                    "retry_generation_1",
                    "Validation failed (1). Retrying (1/2)...",
                    "done",
                )

            return StrategyGeneration(
                name="Retry strategy",
                summary="Summary",
                assumptions=[],
                code="print('retry-ok')",
            )

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post("/api/ai-assistant/generate-stream", json={"message": "Generate retry strategy"})

    assert response.status_code == 200
    events = _parse_stream_events(response.text)
    retry_event = next(
        (
            event
            for event in events
            if event["type"] == "status" and str(event.get("step_id", "")).startswith("retry_generation_")
        ),
        None,
    )
    assert retry_event is not None


def test_generate_assistant_stream_emits_error_event(monkeypatch):
    class DummyGenerator:
        def get_strategy_code(
            self,
            user_prompt: str,
            model: str | None = None,
            progress_callback=None,
        ) -> StrategyGeneration:
            raise RuntimeError("stream failed")

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post("/api/ai-assistant/generate-stream", json={"message": "Generate strategy"})

    assert response.status_code == 200
    events = _parse_stream_events(response.text)
    assert events[-1]["type"] == "error"
    assert "stream failed" in str(events[-1]["detail"])


def test_generate_assistant_stream_sets_non_buffering_headers(monkeypatch):
    class DummyGenerator:
        def get_strategy_code(
            self,
            user_prompt: str,
            model: str | None = None,
            progress_callback=None,
        ) -> StrategyGeneration:
            return StrategyGeneration(
                name="SMA",
                summary="Summary",
                assumptions=[],
                code="print('ok')",
            )

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post("/api/ai-assistant/generate-stream", json={"message": "Generate strategy"})

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
