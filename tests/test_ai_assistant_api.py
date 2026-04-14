from fastapi.testclient import TestClient

from zstar.api.start_backend import app

client = TestClient(app)


def test_echo_assistant_returns_same_message():
    response = client.post("/api/ai-assistant/echo", json={"message": "Hello ZStar"})

    assert response.status_code == 200
    assert response.json() == {"markdown": "Hello ZStar"}


def test_echo_assistant_keeps_markdown_payload_unchanged():
    markdown_message = "## Plan\n\n- Buy\n- Hold\n\n```python\nprint('zstar')\n```"
    response = client.post("/api/ai-assistant/echo", json={"message": markdown_message})

    assert response.status_code == 200
    assert response.json() == {"markdown": markdown_message}


def test_echo_assistant_rejects_blank_message():
    response = client.post("/api/ai-assistant/echo", json={"message": "   "})

    assert response.status_code == 422


def test_echo_assistant_rejects_missing_message():
    response = client.post("/api/ai-assistant/echo", json={})

    assert response.status_code == 422


def test_echo_assistant_rejects_unexpected_fields():
    response = client.post(
        "/api/ai-assistant/echo",
        json={
            "message": "Hello",
            "unexpected": "field",
        },
    )

    assert response.status_code == 422
