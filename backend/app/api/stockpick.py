from fastapi import APIRouter, HTTPException
from app.schemas.stockpick import (
    FactorFilter, ScreenResult, BacktestParam, BacktestResult, StrategyInfo, StockCandidate,
    CompareRequest, StrategyResult, CompareResult,
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



@router.post("/compare", response_model=CompareResult)
async def compare_strategies(params: CompareRequest):
    """多策略对比回测"""
    try:
        results = []
        strategy_map = {s["key"]: s["name"] for s in _service.get_strategies()}
        for strategy in params.strategies:
            bt_params = {
                "code": params.code,
                "strategy": strategy,
                "start_date": params.start_date,
                "end_date": params.end_date,
            }
            bt_result = _service.run_backtest(bt_params)
            results.append(StrategyResult(
                strategy=strategy,
                strategy_name=strategy_map.get(strategy, strategy),
                total_return=bt_result["total_return"],
                annual_return=bt_result["annual_return"],
                max_drawdown=bt_result["max_drawdown"],
                sharpe=bt_result["sharpe"],
                win_rate=bt_result["win_rate"],
                trade_count=bt_result["trade_count"],
                nav_curve=bt_result["nav_curve"],
            ))
        return CompareResult(
            code=params.code,
            name=bt_result.get("name", "") if results else "",
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

