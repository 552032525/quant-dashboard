# AI 基本面分析 实施计划

> **For agentic workers:** 按任务顺序执行，每步完成后再做下一步。使用 \- [ ]\ checkbox 跟踪进度。

**Goal:** 实现模块二 AI 基本面分析，单页面三Tab（AI研报/交互问答/批量对比），覆盖财报解析+估值+风险筛查

**Architecture:** 后端新增 /api/fundamental 路由，通过 akshare 财务服务拉取数据，复用 OpenAI 生成 AI 分析；前端单页面 FundamentalView.vue 三 Tab 切换，共享 Pinia store

**Tech Stack:** FastAPI + akshare + OpenAI, Vue 3 + TypeScript + ECharts + Pinia

**Spec:** docs/superpowers/specs/2026-06-07-fundamental-module-design.md

---

## 文件结构

`
backend/app/
  schemas/fundamental.py     [NEW] 数据模型
  services/__init__.py       [NEW]
  services/financial_service.py [NEW] akshare 财务数据服务
  api/fundamental.py          [NEW] API 路由
  api/router.py               [MOD] 注册 fundamental 路由
frontend/src/
  api/index.ts                [MOD] 新增 fundamental API 客户端
  stores/fundamental.ts       [NEW] Pinia store
  views/FundamentalView.vue   [NEW] 主视图
  components/FinancialChart.vue  [NEW] 财务趋势图
  components/ValuationGauge.vue  [NEW] 估值仪表
  components/RiskRadar.vue       [NEW] 风险雷达
  components/AIReportCard.vue    [NEW] AI研报卡片
  components/DataCards.vue       [NEW] 可折叠数据卡片
  components/CompareTable.vue    [NEW] 对比表格
  router/index.ts              [MOD] 添加路由
  App.vue                      [MOD] 导航入口
`


### Task 1: ?? Schemas

**Files:** backend/app/schemas/fundamental.py [NEW]

?? 8 ? Pydantic ??: FinancialOverview, ValuationData, RiskScreening, HolderData, AIReport, AIResponse, CompareRequest, CompareResult?????????? schemas/fundamental.py ??

- [ ] Step 1: ??????? schemas/fundamental.py
- [ ] Step 2: ??: cd backend; py -c "from app.schemas.fundamental import FinancialOverview; print('OK')"

### Task 2: ??????

**Files:** 
- backend/app/services/__init__.py [NEW]
- backend/app/services/financial_service.py [NEW]

FinancialService ?? akshare ??: get_financial_overview / get_valuation / get_risk / get_holders??????

- [ ] Step 1: ?? __init__.py
- [ ] Step 2: ?? financial_service.py
- [ ] Step 3: ??: cd backend; py -c "from app.services.financial_service import get_financial_service; s=get_financial_service(); print(s.get_valuation('600519'))"

### Task 3: API ??

**Files:** backend/app/api/fundamental.py [NEW]

7 ???: GET overview/valuation/risk/holders/{code}, POST report/chat/compare?AI ???? OpenAI?

- [ ] Step 1: ?? api/fundamental.py
- [ ] Step 2: ????: cd backend; py -c "from app.api.fundamental import router; print('OK')"

### Task 4: ????

**Files:** backend/app/api/router.py [MOD]

```python
from app.api.fundamental import router as fundamental_router
api_router.include_router(fundamental_router, tags=["fundamental"])
```

- [ ] Step 1: ?? router.py
- [ ] Step 2: ?????? /docs ?? fundamental ??

### Task 5: ?? API ?

**Files:** frontend/src/api/index.ts [MOD]

? api ???? fundamental ??(overview/valuation/risk/holders/report/chat/compare)?

- [ ] Step 1: ?? index.ts

### Task 6: ?? Store

**Files:** frontend/src/stores/fundamental.ts [NEW]

useFundamentalStore: code/name/loading/overview/valuation/risk/holders/report/compareResult + fetchAll/fetchReport/chat/compare?

- [ ] Step 1: ?? stores/fundamental.ts

### Task 7-10: ????(4?)

**Files (all NEW):**
- frontend/src/components/FinancialChart.vue ? ECharts ??/??/?????
- frontend/src/components/ValuationGauge.vue ? PE/PB/PS/ROE/?????
- frontend/src/components/RiskRadar.vue ? ????+????
- frontend/src/components/AIReportCard.vue ? AI????+??
- frontend/src/components/DataCards.vue ? ???????
- frontend/src/components/CompareTable.vue ? ????+AI??

- [ ] Step 1-6: ?????? 6 ???

### Task 11: ???

**Files:** frontend/src/views/FundamentalView.vue [NEW]

??? + ??? + ? Tab(AI??/????/????)?

- [ ] Step 1: ?? FundamentalView.vue

### Task 12: ?? + ??

**Files:** 
- frontend/src/router/index.ts [MOD] ? ?? /fundamental/:code?
- frontend/src/App.vue [MOD] ? ?????????

- [ ] Step 1: ????
- [ ] Step 2: ????

### Task 13: ?????

- [ ] Step 1: ????: cd backend; py -m uvicorn app.main:app --port 8000
- [ ] Step 2: curl ?? GET /api/fundamental/overview/600519 ? 4 ???
- [ ] Step 3: ????: cd frontend; npm run dev
- [ ] Step 4: ???????->AI??->????->????
- [ ] Step 5: git commit
