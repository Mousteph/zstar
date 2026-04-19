import json
import asyncio
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from zstar.llm.code_generator import CodeGenerator

from .models import AssistantGenerateRequest

router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])

def _build_strategy_markdown(summary: str, code: str) -> str:
    return f"## Summary\n\n{summary}\n\n## Strategy Code\n\n```python\n{code}\n```"

def _serialize_ndjson_event(payload: dict[str, Any]) -> str:
    return f"{json.dumps(payload, ensure_ascii=False)}\n"

@router.post("/generate-stream")
async def generate_assistant_message_stream(request: AssistantGenerateRequest, raw_request: Request) -> StreamingResponse:
    event_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit_status(step_id: str, label: str, state: str) -> None:
        loop.call_soon_threadsafe(
            event_queue.put_nowait,
            {
                "type": "status",
                "step_id": step_id,
                "label": label,
                "state": state,
            }
        )

    def worker_task():
        """The blocking LLM work happens here in a separate thread."""
        try:
            generator = CodeGenerator()
            strategy = generator.generate_strategy_code(
                user_prompt=request.message,
                progress_callback=emit_status,
            )
            
            loop.call_soon_threadsafe(
                event_queue.put_nowait,
                {
                    "type": "final",
                    "markdown": _build_strategy_markdown(strategy.summary, strategy.code),
                    "strategy_code": strategy.code,
                    "is_strategy_generation": True,
                }
            )
        except Exception as exc:
            loop.call_soon_threadsafe(
                event_queue.put_nowait,
                {"type": "error", "detail": f"Generation failed: {str(exc)}"}
            )
        finally:
            loop.call_soon_threadsafe(event_queue.put_nowait, None)

    async def stream_generator() -> AsyncGenerator[str, None]:
        worker_future = loop.run_in_executor(None, worker_task)
        
        try:
            while True:
                if await raw_request.is_disconnected():
                    break

                payload = await event_queue.get()
                if payload is None:
                    break
                yield _serialize_ndjson_event(payload)
        finally:
            if not worker_future.done():
                print("Request disconnected, cancelling worker task...")


    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
