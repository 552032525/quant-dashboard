from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.models.trade import Trade
from app.models.symbol import Symbol
from app.schemas.behavior import BehaviorAnalysis, BehaviorSummary, TradeBehaviorItem

router = APIRouter(prefix="/behavior", tags=["behavior"])


@router.get("/analysis", response_model=BehaviorAnalysis)
async def analyze_behavior(
    symbol_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Trade, Symbol).join(Symbol, Trade.symbol_id == Symbol.id)
    if symbol_code:
        query = query.where(Symbol.code == symbol_code)
    query = query.order_by(Trade.trade_date.asc())

    result = await db.execute(query)
    rows = result.all()

    stock_data: dict[int, dict] = {}
    for trade, symbol in rows:
        sid = trade.symbol_id
        if sid not in stock_data:
            stock_data[sid] = {"code": symbol.code, "name": symbol.name, "trades": []}
        stock_data[sid]["trades"].append(trade)

    items: list[TradeBehaviorItem] = []
    for sid, data in stock_data.items():
        trades = data["trades"]
        buys = [t for t in trades if t.trade_type == "buy"]
        sells = [t for t in trades if t.trade_type == "sell"]

        total_buy = sum(t.price * t.quantity for t in buys)
        total_sell = sum(t.price * t.quantity for t in sells)
        trade_count = len(trades)

        dates = [
            datetime.strptime(t.trade_date, "%Y-%m-%d")
            for t in trades
            if t.trade_date
        ]
        avg_hold_days = 0.0
        if len(dates) >= 2 and buys:
            avg_hold_days = (max(dates) - min(dates)).days / max(len(buys), 1)

        buy_qty = sum(t.quantity for t in buys)
        sell_qty = sum(t.quantity for t in sells)
        matched_qty = min(buy_qty, sell_qty)
        avg_buy_price = (
            sum(t.price * t.quantity for t in buys) / max(buy_qty, 1)
            if buy_qty > 0
            else 0
        )
        avg_sell_price = (
            sum(t.price * t.quantity for t in sells) / max(sell_qty, 1)
            if sell_qty > 0
            else 0
        )
        total_profit = (
            (avg_sell_price - avg_buy_price) * matched_qty
            if matched_qty > 0
            else 0.0
        )
        profit_pct = (total_profit / total_buy * 100) if total_buy > 0 else 0.0

        win_count = sum(1 for t in sells if t.price > avg_buy_price)
        loss_count = len(sells) - win_count
        win_rate = (
            round(win_count / max(len(sells), 1) * 100, 1) if sells else 0.0
        )

        items.append(
            TradeBehaviorItem(
                code=data["code"],
                name=data["name"],
                total_buy=round(total_buy, 2),
                total_sell=round(total_sell, 2),
                trade_count=trade_count,
                avg_hold_days=round(avg_hold_days, 1),
                total_profit=round(total_profit, 2),
                profit_pct=round(profit_pct, 2),
                win_count=win_count,
                loss_count=loss_count,
                win_rate=win_rate,
            )
        )

    total_trades = sum(i.trade_count for i in items)
    total_buy_amount = sum(i.total_buy for i in items)
    total_sell_amount = sum(i.total_sell for i in items)
    total_profit = sum(i.total_profit for i in items)
    total_profit_pct = (
        round(total_profit / total_buy_amount * 100, 2)
        if total_buy_amount > 0
        else 0.0
    )
    win_sum = sum(i.win_count for i in items)
    loss_sum = sum(i.loss_count for i in items)
    overall_win_rate = (
        round(win_sum / max(win_sum + loss_sum, 1) * 100, 1)
        if (win_sum + loss_sum) > 0
        else 0.0
    )
    avg_hold_days = (
        round(sum(i.avg_hold_days for i in items) / max(len(items), 1), 1)
    )

    best = max(items, key=lambda x: x.total_profit) if items else None
    worst = min(items, key=lambda x: x.total_profit) if items else None

    summary = BehaviorSummary(
        total_trades=total_trades,
        total_buy_amount=total_buy_amount,
        total_sell_amount=total_sell_amount,
        total_profit=total_profit,
        total_profit_pct=total_profit_pct,
        overall_win_rate=overall_win_rate,
        avg_hold_days=avg_hold_days,
        best_stock=best,
        worst_stock=worst,
    )

    return BehaviorAnalysis(summary=summary, stocks=items)
