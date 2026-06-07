# 模块四：智能资金监控 实施计划

> **For agentic workers:** 按任务顺序执行，每步完成后再做下一步。

**Goal:** 实现模块四智能资金监控，单页面四Tab（个股资金/北向资金/板块资金/AI资金解读），覆盖资金流趋势+主力动向+北向态度

**Architecture:** 后端新增 `/api/fundflow` 路由，通过新浪/腾讯免费 API 拉取资金流数据，复用 OpenAI 生成 AI 分析；前端单页面 FundFlowView.vue 四 Tab 切换

**Tech Stack:** FastAPI + requests, Vue 3 + TypeScript + ECharts + Pinia

**Spec:** docs/superpowers/specs/2026-06-08-fundflow-module-design.md

---

## 文件结构

```
backend/app/
  schemas/fundflow.py          [NEW] 数据模型
  services/fundflow_service.py [NEW] 资金流数据服务
  api/fundflow.py              [NEW] API 路由
  api/router.py                [MOD] 注册 fundflow 路由
frontend/src/
  views/FundFlowView.vue       [NEW] 主视图
  components/FundFlowChart.vue [NEW] 资金流向趋势图
  components/NorthBoundChart.vue [NEW] 北向资金图
  components/SectorFlowRank.vue [NEW] 板块资金排名
  stores/fundFlow.ts           [NEW] Pinia store
  api/index.ts                 [MOD] 新增 fundflow 模块
  router/index.ts              [MOD] 添加路由
  App.vue                      [MOD] 导航入口
```

---

### Task 1: 后端 Schemas — backend/app/schemas/fundflow.py [NEW]

定义 5 个 Pydantic 模型：
- `StockFlowItem` — 个股每日资金流（date, main_net, super_large_net, large_net, mid_net, small_net）
- `NorthBoundItem` — 北向每日（date, sh_net, sz_net, total_net, sh_balance, sz_balance）
- `SectorFlowItem` — 板块资金（name, net_amount, main_net, change_pct）
- `MarketFlowSummary` — 大盘总览（date, main_net, total_turnover, up_count, down_count）
- `AIReport` — AI 研报（code, name, content, summary）

### Task 2: 后端数据服务 — backend/app/services/fundflow_service.py [NEW]

核心方法：
- `get_stock_flow(code)` — 新浪 MoneyFlow API 获取个股资金流
- `get_northbound_flow(days=20)` — 腾讯 ff_hsgt 获取北向资金
- `get_northbound_daily()` — 当日北向概况
- `get_sector_flow()` — 新浪板块资金排名
- `get_market_flow()` — 大盘资金总览

### Task 3: 后端 API 路由 — backend/app/api/fundflow.py [NEW]

6 个端点：GET stock/northbound/northbound_daily/sectors/market, POST report

### Task 4: 注册路由 — backend/app/api/router.py [MOD]

添加 fundflow_router 注册

### Task 5: 前端 API + Store

- `api/index.ts` [MOD] — 新增 fundflow 模块
- `stores/fundFlow.ts` [NEW] — Pinia store

### Task 6: 前端组件（3个）

- `FundFlowChart.vue` [NEW] — ECharts 资金流趋势图（柱状+折线混合）
- `NorthBoundChart.vue` [NEW] — ECharts 北向资金净买入图
- `SectorFlowRank.vue` [NEW] — 板块资金排名（横向柱状图）

### Task 7: 前端主视图 + 路由 + 导航

- `FundFlowView.vue` [NEW] — 四 Tab 主视图
- `router/index.ts` [MOD] — 添加 /fundflow/:code? 路由
- `App.vue` [MOD] — 导航加 💰

### Task 8: 构建验证

- 后端导入验证
- 前端 vue-tsc + vite build
- curl 验证 API

