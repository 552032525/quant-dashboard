"""AI智能选股&策略回测 - Schemas"""
from pydantic import BaseModel
from typing import Optional


class FactorFilter(BaseModel):
    pe_max: float = 100
    pe_min: float = 0
    pb_max: float = 20
    pb_min: float = 0
    roe_min: float = 0
    market_cap_min: float = 0  # 亿元
    market_cap_max: float = 10000
    revenue_growth_min: float = 0
    debt_ratio_max: float = 90
    industry: str = ""
    mode: str = "simple"


class StockCandidate(BaseModel):
    code: str
    name: str
    pe: float
    pb: float
    roe: float
    market_cap: float
    score: int


class ScreenResult(BaseModel):
    candidates: list[StockCandidate]
    total_count: int


class BacktestParam(BaseModel):
    code: str
    strategy: str = "ma_cross"  # ma_cross, momentum, grid, mean_reversion
    start_date: str = "2025-01-01"
    end_date: str = "2026-01-01"
    # MA 交叉参数
    ma_short: int = 5
    ma_long: int = 20
    # 动量参数
    momentum_days: int = 20
    # 网格参数
    grid_count: int = 10
    # 均值回归参数
    boll_period: int = 20


class TradeRecord(BaseModel):
    date: str
    action: str  # buy/sell
    price: float
    shares: int
    profit: float = 0


class BacktestResult(BaseModel):
    code: str
    name: str
    strategy: str
    total_return: float  # 总收益率%
    annual_return: float  # 年化收益率%
    max_drawdown: float  # 最大回撤%
    sharpe: float  # 夏普比率
    win_rate: float  # 胜率%
    trade_count: int
    trades: list[TradeRecord]
    nav_curve: list[dict]  # 净值曲线


class StrategyInfo(BaseModel):
    key: str
    name: str
    description: str
    params: list[dict]



# ========== 策略对比 ==========
class CompareRequest(BaseModel):
    code: str
    strategies: list[str] = ["ma_cross", "momentum", "mean_reversion"]
    start_date: str = "2025-01-01"
    end_date: str = "2026-06-08"


class StrategyResult(BaseModel):
    strategy: str
    strategy_name: str
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    trade_count: int
    nav_curve: list[dict]


class CompareResult(BaseModel):
    code: str
    name: str
    results: list[StrategyResult]
