# 模块二：AI 基本面分析 设计文档

> **状态**: 已确认 | **日期**: 2026-06-07 | **版本**: 1.0

## 目标

实现产品清单中模块二的全部核心功能：财报AI解析、自动估值、财务风险筛查、机构持仓跟踪、政策利好匹配。按核心链路优先策略，首期打通财报解析+估值+风险筛查。

## 当前状态

- AI 模块已有基础：`POST /api/ai/analyze`（技术面分析）、`POST /api/ai/chat`（通用对话）
- 数据源：WebAdapter（新浪+腾讯）覆盖行情数据，不覆盖财务数据
- 前端：`AIChatView.vue` 通用对话页，无基本面专项页面

## 目标架构

### 页面结构：单页面三Tab

```
/fundamental/:code?  (FundamentalView.vue)
┌─────────────────────────────────────────┐
│ 搜索栏 + 股票头（名称/现价/涨跌幅）       │
├─────────────────────────────────────────┤
│ Tab: [ AI研报 | 交互问答 | 批量对比 ]     │
├─────────────────────────────────────────┤
│ Tab 1 AI研报:                           │
│  ├ 财报趋势图（营收/利润/现金流）         │
│  ├ 估值仪表（PE/PB/ROE）                │
│  ├ 风险雷达（负债/质押/现金流/商誉）      │
│  └ AI 综合研报                          │
│ Tab 2 交互问答:                          │
│  ├ 数据卡片（可折叠）                    │
│  └ 对话区（基于当前财务数据追问）          │
│ Tab 3 批量对比:                          │
│  ├ 股票池 [+添加]                       │
│  ├ 指标选择                             │
│  └ 对比表格 + AI 点评                   │
└─────────────────────────────────────────┘
```

### 后端 API 设计

所有新 API 挂在 `/api/fundamental` 下：

| 端点 | 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|------|
| `/overview/{code}` | GET | - | `FinancialOverview` | 近5年营收/利润/现金流趋势 |
| `/valuation/{code}` | GET | - | `ValuationData` | PE/PB/PS/ROE/股息率 |
| `/risk/{code}` | GET | - | `RiskScreening` | 负债率/质押/现金流/商誉风险 |
| `/holders/{code}` | GET | - | `HolderData` | 十大股东/机构持仓变化 |
| `/report` | POST | `{code}` | `AIReport` | AI 生成完整基本面研报 |
| `/chat` | POST | `{code, message}` | `AIResponse` | 基于财务数据的交互问答 |
| `/compare` | POST | `{codes[], indicators[]}` | `CompareResult` | 多股横向对比 + AI 点评 |

### 数据模型（schemas/fundamental.py）

```python
class FinancialItem(BaseModel):
    date: str       # 报告期
    revenue: float  # 营业收入（亿元）
    net_profit: float   # 归母净利润（亿元）
    cash_flow: float    # 经营现金流（亿元）

class FinancialOverview(BaseModel):
    code: str
    name: str
    data: list[FinancialItem]

class ValuationData(BaseModel):
    code: str
    name: str
    pe: float           # 市盈率
    pb: float           # 市净率
    ps: float           # 市销率
    roe: float          # ROE(%)
    dividend_yield: float   # 股息率(%)
    industry_pe: float  # 行业平均PE

class RiskScreening(BaseModel):
    code: str
    name: str
    debt_ratio: float       # 资产负债率(%)
    pledge_ratio: float     # 质押比例(%)
    cash_flow_health: str   # 现金流健康度(健康/关注/预警)
    goodwill_ratio: float   # 商誉占比(%)
    risk_level: str         # 综合风险等级(低/中/高)
    risk_items: list[str]   # 风险提示项

class HolderItem(BaseModel):
    name: str
    ratio: float
    change: str  # 增持/减持/不变

class HolderData(BaseModel):
    code: str
    name: str
    top_holders: list[HolderItem]
    institution_change: str  # 机构持仓变化趋势

class AIReport(BaseModel):
    code: str
    name: str
    content: str  # Markdown 格式研报
    summary: str  # 一句话结论

class AIResponse(BaseModel):
    content: str

class CompareRequest(BaseModel):
    codes: list[str]
    indicators: list[str] = ["revenue_growth", "roe", "pe", "debt_ratio"]

class CompareResult(BaseModel):
    table: list[dict]    # 对比表格
    ai_comment: str     # AI 点评
```

### 数据源适配

主数据源：**akshare**（已验证 `stock_financial_abstract` 可用）

| 数据项 | akshare 函数 |
|--------|-------------|
| 财务摘要 | `stock_financial_abstract` |
| 资产负债表 | `stock_zcfz_em` |
| 利润表 | `stock_lrb_em` |
| 十大股东 | `stock_gdfx_top_10_em` |
| 业绩预报 | `stock_yjbb_em` |

估值数据（PE/PB/PS）：从新浪/东方财富实时行情补充

### AI 分析策略

复用现有 OpenAI 客户端，构建专用 prompt 模板：
- **研报模板**：结构化输出（公司概况/财报亮点/风险提示/估值判断/投资建议）
- **问答模板**：注入当前股票财务数据作为 system context
- **对比模板**：注入多股指标表，AI 给出横向评价

### 前端组件树

```
FundamentalView.vue
├── StockHeader.vue          — 搜索栏 + 股票基本信息
├── Tab 切换
├── Tab1 组件:
│   ├── FinancialChart.vue   — 营收/利润/现金流 ECharts
│   ├── ValuationGauge.vue   — PE/PB/ROE 仪表盘
│   ├── RiskRadar.vue        — 风险雷达图
│   └── AIReportCard.vue     — AI 研报卡片
├── Tab2 组件:
│   ├── DataCards.vue        — 可折叠数据摘要
│   └── ChatPanel.vue        — 对话区（基于现有 AIChat 逻辑）
└── Tab3 组件:
    ├── StockPool.vue        — 股票池增删
    └── CompareTable.vue     — 对比表 + AI 点评
```

### 路由

```ts
{ path: "/fundamental/:code?", name: "fundamental",
  component: () => import("../views/FundamentalView.vue") }
```

### 导航更新

在左侧导航新增"基本面分析"入口，链接 `/fundamental`。

## 不做的

- 不在此阶段做机构持仓详情页（后续迭代）
- 不做政策利好数据库（依赖外部政策库，后续评估）
- 不做历史研报存档
- 不修改现有行情和 AI 模块代码

## 数据刷新策略

- 财务数据：按需加载（用户输入代码后请求），财报数据变化频率低
- AI 研报：每次打开/刷新时重新生成
- 批量对比：用户点击"开始对比"触发
