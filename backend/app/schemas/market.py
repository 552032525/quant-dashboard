from pydantic import BaseModel
from datetime import date

class KLineItem(BaseModel):
    date: date
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
