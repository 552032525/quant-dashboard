from fastapi import APIRouter, HTTPException
from app.schemas.risk import RiskResult, MarketRiskSummary, PortfolioRiskCheck
from app.services.risk_service import get_risk_service

router = APIRouter(prefix="/risk")
_service = get_risk_service()


@router.get("/stock/{code}", response_model=RiskResult)
async def check_stock_risk(code: str):
    try:
        data = _service.check_stock_risk(code)
        return RiskResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market", response_model=MarketRiskSummary)
async def get_market_risk():
    try:
        data = _service.get_market_risk()
        return MarketRiskSummary(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio", response_model=list[PortfolioRiskCheck])
async def check_portfolio_risks(body: dict):
    try:
        positions = body.get("positions", [])
        results = _service.check_portfolio_risks(positions)
        return [PortfolioRiskCheck(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
