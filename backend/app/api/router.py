from fastapi import APIRouter
from app.api.market import router as market_router
from app.api.portfolio import router as portfolio_router
from app.api.ai import router as ai_router

api_router = APIRouter(prefix="/api")
api_router.include_router(market_router, tags=["market"])
api_router.include_router(portfolio_router, tags=["portfolio"])
api_router.include_router(ai_router, tags=["ai"])
