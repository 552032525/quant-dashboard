from fastapi import APIRouter, HTTPException
from app.schemas.stockpick import (
    FactorFilter, ScreenResult, BacktestParam, BacktestResult, StrategyInfo, StockCandidate,
)
from app.services.stockpick_service import get_stockpick_service

router = APIRouter(prefix="/stockpick")
_service = get_stockpick_service()


@router.post("/screen", response_model=ScreenResult)
async def screen_stocks(filters: FactorFilter):
    try:
        candidates = _service.screen_stocks(filters.model_dump())
        return ScreenResult(
            candidates=[StockCandidate(**c) for c in candidates],
            total_count=len(candidates),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(params: BacktestParam):
    try:
        result = _service.run_backtest(params.model_dump())
        return BacktestResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies", response_model=list[StrategyInfo])
async def list_strategies():
    try:
        return [StrategyInfo(**s) for s in _service.get_strategies()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
