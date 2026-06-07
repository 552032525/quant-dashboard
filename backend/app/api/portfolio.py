from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.position import Position
from app.models.symbol import Symbol
from app.adapters import get_adapter
from app.schemas.portfolio import PositionCreate, PositionUpdate, PositionResponse, PortfolioSummary
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio")

async def _fetch_current_price(code: str) -> float | None:
    """尝试获取实时价格，失败返回 None"""
    try:
        adapter = get_adapter()
        quote = await adapter.get_realtime_quote(code)
        return float(quote.get("price", 0))
    except Exception as e:
        logger.warning(f"获取 {code} 实时价格失败: {e}")
        return None

@router.get("", response_model=list[PositionResponse])
async def list_positions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).order_by(Position.created_at.desc()))
    positions = result.scalars().all()
    resp = []
    for p in positions:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        code = symbol.code if symbol else ""
        current_price = await _fetch_current_price(code) if code else None
        market_value = current_price * p.quantity if current_price else None
        pl = (current_price - p.cost_price) * p.quantity if current_price else None
        pl_pct = round((current_price - p.cost_price) / p.cost_price * 100, 2) if current_price and p.cost_price > 0 else None
        resp.append(
            PositionResponse(
                id=p.id,
                symbol_code=code,
                symbol_name=symbol.name if symbol else "",
                quantity=p.quantity,
                cost_price=p.cost_price,
                current_price=current_price,
                market_value=market_value,
                profit_loss=pl,
                profit_loss_pct=pl_pct,
                created_at=p.created_at,
            )
        )
    return resp

@router.post("", response_model=PositionResponse, status_code=201)
async def create_position(data: PositionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Symbol).where(Symbol.code == data.symbol_code))
    symbol = result.scalar_one_or_none()
    if not symbol:
        raise HTTPException(status_code=404, detail=f"未找到股票: {data.symbol_code}")
    position = Position(symbol_id=symbol.id, quantity=data.quantity, cost_price=data.cost_price)
    db.add(position)
    await db.commit()
    await db.refresh(position)
    current_price = await _fetch_current_price(symbol.code)
    market_value = current_price * position.quantity if current_price else None
    pl = (current_price - position.cost_price) * position.quantity if current_price else None
    pl_pct = round((current_price - position.cost_price) / position.cost_price * 100, 2) if current_price and position.cost_price > 0 else None
    return PositionResponse(
        id=position.id,
        symbol_code=symbol.code,
        symbol_name=symbol.name,
        quantity=position.quantity,
        cost_price=position.cost_price,
        current_price=current_price,
        market_value=market_value,
        profit_loss=pl,
        profit_loss_pct=pl_pct,
        created_at=position.created_at,
    )

@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(position_id: int, data: PositionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="持仓记录不存在")
    if data.quantity is not None:
        position.quantity = data.quantity
    if data.cost_price is not None:
        position.cost_price = data.cost_price
    await db.commit()
    await db.refresh(position)
    sym_result = await db.execute(select(Symbol).where(Symbol.id == position.symbol_id))
    symbol = sym_result.scalar_one()
    current_price = await _fetch_current_price(symbol.code)
    market_value = current_price * position.quantity if current_price else None
    pl = (current_price - position.cost_price) * position.quantity if current_price else None
    pl_pct = round((current_price - position.cost_price) / position.cost_price * 100, 2) if current_price and position.cost_price > 0 else None
    return PositionResponse(
        id=position.id,
        symbol_code=symbol.code,
        symbol_name=symbol.name,
        quantity=position.quantity,
        cost_price=position.cost_price,
        current_price=current_price,
        market_value=market_value,
        profit_loss=pl,
        profit_loss_pct=pl_pct,
        created_at=position.created_at,
    )

@router.delete("/{position_id}", status_code=204)
async def delete_position(position_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="持仓记录不存在")
    await db.delete(position)
    await db.commit()

@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position))
    positions = result.scalars().all()
    total_cost = 0.0
    total_market_value = 0.0
    for p in positions:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        code = symbol.code if symbol else ""
        current_price = await _fetch_current_price(code) if code else None
        cost = p.quantity * p.cost_price
        total_cost += cost
        if current_price:
            total_market_value += current_price * p.quantity
        else:
            total_market_value += cost  # 获取不到价格时用成本兜底
    total_pl = total_market_value - total_cost
    total_pl_pct = round(total_pl / total_cost * 100, 2) if total_cost > 0 else 0.0
    return PortfolioSummary(
        total_assets=total_market_value,
        total_market_value=total_market_value,
        available_cash=0.0,
        total_profit_loss=round(total_pl, 2),
        total_profit_loss_pct=total_pl_pct,
    )
