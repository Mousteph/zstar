from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssistantEchoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=8000, description="User prompt message")

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty")
        return value


class AssistantEchoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str = Field(min_length=1, max_length=8000, description="Assistant markdown response")
