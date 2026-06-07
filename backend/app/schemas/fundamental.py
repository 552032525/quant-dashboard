from pydantic import BaseModel

class FinancialItem(BaseModel):
    date: str
    revenue: float
    net_profit: float
    cash_flow: float

class FinancialOverview(BaseModel):
    code: str
    name: str
    data: list[FinancialItem]

class ValuationData(BaseModel):
    code: str
    name: str
    pe: float
    pb: float
    ps: float
    roe: float
    dividend_yield: float
    industry_pe: float

class RiskScreening(BaseModel):
    code: str
    name: str
    debt_ratio: float
    pledge_ratio: float
    cash_flow_health: str
    goodwill_ratio: float
    risk_level: str
    risk_items: list[str]

class HolderItem(BaseModel):
    name: str
    ratio: float
    change: str

class HolderData(BaseModel):
    code: str
    name: str
    top_holders: list[HolderItem]
    institution_change: str

class AIReport(BaseModel):
    code: str
    name: str
    content: str
    summary: str

class AIResponse(BaseModel):
    content: str

class CompareRequest(BaseModel):
    codes: list[str]
    indicators: list[str] = ["revenue_growth", "roe", "pe", "debt_ratio"]

class CompareResult(BaseModel):
    table: list[dict]
    ai_comment: str
