from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from datetime import date, datetime, timedelta
import requests, re, json, logging, asyncio
from app.adapters import get_adapter
from app.schemas.market import KLineItem, RealtimeQuote, SymbolInfo, IndexQuote, MarketHeat, SectorInfo, RankingItem, IntradayPoint

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

@router.get("/index", response_model=list[IndexQuote])
async def get_index():
    try:
        data = await get_adapter().get_index_quotes()
        return [IndexQuote(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/heat", response_model=MarketHeat)
async def get_heat():
    try:
        data = await get_adapter().get_market_heat()
        return MarketHeat(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectors", response_model=list[SectorInfo])
async def get_sectors(type: str = "industry"):
    try:
        data = await get_adapter().get_sectors(type)
        return [SectorInfo(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rankings", response_model=list[RankingItem])
async def get_rankings(type: str = "up", limit: int = 20):
    try:
        data = await get_adapter().get_rankings(type, limit)
        return [RankingItem(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intraday/{code}", response_model=list[IntradayPoint])
async def get_intraday(code: str):
    try:
        data = await get_adapter().get_intraday(code)
        return [IntradayPoint(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ── WebSocket 实时行情推送 ─────────────────────────────────
from fastapi import WebSocket, WebSocketDisconnect
import asyncio, json

@router.websocket("/ws/{code}")
async def websocket_quote(websocket: WebSocket, code: str):
    await websocket.accept()
    logger = logging.getLogger("market.ws")
    logger.info(f"WebSocket 连接: {code}")
    try:
        while True:
            try:
                data = await get_adapter().get_realtime_quote(code)
                await websocket.send_json({
                    "code": code,
                    "price": data.get("price", 0),
                    "change_pct": data.get("change_pct", 0),
                    "volume": data.get("volume", 0),
                    "trading_status": data.get("trading_status", ""),
                    "time": datetime.now().strftime("%H:%M:%S"),
                })
            except Exception as e:
                await websocket.send_json({"error": str(e)})
            await asyncio.sleep(5)  # 5 秒推送一次
    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: {code}")

# ── 五档盘口 ───────────────────────────────────────────────
@router.get("/depth/{code}")
async def get_depth(code: str):
    """获取五档买卖盘口（新浪接口）"""
    prefix = "sh" + code if code.startswith(("6", "9")) else "sz" + code
    try:
        resp = requests.get(f"http://hq.sinajs.cn/list={prefix}", headers={
            "Referer": "https://finance.sina.com.cn"
        }, timeout=5)
        resp.encoding = "gbk"
        m = re.search(r'"([^"]*)"', resp.text)
        if not m:
            return {"code": code, "bids": [], "asks": []}

        parts = m.group(1).split(",")
        if len(parts) < 30:
            return {"code": code, "bids": [], "asks": []}

        # 新浪格式: 买1价,买1量,买2价,买2量,... 卖1价,卖1量,...
        # 买盘: parts[11..20], 卖盘: parts[21..30]
        name = parts[0]
        price = float(parts[3]) if parts[3] else 0

        bids = []
        for i in range(11, 20, 2):
            if i + 1 < len(parts) and parts[i] and parts[i+1]:
                bids.append({"price": float(parts[i]), "volume": int(float(parts[i+1]))})

        asks = []
        for i in range(21, 30, 2):
            if i + 1 < len(parts) and parts[i] and parts[i+1]:
                asks.append({"price": float(parts[i]), "volume": int(float(parts[i+1]))})

        return {
            "code": code, "name": name, "price": price,
            "bids": bids, "asks": asks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取盘口失败: {e}")

