from pydantic import BaseModel


class StrategyGeneration(BaseModel):
    name: str
    summary: str
    code: str
    can_answer: bool
