from pydantic import BaseModel
from typing import List


class StrategyGeneration(BaseModel):
    name: str
    summary: str
    assumptions: List[str]
    code: str