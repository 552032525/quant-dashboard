# 量化交易看板 — 设计规格书

> 状态：待审核  
> 日期：2026-06-03  
> 技术栈：Vue3 + FastAPI + PostgreSQL + Docker

---

## 1. 项目概述

### 1.1 目标

构建一个集**实时行情、策略回测、持仓管理、AI 分析、预警通知**于一体的个人量化交易看板，既是实用工具也是全栈能力展示作品。

### 1.2 用户画像

- 个人量化交易者，需要盯盘 + 回测 + 持仓管理一站式工具
- 有 Python 基础，使用 akshare/券商 API 获取数据
- 有服务器（43.138.253.185），自行部署

### 1.3 成功标准

- [ ] 本地 `docker-compose up` 一键启动全栈
- [ ] 可查看 A 股实时/历史 K 线图
- [ ] 可切换 akshare / 券商 API 数据源
- [ ] 持仓页面显示盈亏统计
- [ ] AI 面板可调用 GPT 解读行情
- [ ] 部署到服务器可通过域名/IP 访问

---

## 2. 设计语言

| 要素 | 取值 | 来源 |
|------|------|------|
| 底色 | `#0d1b2a`（暗夜海军蓝） | Stripe |
| 主色 | `#0052ff`（Coinbase Blue） | Coinbase |
| 涨色 | `#05b169`（绿） | Coinbase |
| 跌色 | `#cf202f`（红） | Coinbase |
| 正文字体 | Inter（400/500） | 开源替代 Sohne |
| 数值字体 | JetBrains Mono（等宽） | 金融数据展示 |
| CTA 圆角 | 100px 药丸形 | Stripe / Coinbase |
| 卡片圆角 | 12px | Stripe |
| 输入框圆角 | 8px | — |
| 阴影 | 堆叠微阴影 + 1px 发丝线边框 | Vercel / Linear |
| 配色原则 | 主色仅用于 CTA/关键交互，不滥用 | 稀缺强调色原则 |

---

## 3. 技术架构

### 3.1 技术选型

| 层 | 技术 | 理由 |
|----|------|------|
| 前端框架 | Vue3 + Vite | 用户技术栈匹配 |
| 状态管理 | Pinia | Vue3 官方推荐 |
| UI 组件 | TailwindCSS + 手写组件 | 精确控制金融风格 |
| 图表 | ECharts 5 | K线/分时图原生支持 |
| 后端框架 | FastAPI | 异步支持好，量化生态匹配 |
| ORM | SQLAlchemy 2.0 (async) | 成熟稳定 |
| 定时任务 | Celery + Redis | 定时拉行情 + 预警轮询 |
| 数据源 | akshare / 券商 API | 可插拔适配器模式 |
| AI | OpenAI GPT-5.5 API | 行情解读 |
| 数据库 | PostgreSQL 16 | 生产可靠 |
| 部署 | Docker Compose | 一键部署到服务器 |

### 3.2 项目结构

