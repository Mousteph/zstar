from fastapi.testclient import TestClient

from zstar.api.ai_assistant import assistant_router
from zstar.api.start_backend import app
from zstar.llm.models import StrategyGeneration

client = TestClient(app)


def test_generate_assistant_returns_summary_then_code_markdown(monkeypatch):
    class DummyGenerator:
        def get_strategy_code(self, user_prompt: str, model: str | None = None) -> StrategyGeneration:
            return StrategyGeneration(
                name="RSI mean reversion",
                summary=f"Generated from: {user_prompt}",
                assumptions=["Assume daily candles"],
                code="print('hello zstar')",
            )

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post("/api/ai-assistant/generate", json={"message": "Build an RSI strategy"})

    assert response.status_code == 200
    response_json = response.json()
    assert "## Summary" in response_json["markdown"]
    assert "Generated from: Build an RSI strategy" in response_json["markdown"]
    assert "## Strategy Code" in response_json["markdown"]
    assert "```python" in response_json["markdown"]
    assert "print('hello zstar')" in response_json["markdown"]


def test_generate_assistant_passes_optional_model_to_code_generator(monkeypatch):
    captured: dict[str, str | None] = {"model": None}

    class DummyGenerator:
        def get_strategy_code(self, user_prompt: str, model: str | None = None) -> StrategyGeneration:
            captured["model"] = model
            return StrategyGeneration(
                name="Trend strategy",
                summary="Summary",
                assumptions=[],
                code="print('ok')",
            )

    monkeypatch.setattr(assistant_router, "_build_code_generator", lambda: DummyGenerator())
    response = client.post(
        "/api/ai-assistant/generate",
        json={"message": "Build a trend strategy", "model": "qwen2.5-coder:7b"},
    )

    assert response.status_code == 200
    assert captured["model"] == "qwen2.5-coder:7b"


def test_generate_assistant_rejects_blank_message():
    response = client.post("/api/ai-assistant/generate", json={"message": "   "})

    assert response.status_code == 422


def test_generate_assistant_rejects_missing_message():
    response = client.post("/api/ai-assistant/generate", json={})

    assert response.status_code == 422


def test_generate_assistant_rejects_unexpected_fields():
    response = client.post(
        "/api/ai-assistant/generate",
        json={
            "message": "Hello",
            "unexpected": "field",
        },
    )

    assert response.status_code == 422
