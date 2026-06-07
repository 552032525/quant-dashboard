from pydantic import BaseModel
from typing import Optional

class TradeBehaviorItem(BaseModel):
    code: str
    name: str
    total_buy: float
    total_sell: float
    trade_count: int
    avg_hold_days: float
    total_profit: float
    profit_pct: float
    win_count: int
    loss_count: int
    win_rate: float

class BehaviorSummary(BaseModel):
    total_trades: int
    total_buy_amount: float
    total_sell_amount: float
    total_profit: float
    total_profit_pct: float
    overall_win_rate: float
    avg_hold_days: float
    best_stock: Optional[TradeBehaviorItem] = None
    worst_stock: Optional[TradeBehaviorItem] = None

class BehaviorAnalysis(BaseModel):
    summary: BehaviorSummary
    stocks: list[TradeBehaviorItem]
