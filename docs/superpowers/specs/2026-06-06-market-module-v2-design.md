# 实时行情模块 V2 设计文档

> **状态**: 已确认 | **日期**: 2026-06-06 | **版本**: 2.0

## 目标

将行情模块从"单股查询+K线"升级为产品级市场总览仪表盘，覆盖全市场实时行情、多周期K线（含分时/分钟线）、行业/概念板块热力图、市场热度统计四大子功能。

## 当前状态

- `MarketView.vue` — 搜索框 + K线图 + 指标卡，单一股票视角
- `GET /api/market/realtime/{code}` — 单股实时报价
- `GET /api/market/kline/{code}` — 单股K线（日/周/月）
- `GET /api/market/search` — 股票搜索
- 数据源适配器 `AkshareAdapter` / `BaostockAdapter` 仅覆盖上述三个方法

## 目标架构

### 页面结构

```
/ (首页 MarketOverview)          /stock/:code (个股详情 MarketDetail)
┌─────────────────────────┐      ┌─────────────────────────┐
│ 三大指数概览条            │      │ 搜索框 + 股票名 + 实时价   │
│ 上证·深证·创业板 涨跌幅    │      │ 多周期 Tab:              │
├─────────────────────────┤      │ 分时|30分|60分|日|周|月   │
│ 市场热度概览              │ 点击  ├─────────────────────────┤
│ 涨跌比|涨停跌停|成交额|北向 │ ──→  │ K线图 (ECharts)         │
├────────────┬────────────┤      │ + 右侧指标卡              │
│ 板块热力图  │ 涨跌榜 Top20 │      │ + 所属板块联动标签        │
│ 行业↔概念  │ 涨幅↔跌幅   │      └─────────────────────────┘
└────────────┴────────────┘
```

### 后端 API 设计

所有新 API 挂在 `/api/market` 下：

| 端点 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `GET /index` | - | `list[IndexQuote]` | 三大指数（000001/399001/399006）实时行情 |
| `GET /heat` | - | `MarketHeat` | 涨跌家数比、涨停/跌停数、总成交额、北向资金净流入 |
| `GET /sectors` | `type=industry\|concept` | `list[SectorInfo]` | 板块名称、涨跌幅、领涨股、成分股数 |
| `GET /rankings` | `type=up\|down, limit=20` | `list[RankingItem]` | 涨跌排行榜，含代码/名称/最新价/涨跌幅 |
| `GET /kline/{code}` | 增加 `period=1\|5\|15\|30\|60\|daily\|weekly\|monthly` | `list[KLineItem]` | 扩展周期支持，新增分时和分钟K线 |
| `GET /intraday/{code}` | - | `list[IntradayPoint]` | 当日分时数据（时间+价格+均价+成交量） |

**数据模型（schemas/market.py 新增）**：

```python
class IndexQuote(BaseModel):
    code: str; name: str; price: float; change: float; change_pct: float

class MarketHeat(BaseModel):
    up_count: int; down_count: int; flat_count: int
    limit_up: int; limit_down: int
    total_volume: float  # 总成交额（亿）
    north_flow: float    # 北向资金净流入（亿）

class SectorInfo(BaseModel):
    name: str; change_pct: float; lead_stock: str; stock_count: int

class RankingItem(BaseModel):
    code: str; name: str; price: float; change_pct: float

class IntradayPoint(BaseModel):
    time: str; price: float; avg_price: float; volume: float
```

### 适配器扩展

`akshare` 已支持所需全部数据源：

| 方法 | akshare 函数 | 说明 |
|------|-------------|------|
| `get_index_quotes` | `stock_zh_index_spot_em` | 指数实时行情 |
| `get_market_heat` | `stock_zh_a_spot_em`（统计全市场） | 涨跌统计 |
| `get_sectors` | `stock_board_industry_spot_em` / `stock_board_concept_spot_em` | 板块行情 |
| `get_rankings` | `stock_zh_a_spot_em`（排序取前N） | 涨跌排行 |
| `get_intraday` | `stock_zh_a_hist_min_em`（period=1） | 分时数据 |
| `get_kline`（扩展） | `stock_zh_a_hist`（period 扩展映射） | 多周期K线 |

北向资金：`stock_hsgt_north_net_flow_in_em` 取当日累计。

### 前端组件树

```
MarketOverview.vue
├── IndexBar.vue          — 三大指数条，3列横向
├── HeatBar.vue           — 涨跌比·涨停跌停·成交额·北向，4指标横向
├── SectorHeatmap.vue     — ECharts treemap，行业/概念可切换
└── RankingList.vue       — 涨跌榜，涨幅↔跌幅可切换，点击跳详情

MarketDetail.vue          — 改造现有 MarketView
├── 搜索框 + 股票头
├── 周期 Tab 组件
├── KLineChart.vue        — 复用，扩展支持分钟线
├── MetricCard 列表       — 复用
└── 所属板块标签          — 可点击反向查看板块
```

### 路由调整

```typescript
routes: [
  { path: "/", name: "market", component: () => import("../views/MarketOverview.vue") },
  { path: "/stock/:code", name: "stock-detail", component: () => import("../views/MarketDetail.vue") },
  { path: "/portfolio", name: "portfolio", component: () => import("../views/PortfolioView.vue") },
  { path: "/ai", name: "ai", component: () => import("../views/AIChatView.vue") },
]
```

## 不做的

- 不在此阶段做自选股列表（属模块十）
- 不做 WebSocket 实时推送（此阶段轮询即可）
- 不改 baostock 适配器（baostock 不支持板块/分钟数据）
- 不 touch 持仓和 AI 模块

## 数据刷新策略

- 首页各组件：进入页面加载一次，手动刷新按钮
- 详情页：切换到新周期时请求对应数据
- 数据源默认切换为 `akshare`（baostock 不支持板块/分钟线）
