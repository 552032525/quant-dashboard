"""风控预警 - Schemas"""
from pydantic import BaseModel
from typing import Optional


class RiskItem(BaseModel):
    type: str  # financial/legal/price/volume
    severity: str  # high/medium/low
    description: str
    detail: str = ""


class RiskResult(BaseModel):
    code: str
    name: str
    overall_risk: str  # high/medium/low
    items: list[RiskItem]
    suggestion: str


class MarketRiskSummary(BaseModel):
    date: str
    risk_level: str
    signals: list[str]
    description: str


class PortfolioRiskCheck(BaseModel):
    code: str
    name: str
    weight_pct: float
    risk_flags: list[str]
    stop_loss_price: float
    take_profit_price: float
