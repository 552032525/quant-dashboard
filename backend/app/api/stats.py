from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.models.daily_stats import DailyStats
from app.models.position import Position
from app.models.symbol import Symbol
from app.adapters import get_adapter
from app.schemas.daily_stats import DailyStatsCreate, DailyStatsResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats")

async def _compute_portfolio_summary(db: AsyncSession) -> dict:
    """计算当前投资组合摘要（总资产、市值、盈亏等）"""
    result = await db.execute(select(Position))
    positions = result.scalars().all()
    total_cost = 0.0
    total_market_value = 0.0
    for p in positions:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        code = symbol.code if symbol else ""
        current_price = None
        if code:
            try:
                adapter = get_adapter()
                quote = await adapter.get_realtime_quote(code)
                current_price = float(quote.get("price", 0))
            except Exception as e:
                logger.warning(f"获取 {code} 实时价格失败: {e}")
        cost = p.quantity * p.cost_price
        total_cost += cost
        if current_price and current_price > 0:
            total_market_value += current_price * p.quantity
        else:
            total_market_value += cost
    total_pl = round(total_market_value - total_cost, 2)
    total_pl_pct = round(total_pl / total_cost * 100, 2) if total_cost > 0 else 0.0
    return {
        "total_assets": round(total_market_value, 2),
        "total_market_value": round(total_market_value, 2),
        "available_cash": 0.0,
        "total_profit_loss": total_pl,
        "total_profit_loss_pct": total_pl_pct,
    }


@router.get("/daily", response_model=list[DailyStatsResponse])
async def list_daily_stats(
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
):
    """查询每日统计列表，按日期降序"""
    stmt = select(DailyStats)
    if start_date:
        stmt = stmt.where(DailyStats.date >= start_date)
    if end_date:
        stmt = stmt.where(DailyStats.date <= end_date)
    stmt = stmt.order_by(desc(DailyStats.date))
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [
        DailyStatsResponse(
            id=r.id,
            date=r.date,
            total_assets=r.total_assets,
            total_market_value=r.total_market_value,
            available_cash=r.available_cash,
            daily_profit=r.daily_profit,
            daily_profit_pct=r.daily_profit_pct,
            cumulative_profit=r.cumulative_profit,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post("/snapshot", response_model=DailyStatsResponse, status_code=201)
async def create_snapshot(db: AsyncSession = Depends(get_db)):
    """手动触发当日快照，从投资组合获取当前数据写入 daily_stats"""
    today = date.today()
    # 检查今日是否已有记录
    existing = await db.execute(
        select(DailyStats).where(DailyStats.date == today)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"今日 ({today}) 已有快照记录")
    # 获取昨日记录用于计算日收益
    yesterday = today - timedelta(days=1)
    yesterday_result = await db.execute(
        select(DailyStats).where(DailyStats.date <= yesterday).order_by(desc(DailyStats.date)).limit(1)
    )
    yesterday_record = yesterday_result.scalar_one_or_none()
    # 计算当前投资组合摘要
    summary = await _compute_portfolio_summary(db)
    # 计算当日收益和累计收益
    if yesterday_record:
        daily_profit = round(summary["total_assets"] - yesterday_record.total_assets, 2)
        daily_profit_pct = round(daily_profit / yesterday_record.total_assets * 100, 2) if yesterday_record.total_assets > 0 else 0.0
        cumulative_profit = round(yesterday_record.cumulative_profit + daily_profit, 2)
    else:
        daily_profit = 0.0
        daily_profit_pct = 0.0
        cumulative_profit = 0.0
    record = DailyStats(
        date=today,
        total_assets=summary["total_assets"],
        total_market_value=summary["total_market_value"],
        available_cash=summary["available_cash"],
        daily_profit=daily_profit,
        daily_profit_pct=daily_profit_pct,
        cumulative_profit=cumulative_profit,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return DailyStatsResponse(
        id=record.id,
        date=record.date,
        total_assets=record.total_assets,
        total_market_value=record.total_market_value,
        available_cash=record.available_cash,
        daily_profit=record.daily_profit,
        daily_profit_pct=record.daily_profit_pct,
        cumulative_profit=record.cumulative_profit,
        created_at=record.created_at,
    )


@router.get("/latest", response_model=DailyStatsResponse)
async def get_latest_stats(db: AsyncSession = Depends(get_db)):
    """获取最近一条统计记录"""
    result = await db.execute(
        select(DailyStats).order_by(desc(DailyStats.date)).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="暂无每日统计记录")
    return DailyStatsResponse(
        id=record.id,
        date=record.date,
        total_assets=record.total_assets,
        total_market_value=record.total_market_value,
        available_cash=record.available_cash,
        daily_profit=record.daily_profit,
        daily_profit_pct=record.daily_profit_pct,
        cumulative_profit=record.cumulative_profit,
        created_at=record.created_at,
    )
