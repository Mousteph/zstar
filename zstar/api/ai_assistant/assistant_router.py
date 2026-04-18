from fastapi import APIRouter, HTTPException

from .models import AssistantGenerateRequest, AssistantGenerateResponse

router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])


def _build_code_generator():
    from zstar.llm.code_generator import CodeGenerator

    return CodeGenerator()


def _build_strategy_markdown(summary: str, code: str) -> str:
    return f"## Summary\n\n{summary}\n\n## Strategy Code\n\n```python\n{code}\n```"


@router.post("/generate")
def generate_assistant_message(request: AssistantGenerateRequest) -> AssistantGenerateResponse:
    try:
        code_generator = _build_code_generator()
        strategy_generation = code_generator.get_strategy_code(
            user_prompt=request.message,
            model=request.model,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Assistant generation failed: {str(exc)}") from exc

    return AssistantGenerateResponse(
        markdown=_build_strategy_markdown(
            summary=strategy_generation.summary,
            code=strategy_generation.code,
        )
    )
