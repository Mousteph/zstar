from fastapi import APIRouter

from .models import AssistantEchoRequest, AssistantEchoResponse

router = APIRouter(prefix="/api/ai-assistant", tags=["ai-assistant"])


@router.post("/echo", response_model=AssistantEchoResponse)
def echo_assistant_message(request: AssistantEchoRequest) -> AssistantEchoResponse:
    return AssistantEchoResponse(markdown=request.message)
