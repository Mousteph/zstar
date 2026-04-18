from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssistantGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=8000, description="User prompt message")
    model: str | None = Field(
        default=None,
        max_length=128,
        description="Optional model override used for strategy generation",
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty")
        return value

    @field_validator("model")
    @classmethod
    def normalize_optional_model(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class AssistantGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str = Field(min_length=1, max_length=8000, description="Assistant markdown response")
