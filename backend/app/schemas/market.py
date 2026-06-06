from pydantic import BaseModel

class KLineItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class RealtimeQuote(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: float
    high: float
    low: float
    open: float
    pre_close: float

class SymbolInfo(BaseModel):
    code: str
    name: str
    market: str
    type: str

class IndexQuote(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_pct: float

class MarketHeat(BaseModel):
    up_count: int
    down_count: int
    flat_count: int
    limit_up: int
    limit_down: int
    total_volume: float
    north_flow: float

class SectorInfo(BaseModel):
    name: str
    change_pct: float
    lead_stock: str
    stock_count: int

class RankingItem(BaseModel):
    code: str
    name: str
    price: float
    change_pct: float

class IntradayPoint(BaseModel):
    time: str
    price: float
    avg_price: float
    volume: float
