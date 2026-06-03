from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.position import Position
from app.models.symbol import Symbol
from app.schemas.portfolio import PositionCreate, PositionUpdate, PositionResponse, PortfolioSummary

router = APIRouter(prefix="/portfolio")

@router.get("", response_model=list[PositionResponse])
async def list_positions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).order_by(Position.created_at.desc()))
    positions = result.scalars().all()
    resp = []
    for p in positions:
        sym_result = await db.execute(select(Symbol).where(Symbol.id == p.symbol_id))
        symbol = sym_result.scalar_one_or_none()
        resp.append(
            PositionResponse(
                id=p.id,
                symbol_code=symbol.code if symbol else "",
                symbol_name=symbol.name if symbol else "",
                quantity=p.quantity,
                cost_price=p.cost_price,
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
    return PositionResponse(
        id=position.id,
        symbol_code=symbol.code,
        symbol_name=symbol.name,
        quantity=position.quantity,
        cost_price=position.cost_price,
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
    return PositionResponse(
        id=position.id,
        symbol_code=symbol.code,
        symbol_name=symbol.name,
        quantity=position.quantity,
        cost_price=position.cost_price,
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
    total_cost = sum(p.quantity * p.cost_price for p in positions)
    return PortfolioSummary(
        total_assets=total_cost,
        total_market_value=total_cost,
        available_cash=0.0,
        total_profit_loss=0.0,
        total_profit_loss_pct=0.0,
    )
