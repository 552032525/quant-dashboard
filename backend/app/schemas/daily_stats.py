from pydantic import BaseModel
from datetime import date, datetime

class DailyStatsCreate(BaseModel):
    date: date
    total_assets: float = 0.0
    total_market_value: float = 0.0
    available_cash: float = 0.0
    daily_profit: float = 0.0
    daily_profit_pct: float = 0.0
    cumulative_profit: float = 0.0

class DailyStatsResponse(BaseModel):
    id: int
    date: date
    total_assets: float
    total_market_value: float
    available_cash: float
    daily_profit: float
    daily_profit_pct: float
    cumulative_profit: float
    created_at: datetime
