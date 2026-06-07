"""AI自动复盘 - Schemas"""
from pydantic import BaseModel


class DailyReview(BaseModel):
    date: str
    content: str
    market_summary: str
    hot_sectors: list[str]
    risk_alert: str


class StockReview(BaseModel):
    code: str
    name: str
    content: str
    technical_view: str
    fundamental_view: str
    overall_rating: str  # 强烈推荐/推荐/中性/回避


class WeeklyReview(BaseModel):
    week_range: str
    content: str
    weekly_return: float
    key_events: list[str]
