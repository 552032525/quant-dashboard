from pydantic import BaseModel
from typing import Optional

class StockFlowItem(BaseModel):
    date: str
    main_net: float       # 主力净流入(万元)
    super_large_net: float # 超大单净流入
    large_net: float       # 大单净流入
    mid_net: float         # 中单净流入
    small_net: float       # 小单净流入

class StockFlowResult(BaseModel):
    code: str
    name: str
    flows: list[StockFlowItem]

class NorthBoundItem(BaseModel):
    date: str
    sh_net: float      # 沪股通净买入(亿元)
    sz_net: float      # 深股通净买入(亿元)
    total_net: float   # 合计净买入

class NorthBoundResult(BaseModel):
    items: list[NorthBoundItem]

class NorthBoundDaily(BaseModel):
    date: str
    sh_net: float
    sz_net: float
    total_net: float
    sh_balance: float  # 沪股通余额
    sz_balance: float  # 深股通余额

class SectorFlowItem(BaseModel):
    name: str
    net_amount: float    # 净流入(万元)
    main_net: float      # 主力净流入
    change_pct: float    # 板块涨跌幅

class SectorFlowResult(BaseModel):
    inflow_top10: list[SectorFlowItem]
    outflow_top10: list[SectorFlowItem]

class MarketFlowSummary(BaseModel):
    date: str
    main_net: float      # 主力净流入(亿元)
    total_turnover: float # 总成交额(亿元)
    up_count: int
    down_count: int

class AIReport(BaseModel):
    code: str
    name: str
    content: str
    summary: str

class ReportRequest(BaseModel):
    code: str
