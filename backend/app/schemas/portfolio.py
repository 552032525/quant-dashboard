from pydantic import BaseModel
from datetime import datetime

class PositionCreate(BaseModel):
    symbol_code: str
    quantity: int
    cost_price: float

class PositionUpdate(BaseModel):
    quantity: int | None = None
    cost_price: float | None = None

class PositionResponse(BaseModel):
    id: int
    symbol_code: str
    symbol_name: str
    quantity: int
    cost_price: float
    current_price: float | None = None
    market_value: float | None = None
    profit_loss: float | None = None
    profit_loss_pct: float | None = None
    created_at: datetime

class PortfolioSummary(BaseModel):
    total_assets: float
    total_market_value: float
    available_cash: float
    total_profit_loss: float
    total_profit_loss_pct: float
