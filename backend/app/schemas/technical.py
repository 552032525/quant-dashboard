from pydantic import BaseModel
from typing import Optional

class IndicatorData(BaseModel):
    dates: list[str]
    open: list[Optional[float]]
    high: list[Optional[float]]
    low: list[Optional[float]]
    close: list[Optional[float]]
    volume: list[Optional[float]]
    ma5: list[Optional[float]]
    ma10: list[Optional[float]]
    ma20: list[Optional[float]]
    ma60: list[Optional[float]]
    boll_up: list[Optional[float]]
    boll_mid: list[Optional[float]]
    boll_dn: list[Optional[float]]
    macd_dif: list[Optional[float]]
    macd_dea: list[Optional[float]]
    macd_bar: list[Optional[float]]
    rsi6: list[Optional[float]]
    rsi12: list[Optional[float]]
    rsi24: list[Optional[float]]
    kdj_k: list[Optional[float]]
    kdj_d: list[Optional[float]]
    kdj_j: list[Optional[float]]

class AnomalyItem(BaseModel):
    date: str
    type: str
    description: str

class AnomalyResult(BaseModel):
    code: str
    name: str
    anomalies: list[AnomalyItem]

class ScoreResult(BaseModel):
    code: str
    name: str
    trend: int
    momentum: int
    volatility: int
    volume_score: int
    total: int
    description: str

class AIReport(BaseModel):
    code: str
    name: str
    content: str
    summary: str
