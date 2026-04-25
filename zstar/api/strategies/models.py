from pydantic import BaseModel


class StrategiesListResponse(BaseModel):
    strategies: list[str]
