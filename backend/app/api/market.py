from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from datetime import date, datetime, timedelta
import json, logging, asyncio
from app.adapters import get_adapter
from app.schemas.market import KLineItem, RealtimeQuote, SymbolInfo, IndexQuote, MarketHeat, SectorInfo, RankingItem, IntradayPoint
from app.core.sina_utils import _sina_raw_parts

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
    try:
        parts = _sina_raw_parts(code)
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


# ── 市场广度 ───────────────────────────────────────────────
@router.get("/breadth")
async def get_market_breadth():
    """获取市场广度：涨跌家数、涨停跌停数"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return {"up_count": 0, "down_count": 0, "flat_count": 0, "limit_up": 0, "limit_down": 0, "total_volume": 0, "up_volume": 0, "ratio": 0}
        up_count = len(df[df["涨跌幅"] > 0])
        down_count = len(df[df["涨跌幅"] < 0])
        flat_count = len(df[df["涨跌幅"] == 0])
        limit_up = len(df[df["涨跌幅"] >= 9.9])
        limit_down = len(df[df["涨跌幅"] <= -9.9])
        total_volume = df["成交额"].sum() / 1e8
        up_volume = df[df["涨跌幅"] > 0]["成交额"].sum() / 1e8
        return {
            "up_count": int(up_count),
            "down_count": int(down_count),
            "flat_count": int(flat_count),
            "limit_up": int(limit_up),
            "limit_down": int(limit_down),
            "total_volume": round(total_volume, 2),
            "up_volume": round(up_volume, 2),
            "ratio": round(up_count / max(up_count + down_count, 1) * 100, 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 指数历史走势 ────────────────────────────────────────────
@router.get("/index-history")
async def get_index_history(days: int = 30):
    """获取三大指数近期走势"""
    try:
        import akshare as ak
        end = date.today().strftime("%Y%m%d")
        start = (date.today() - timedelta(days=days)).strftime("%Y%m%d")
        indices = [
            ("000001", "上证指数"),
            ("399001", "深证成指"),
            ("399006", "创业板指"),
        ]
        result = {}
        for code, name in indices:
            try:
                df = ak.stock_zh_index_daily(symbol="sh" + code if code.startswith("0") else "sz" + code)
                if df is not None and len(df) > 0:
                    df = df.tail(days)
                    result[code] = {
                        "name": name,
                        "data": [{"date": str(row["date"])[:10], "close": float(row["close"]), "volume": float(row["volume"])} for _, row in df.iterrows()],
                    }
            except Exception:
                pass
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
