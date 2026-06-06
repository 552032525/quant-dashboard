from fastapi import APIRouter, HTTPException, Query
from datetime import date, timedelta
from app.adapters import get_adapter
from app.schemas.market import KLineItem, RealtimeQuote, SymbolInfo

router = APIRouter(prefix="/market")

@router.get("/realtime/{code}", response_model=RealtimeQuote)
async def get_realtime(code: str):
    try:
        data = await get_adapter().get_realtime_quote(code)
        return RealtimeQuote(**data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/kline/{code}", response_model=list[KLineItem])
async def get_kline(
    code: str,
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=365)),
    end_date: date = Query(default_factory=date.today),
    period: str = "daily",
):
    try:
        data = await get_adapter().get_kline(code, start_date, end_date, period)
        return [KLineItem(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=list[SymbolInfo])
async def search_symbol(keyword: str = Query(..., min_length=1)):
    try:
        data = await get_adapter().search_symbol(keyword)
        return [
            SymbolInfo(**item, market="SH" if item["code"].startswith("6") else "SZ", type="stock")
            for item in data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
