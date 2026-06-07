from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.trade import Trade
from app.models.symbol import Symbol
from app.schemas.trade import TradeCreate, TradeUpdate, TradeResponse, TradeSummary
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trade")

@router.get("", response_model=list[TradeResponse])
async def list_trades(
    symbol_code: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Trade).order_by(desc(Trade.trade_date), desc(Trade.created_at))
    if symbol_code:
        sym_result = await db.execute(select(Symbol).where(Symbol.code == symbol_code))
        symbol = sym_result.scalar_one_or_none()
        if symbol:
            query = query.where(Trade.symbol_id == symbol.id)
        else:
            return []
    query = query.limit(limit)
    result = await db.execute(query)
    trades = result.scalars().all()
    resp = []
    for t in trades:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == t.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        resp.append(TradeResponse(
            id=t.id, symbol_code=symbol.code if symbol else "", symbol_name=symbol.name if symbol else "",
            trade_type=t.trade_type, quantity=t.quantity, price=t.price, fee=t.fee,
            amount=round(t.quantity * t.price, 2), trade_date=t.trade_date, note=t.note, created_at=t.created_at,
        ))
    return resp

@router.post("", response_model=TradeResponse, status_code=201)
async def create_trade(data: TradeCreate, db: AsyncSession = Depends(get_db)):
    # 查找或创建 symbol
    result = await db.execute(select(Symbol).where(Symbol.code == data.symbol_code))
    symbol = result.scalar_one_or_none()
    if not symbol:
        from app.models.symbol import Market, SymbolType
        symbol = Symbol(code=data.symbol_code, name=data.symbol_code, market=Market.SH if data.symbol_code.startswith(("6","9")) else Market.SZ, type=SymbolType.STOCK)
        db.add(symbol)
        await db.flush()
    trade = Trade(
        symbol_id=symbol.id, trade_type=data.trade_type,
        quantity=data.quantity, price=data.price, fee=data.fee,
        trade_date=data.trade_date, note=data.note,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return TradeResponse(
        id=trade.id, symbol_code=symbol.code, symbol_name=symbol.name,
        trade_type=trade.trade_type, quantity=trade.quantity, price=trade.price,
        fee=trade.fee, amount=round(trade.quantity * trade.price, 2),
        trade_date=trade.trade_date, note=trade.note, created_at=trade.created_at,
    )

@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(trade_id: int, data: TradeUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")
    for field in ["trade_type", "quantity", "price", "fee", "trade_date", "note"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(trade, field, val)
    await db.commit()
    await db.refresh(trade)
    sym_result = await db.execute(select(Symbol).where(Symbol.id == trade.symbol_id))
    symbol = sym_result.scalar_one()
    return TradeResponse(
        id=trade.id, symbol_code=symbol.code, symbol_name=symbol.name,
        trade_type=trade.trade_type, quantity=trade.quantity, price=trade.price,
        fee=trade.fee, amount=round(trade.quantity * trade.price, 2),
        trade_date=trade.trade_date, note=trade.note, created_at=trade.created_at,
    )

@router.delete("/{trade_id}", status_code=204)
async def delete_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")
    await db.delete(trade)
    await db.commit()

@router.get("/summary", response_model=TradeSummary)
async def trade_summary(symbol_code: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Trade)
    if symbol_code:
        sym_result = await db.execute(select(Symbol).where(Symbol.code == symbol_code))
        symbol = sym_result.scalar_one_or_none()
        if symbol:
            query = query.where(Trade.symbol_id == symbol.id)
        else:
            return TradeSummary(total_buy_amount=0, total_sell_amount=0, net_flow=0, trade_count=0, realized_pl=0)
    result = await db.execute(query)
    trades = result.scalars().all()
    total_buy = sum(t.quantity * t.price for t in trades if t.trade_type == "buy")
    total_sell = sum(t.quantity * t.price for t in trades if t.trade_type == "sell")
    # 简化已实现盈亏：卖出总额 - 对应买入成本（按均价估算）
    buy_trades = [t for t in trades if t.trade_type == "buy"]
    sell_trades = [t for t in trades if t.trade_type == "sell"]
    avg_buy_price = sum(t.price for t in buy_trades) / len(buy_trades) if buy_trades else 0
    realized_pl = sum((t.price - avg_buy_price) * t.quantity for t in sell_trades) if avg_buy_price > 0 else 0
    return TradeSummary(
        total_buy_amount=round(total_buy, 2),
        total_sell_amount=round(total_sell, 2),
        net_flow=round(total_buy - total_sell, 2),
        trade_count=len(trades),
        realized_pl=round(realized_pl, 2),
    )
