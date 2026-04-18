import json
from queue import Queue
from threading import Thread
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .models import AssistantGenerateRequest

router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])


def _build_code_generator():
    from zstar.llm.code_generator import CodeGenerator

    return CodeGenerator()


def _build_strategy_markdown(summary: str, code: str) -> str:
    return f"## Summary\n\n{summary}\n\n## Strategy Code\n\n```python\n{code}\n```"


def _serialize_ndjson_event(payload: dict[str, Any]) -> str:
    return f"{json.dumps(payload, ensure_ascii=False)}\n"


@router.post("/generate-stream")
def generate_assistant_message_stream(request: AssistantGenerateRequest) -> StreamingResponse:
    event_queue: Queue[dict[str, Any] | None] = Queue()

    def emit_status(step_id: str, label: str, state: str) -> None:
        event_queue.put(
            {
                "type": "status",
                "step_id": step_id,
                "label": label,
                "state": state,
            }
        )

    def worker() -> None:
        try:
            code_generator = _build_code_generator()
            strategy_generation = code_generator.get_strategy_code(
                user_prompt=request.message,
                model=request.model,
                progress_callback=emit_status,
            )
            event_queue.put(
                {
                    "type": "final",
                    "markdown": _build_strategy_markdown(
                        summary=strategy_generation.summary,
                        code=strategy_generation.code,
                    ),
                    "strategy_code": strategy_generation.code,
                    "is_strategy_generation": True,
                }
            )
        except Exception as exc:
            event_queue.put(
                {
                    "type": "error",
                    "detail": f"Assistant generation failed: {str(exc)}",
                }
            )
        finally:
            event_queue.put(None)

    def stream_events():
        while True:
            payload = event_queue.get()
            if payload is None:
                break
            yield _serialize_ndjson_event(payload)

    Thread(target=worker, daemon=True).start()
    return StreamingResponse(
        stream_events(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
