from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TradeCreate(BaseModel):
    symbol_code: str
    trade_type: str  # buy / sell
    quantity: int
    price: float
    fee: float = 0.0
    trade_date: str  # YYYY-MM-DD
    note: str = ""


class TradeUpdate(BaseModel):
    trade_type: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    fee: Optional[float] = None
    trade_date: Optional[str] = None
    note: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    symbol_code: str
    symbol_name: str
    trade_type: str
    quantity: int
    price: float
    fee: float
    amount: float  # quantity * price
    trade_date: str
    note: str
    created_at: datetime


class TradeSummary(BaseModel):
    total_buy_amount: float
    total_sell_amount: float
    net_flow: float  # 买入 - 卖出（正=净买入）
    trade_count: int
    realized_pl: float  # 已实现盈亏