```
quant-dashboard/
├── frontend/                    # Vue3 SPA
│   ├── src/
│   │   ├── views/
│   │   │   ├── MarketView.vue          # 实时行情看板
│   │   │   ├── BacktestView.vue        # 策略回测
│   │   │   ├── PortfolioView.vue       # 持仓/账户
│   │   │   └── AIChatView.vue          # AI 分析面板
│   │   ├── components/
│   │   │   ├── KLineChart.vue          # K线图组件
│   │   │   ├── TickerTape.vue          # 滚动行情条
│   │   │   ├── OrderBook.vue           # 订单簿
│   │   │   ├── MetricCard.vue          # 指标卡片
│   │   │   └── AlertBadge.vue          # 预警通知
│   │   ├── stores/
│   │   │   ├── market.ts               # 行情状态
│   │   │   ├── portfolio.ts            # 持仓状态
│   │   │   └── settings.ts             # 用户设置
│   │   ├── api/                        # 后端接口封装
│   │   └── router/                     # Vue Router
│   ├── tailwind.config.js
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── market.py               # 行情接口
│   │   │   ├── backtest.py             # 回测接口
│   │   │   ├── portfolio.py            # 持仓接口
│   │   │   └── ai.py                   # AI 分析接口
│   │   ├── adapters/
│   │   │   ├── base.py                 # 数据源抽象基类
│   │   │   ├── akshare.py              # akshare 适配器
│   │   │   └── broker.py               # 券商 API 适配器
│   │   ├── engine/
│   │   │   └── backtest.py             # 回测引擎
│   │   ├── services/
│   │   │   ├── alert.py                # 预警服务
│   │   │   └── scheduler.py            # 定时任务
│   │   ├── models/                     # SQLAlchemy 模型
│   │   ├── schemas/                    # Pydantic 模式
│   │   └── core/
│   │       ├── config.py               # 配置中心
│   │       └── database.py             # 数据库连接
│   └── requirements.txt
├── docker-compose.yml
├── Dockerfile.frontend
├── Dockerfile.backend
└── README.md
```

### 3.3 数据流

```
[akshare/券商API] ──pull──> [Celery Worker] ──write──> [PostgreSQL]
                                                          │
[Browser] <──WebSocket/SSE── [FastAPI] <──read───────────┘
    │
    └──AI分析请求──> [FastAPI] ──> [OpenAI GPT-5.5] ──> 返回分析文本
```

---

## 4. 功能规格

### 4.1 行情看板（首页）

**布局**：三栏式
- **左栏（240px）**：自选股列表，可添加/删除/排序，点击切换主图
- **中栏（flex-1）**：K 线图（日/周/月/分钟切换）+ 分时图浮层
- **右栏（320px）**：最新价、涨跌幅大数字 + 五档盘口

**K 线图**：
- ECharts candlestick 系列
- 叠加 MA5/MA10/MA20/MA60 均线
- 下方成交量柱状图
- 可切换 MACD/RSI/KDJ 副图指标
- 十字光标 + 缩放拖拽

**顶部滚动条**：
- 自选股实时价一行滚动
- 涨绿跌红，等宽数字

**数据刷新**：
- 行情通过 WebSocket 推送（或 3 秒轮询降级）
- 历史 K 线从数据库读取

### 4.2 策略回测

**策略选择器**：
- 预置策略：均线交叉、双均线、网格交易、动量突破
- 参数面板（滑条 + 输入框实时调参）

**回测结果展示**：
- 收益曲线（ECharts 折线图，叠加基准对比）
- 指标卡片：总收益率、年化收益、最大回撤、夏普比率、胜率
- 交易明细表格（日期/方向/价格/数量/盈亏）

**回测流程**：
1. 用户选策略 + 调参数 + 选时间区间
2. 后端从数据库拉历史数据
3. 回测引擎逐日模拟交易
4. 返回结果 → 前端渲染

### 4.3 持仓管理

**总览卡片**：
- 总资产、持仓市值、可用资金、当日盈亏、累计盈亏
- 资产净值小曲线图

**持仓列表**：
- 表格列：代码、名称、持仓量、成本价、现价、浮动盈亏、盈亏%
- 每行右侧微型 sparkline

**操作**：
- 手动录入持仓（代码 + 数量 + 成本价）
- 编辑/删除
- 后续：对接券商 API 自动同步

### 4.4 AI 分析面板

**入口**：侧边可折叠面板 + 全屏模式

**功能**：
- 一键解读当前选中品种（发送最近 N 日行情数据给 GPT）
- 自定义提问输入框
- 对话历史保留

**提示词模板**：
> 你是一个量化交易分析师。以下是 {品种} 最近 {N} 日的行情数据：
> {OHLCV 数据}
> 请从技术面角度给出简要分析：趋势判断、关键支撑/压力位、风险提示。200 字以内。

### 4.5 预警通知

**触发条件**：
- 价格突破（上穿/下穿指定价）
- 涨跌幅超过阈值
- 均线金叉/死叉

