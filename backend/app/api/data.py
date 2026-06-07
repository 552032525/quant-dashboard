"""数据备份与导出"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
from fastapi import Depends
import io, json, logging
from datetime import datetime

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

    # 数据库文件大小
    import os
    db_path = "quant_dashboard.db"
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    return {"row_counts": info, "db_size_bytes": db_size, "db_size_mb": round(db_size / 1024 / 1024, 2)}
