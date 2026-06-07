"""个性化智能盯盘 - Schemas"""
from pydantic import BaseModel
from typing import Optional


class AlertRule(BaseModel):
    id: Optional[int] = None
    code: str
    name: str = ""
    type: str  # price_break/change_pct/volume_spike/ma_cross
    threshold: float  # 触发阈值
    direction: str = "above"  # above/below
    enabled: bool = True


class AlertEvent(BaseModel):
    code: str
    name: str
    type: str
    message: str
    time: str
    current_value: float


class WatchItem(BaseModel):
    code: str
    name: str
    price: float = 0
    change_pct: float = 0
    alert_count: int = 0
    sort_order: int = 0


class MonitorSummary(BaseModel):
    active_alerts: int
    triggered_today: int
    watchlist_count: int
    recent_events: list[AlertEvent]


class PositionRiskAlert(BaseModel):
    code: str
    name: str
    weight_pct: float
    message: str
    risk_level: str  # low/medium/high


class PositionRiskResult(BaseModel):
    total_assets: float
    position_count: int
    alerts: list[PositionRiskAlert]
    max_single_weight: float
    max_single_code: str