**通知渠道**：
- 浏览器 Notification API（前台通知）
- 邮件（SMTP，复用已有的 QQ 邮箱配置）
- 后续：企业微信/钉钉 Webhook

---

## 5. API 设计（概要）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/market/realtime` | GET | 自选股实时行情 |
| `/api/market/kline/{symbol}` | GET | 历史 K 线数据 |
| `/api/market/search` | GET | 股票搜索 |
| `/api/portfolio` | GET/POST/PUT/DELETE | 持仓 CRUD |
| `/api/portfolio/summary` | GET | 持仓汇总统计 |
| `/api/backtest/run` | POST | 执行回测 |
| `/api/backtest/strategies` | GET | 可用策略列表 |
| `/api/ai/analyze` | POST | AI 分析 |
| `/api/ai/chat` | POST | AI 对话 |
| `/api/alerts` | GET/POST/DELETE | 预警管理 |
| `/api/watchlist` | GET/POST/DELETE | 自选股管理 |

---

## 6. 数据模型（概要）

```
Symbol (品种)
  - code: str (如 600519)
  - name: str
  - market: enum (SH/SZ)
  - type: enum (stock/etf/index)

KLineData (K线)
  - symbol_id: FK
  - date: date
  - open/high/low/close/volume

Position (持仓)
  - symbol_id: FK
  - quantity: int
  - cost_price: decimal
  - created_at / updated_at

Alert (预警)
  - symbol_id: FK
  - condition: enum
  - threshold: decimal
  - enabled: bool

WatchlistItem (自选股)
  - symbol_id: FK
  - sort_order: int
```

---

## 7. 部署

### 7.1 Docker Compose 服务

| 服务 | 镜像 | 端口 |
|------|------|------|
| frontend | nginx:alpine + Vue3 静态文件 | 80 |
| backend | python:3.12-slim + uvicorn | 8000 |
| db | postgres:16-alpine | 5432 |
| redis | redis:7-alpine | 6379 |
| celery | python:3.12-slim + celery | — |

### 7.2 部署步骤

```bash
# 1. 上传到服务器
rsync -avz ./ root@43.138.253.185:/opt/quant-dashboard/

# 2. SSH 登录
ssh root@43.138.253.185

# 3. 启动
cd /opt/quant-dashboard
docker-compose up -d
```

### 7.3 环境变量

```
POSTGRES_USER=quant
POSTGRES_PASSWORD=<secure>
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
DATA_SOURCE=akshare   # akshare | broker
SMTP_HOST=smtp.qq.com
SMTP_USER=xxx@qq.com
SMTP_PASS=<auth_code>
```

---

## 8. 分两期交付

### 第一期（MVP — 本周）

- [ ] 项目脚手架（Vue3 + FastAPI + Docker Compose）
- [ ] 行情看板页面（K 线图 + 自选股 + 盘口）
- [ ] akshare 数据源适配器
- [ ] 持仓管理（手动录入）
- [ ] AI 分析面板（GPT 行情解读）
- [ ] 部署到服务器 43.138.253.185

### 第二期（后续）

- [ ] 策略回测引擎
- [ ] 券商 API 适配器
- [ ] 预警通知系统（Celery 定时检查）
- [ ] 持仓自动同步
- [ ] 历史数据定时拉取 + 数据库存储

---

## 9. 风险与约束

| 风险 | 应对 |
|------|------|
| akshare 接口不稳定 | 适配器模式可随时切换，本地缓存降级 |
| 券商 API 各家协议不同 | 抽象基类定义统一接口，逐家实现 |
| 服务器性能有限 | PostgreSQL/Redis 使用 alpine 轻量镜像 |
| AI 调用成本 | 缓存常见分析结果，限制请求频率 |
| 实时行情延迟 | WebSocket 优先，轮询降级，显示更新时间戳 |

---

> 文档版本：v1.0  
> 下一步：用户审核通过后，进入实现计划阶段。
