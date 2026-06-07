"""持仓&智能调仓 - Schemas"""
from pydantic import BaseModel


class PositionAdvice(BaseModel):
    code: str
    name: str
    current_weight: float
    suggested_weight: float
    action: str  # hold/buy_more/reduce/add
    reason: str


class RebalanceResult(BaseModel):
    advice: list[PositionAdvice]
    summary: str
