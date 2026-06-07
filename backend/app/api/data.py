"""数据备份与导出"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
import csv, io, json, logging
from datetime import datetime
from app.api.portfolio import _fetch_current_price

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])

@router.get("/export")
async def export_all_data(db: AsyncSession = Depends(get_db)):
    """导出所有数据为 JSON（备份用）"""
    from app.models.position import Position
    from app.models.symbol import Symbol
    from app.models.trade import Trade
    from app.models.watchlist import WatchlistItem
    from app.models.alert import Alert

    export = {"exported_at": datetime.now().isoformat(), "tables": {}}

    # symbols
    result = await db.execute(select(Symbol))
    symbols = result.scalars().all()
    export["tables"]["symbols"] = [
        {"id": s.id, "code": s.code, "name": s.name, "market": s.market.value if s.market else "", "type": s.type.value if s.type else ""}
        for s in symbols
    ]

    # positions
    result = await db.execute(select(Position))
    positions = result.scalars().all()
    export["tables"]["positions"] = [
        {"id": p.id, "symbol_id": p.symbol_id, "quantity": p.quantity, "cost_price": p.cost_price, "created_at": str(p.created_at)}
        for p in positions
    ]

    # trades
    result = await db.execute(select(Trade))
    trades = result.scalars().all()
    export["tables"]["trades"] = [
        {"id": t.id, "symbol_id": t.symbol_id, "trade_type": t.trade_type, "quantity": t.quantity,
         "price": t.price, "fee": t.fee, "trade_date": t.trade_date, "note": t.note, "created_at": str(t.created_at)}
        for t in trades
    ]

    # watchlist
    result = await db.execute(select(WatchlistItem))
    watchlist = result.scalars().all()
    export["tables"]["watchlist"] = [
        {"id": w.id, "symbol_id": w.symbol_id, "sort_order": w.sort_order}
        for w in watchlist
    ]

    # alerts
    result = await db.execute(select(Alert))
    alerts = result.scalars().all()
    export["tables"]["alerts"] = [
        {"id": a.id, "symbol_id": a.symbol_id, "condition": a.condition, "threshold": a.threshold, "enabled": a.enabled}
        for a in alerts
    ]

    json_str = json.dumps(export, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=quant_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
    )

@router.get("/db-info")
async def db_info(db: AsyncSession = Depends(get_db)):
    """数据库统计信息"""
    from app.models.position import Position
    from app.models.symbol import Symbol
    from app.models.trade import Trade
    from app.models.watchlist import WatchlistItem
    from app.models.alert import Alert

    models = {"symbols": Symbol, "positions": Position, "trades": Trade, "watchlist": WatchlistItem, "alerts": Alert}
    info = {}
    for name, model in models.items():
        result = await db.execute(select(model))
        info[name] = len(result.scalars().all())

    import os
    db_path = "quant_dashboard.db"
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    return {"row_counts": info, "db_size_bytes": db_size, "db_size_mb": round(db_size / 1024 / 1024, 2)}

@router.get("/export/trades/csv")
async def export_trades_csv(db: AsyncSession = Depends(get_db)):
    """导出交易记录为 CSV"""
    from app.models.trade import Trade
    from app.models.symbol import Symbol

    result = await db.execute(select(Trade).order_by(Trade.trade_date.desc()))
    trades = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "股票代码", "股票名称", "方向", "数量", "价格", "手续费", "金额", "日期", "备注", "创建时间"])

    for t in trades:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == t.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        writer.writerow([
            t.id,
            symbol.code if symbol else "",
            symbol.name if symbol else "",
            "买入" if t.trade_type == "buy" else "卖出",
            t.quantity,
            t.price,
            t.fee,
            round(t.quantity * t.price, 2),
            t.trade_date,
            t.note or "",
            t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=trades_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/export/positions/csv")
async def export_positions_csv(db: AsyncSession = Depends(get_db)):
    """导出持仓为 CSV"""
    from app.models.position import Position
    from app.models.symbol import Symbol

    result = await db.execute(select(Position).order_by(Position.created_at.desc()))
    positions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "股票代码", "股票名称", "数量", "成本价", "现价", "市值", "盈亏", "盈亏%"])

    for p in positions:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        code = symbol.code if symbol else ""
        current_price = await _fetch_current_price(code) if code else None
        market_value = round(current_price * p.quantity, 2) if current_price else None
        pl = round((current_price - p.cost_price) * p.quantity, 2) if current_price else None
        pl_pct = round((current_price - p.cost_price) / p.cost_price * 100, 2) if current_price and p.cost_price > 0 else None

        writer.writerow([
            p.id,
            code,
            symbol.name if symbol else "",
            p.quantity,
            p.cost_price,
            current_price if current_price else "",
            market_value if market_value else "",
            pl if pl is not None else "",
            pl_pct if pl_pct is not None else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=positions_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/cache-stats")
async def cache_stats():
    """缓存统计信息"""
    from app.core.cache import stats as cache_stats_func
    return cache_stats_func()

@router.post("/cache-clear")
async def cache_clear():
    """清空所有缓存"""
    from app.core.cache import clear
    clear()
    return {"ok": True, "message": "缓存已清空"}
