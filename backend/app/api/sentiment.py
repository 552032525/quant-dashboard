from fastapi import APIRouter, HTTPException
from app.schemas.sentiment import (
    NewsResult, MarketNewsResult, SentimentScore, ResearchSummary, SummaryRequest,
)
from app.services.sentiment_service import get_sentiment_service

router = APIRouter(prefix="/sentiment")
_service = get_sentiment_service()


@router.get("/news/{code}", response_model=NewsResult)
async def get_stock_news(code: str):
    try:
        data = _service.get_stock_news(code)
        return NewsResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-news", response_model=MarketNewsResult)
async def get_market_news():
    try:
        data = _service.get_market_news()
        return MarketNewsResult(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/{code}", response_model=SentimentScore)
async def analyze_sentiment(code: str, body: dict = None):
    try:
        news_texts = []
        if body and "texts" in body:
            news_texts = body["texts"]
        else:
            # 先获取新闻再分析
            news_data = _service.get_stock_news(code)
            news_texts = [n["title"] for n in news_data.get("items", []) if n["title"]]

        result = _service.analyze_sentiment(code, news_texts)
        return SentimentScore(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=ResearchSummary)
async def summarize_research(req: SummaryRequest):
    try:
        result = _service.summarize_research(req.code, req.content)
        return ResearchSummary(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
