from pydantic import BaseModel, Field, field_validator, model_validator


class DataLoaderConfigModel(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    start_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)
    interval: str = Field(default="1d")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol cannot be empty")

        return normalized


    @model_validator(mode="after")
    def validate_dates(self) -> "DataLoaderConfigModel":
        if self.end_date is not None and self.start_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date")

        return self
