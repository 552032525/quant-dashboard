"""NLP舆情资讯 - Schemas"""
from pydantic import BaseModel
from typing import Optional


class NewsItem(BaseModel):
    title: str
    summary: str = ""
    source: str = ""
    time: str = ""
    url: str = ""
    sentiment: Optional[float] = None  # -1到1，负为空，正为多


class NewsResult(BaseModel):
    code: str
    name: str
    items: list[NewsItem]


class MarketNewsResult(BaseModel):
    hot_topics: list[NewsItem]
    breaking_news: list[NewsItem]


class SentimentScore(BaseModel):
    code: str
    name: str
    overall: float  # -1到1总情感
    positive_count: int
    negative_count: int
    neutral_count: int
    key_topics: list[str]


class ResearchSummary(BaseModel):
    code: str
    name: str
    content: str
    key_points: list[str]
    rating: str = ""  # 买入/增持/持有/减持/卖出


class SummaryRequest(BaseModel):
    code: str
    content: str = ""  # 可选：用户提供的研报内容
