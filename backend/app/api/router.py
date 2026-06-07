from fastapi import APIRouter
from app.api.market import router as market_router
from app.api.portfolio import router as portfolio_router
from app.api.ai import router as ai_router
from app.api.fundamental import router as fundamental_router
from app.api.technical import router as technical_router
from app.api.fundflow import router as fundflow_router
from app.api.sentiment import router as sentiment_router
from app.api.stockpick import router as stockpick_router
from app.api.risk import router as risk_router
from app.api.rebalance import router as rebalance_router
from app.api.review import router as review_router
from app.api.monitor import router as monitor_router
from app.api.trade import router as trade_router
from app.api.data import router as data_router
from app.api.stats import router as stats_router
from app.api.behavior import router as behavior_router

api_router = APIRouter(prefix="/api")
api_router.include_router(market_router, tags=["market"])
api_router.include_router(portfolio_router, tags=["portfolio"])
api_router.include_router(ai_router, tags=["ai"])
api_router.include_router(fundamental_router, tags=["fundamental"])
api_router.include_router(technical_router, tags=["technical"])
api_router.include_router(fundflow_router, tags=["fundflow"])
api_router.include_router(sentiment_router, tags=["sentiment"])
api_router.include_router(stockpick_router, tags=["stockpick"])
api_router.include_router(risk_router, tags=["risk"])
api_router.include_router(rebalance_router, tags=["rebalance"])
api_router.include_router(review_router, tags=["review"])
api_router.include_router(monitor_router, tags=["monitor"])
api_router.include_router(trade_router, tags=["trade"])
api_router.include_router(data_router, tags=["data"])
api_router.include_router(stats_router, tags=["stats"])
api_router.include_router(behavior_router, tags=["behavior"])

# v1 路由（指向相同的 router 模块，建议新功能使用）
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(market_router, tags=["market"])
api_v1_router.include_router(portfolio_router, tags=["portfolio"])
api_v1_router.include_router(ai_router, tags=["ai"])
api_v1_router.include_router(fundamental_router, tags=["fundamental"])
api_v1_router.include_router(technical_router, tags=["technical"])
api_v1_router.include_router(fundflow_router, tags=["fundflow"])
api_v1_router.include_router(sentiment_router, tags=["sentiment"])
api_v1_router.include_router(stockpick_router, tags=["stockpick"])
api_v1_router.include_router(risk_router, tags=["risk"])
api_v1_router.include_router(rebalance_router, tags=["rebalance"])
api_v1_router.include_router(review_router, tags=["review"])
api_v1_router.include_router(monitor_router, tags=["monitor"])
api_v1_router.include_router(trade_router, tags=["trade"])
api_v1_router.include_router(data_router, tags=["data"])
api_v1_router.include_router(stats_router, tags=["stats"])
api_v1_router.include_router(behavior_router, tags=["behavior"])
