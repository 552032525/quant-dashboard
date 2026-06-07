# 模块三：AI 技术面智能分析 实施计划

> **For agentic workers:** 按任务顺序执行，每步完成后再做下一步。使用 `- [ ]` checkbox 跟踪进度。

**Goal:** 实现模块三 AI 技术面智能分析，单页面六指标图表+量化打分+AI研报

**Architecture:** 后端新增 `/api/technical` 路由，Python 原生计算 MACD/RSI/KDJ/BOLL/MA；前端 TechnicalView.vue 单页滚动，改造 KLineChart 叠加指标

**Spec:** docs/superpowers/specs/2026-06-07-technical-module-design.md

## 文件结构

```
backend/app/
  services/technical_service.py [NEW] 指标计算服务
  schemas/technical.py          [NEW] 数据模型
  api/technical.py              [NEW] API 路由
  api/router.py                 [MOD] 注册 technical 路由
frontend/src/
  views/TechnicalView.vue       [NEW] 主视图
  components/MacdChart.vue      [NEW] MACD 子图
  components/RsiKdjChart.vue    [NEW] RSI+KDJ
  components/ScoreCards.vue     [NEW] 打分卡片
  components/KLineChart.vue     [MOD] 叠加MA+BOLL
  api/index.ts                  [MOD] 新增 technical 模块
  stores/technical.ts           [NEW] Pinia store
  router/index.ts               [MOD] 添加路由
  App.vue                       [MOD] 导航入口
```

---

### Task 1: Schemas — backend/app/schemas/technical.py [NEW]

```python
from pydantic import BaseModel

class IndicatorData(BaseModel):
    dates: list[str]
    open: list[float]; high: list[float]; low: list[float]; close: list[float]; volume: list[float]
    ma5: list[float]; ma10: list[float]; ma20: list[float]; ma60: list[float]
    boll_up: list[float]; boll_mid: list[float]; boll_dn: list[float]
    macd_dif: list[float]; macd_dea: list[float]; macd_bar: list[float]
    rsi6: list[float]; rsi12: list[float]; rsi24: list[float]
    kdj_k: list[float]; kdj_d: list[float]; kdj_j: list[float]

class AnomalyItem(BaseModel):
    date: str; type: str; description: str

class AnomalyResult(BaseModel):
    code: str; name: str; anomalies: list[AnomalyItem]

class ScoreResult(BaseModel):
    code: str; name: str
    trend: int; momentum: int; volatility: int; volume_score: int; total: int
    description: str

class AIReport(BaseModel):
    code: str; name: str; content: str; summary: str
```

- [ ] Step 1: 创建 schemas/technical.py
- [ ] Step 2: 验证: `cd backend; py -c "from app.schemas.technical import IndicatorData, ScoreResult; print('OK')"`

### Task 2: 指标计算服务 — backend/app/services/technical_service.py [NEW]

核心方法：`calc_indicators(code, period)` 返回完整 IndicatorData。

计算逻辑（纯 Python，无依赖）：
- MA: `sum(last N closes) / N`
- EMA: `price * k + prev_ema * (1-k)`, k=2/(N+1)
- MACD: EMA12 - EMA26 = DIF, DIF的EMA9 = DEA, BAR = 2*(DIF-DEA)
- RSI: `100 - 100/(1 + avg_gain/avg_loss)` over N periods
- KDJ: RSV = (C-L9)/(H9-L9)*100, K=2/3*prev_K+1/3*RSV, D=2/3*prev_D+1/3*K, J=3*K-2*D
- BOLL: MA20, UP = MA20 + 2*std, DN = MA20 - 2*std
- Anomaly: 放量长阳(vol>2xMA_vol & change>5%), 缩量十字星(vol<0.5xMA_vol & abs(open-close)/open<0.3%)

- [ ] Step 1: 创建 technical_service.py
- [ ] Step 2: 验证: `cd backend; py -c "from app.services.technical_service import calc_indicators; d=calc_indicators('600519','daily'); print(len(d['dates']), d['rsi6'][-1])"`

### Task 3: API 路由 — backend/app/api/technical.py [NEW]

4 个端点：
- `GET /indicators/{code}?period=daily` — 返回完整指标数据
- `GET /anomaly/{code}` — 异动检测
- `POST /report` — AI 研报（注入指标摘要）
- `POST /score` — 量化打分（纯规则计算，不调 AI）

- [ ] Step 1: 创建 api/technical.py
- [ ] Step 2: 验证导入
- [ ] Step 3: 在 router.py 注册

### Task 4: 前端改造 KLineChart [MOD]

在现有 KLineChart.vue 基础上：
- 叠加 MA5/10/20/60 折线
- 叠加 BOLL 上中下轨
- 接收周期切换 prop

- [ ] Step 1: 改造 KLineChart.vue

### Task 5: 新建组件 — MacdChart / RsiKdjChart / ScoreCards [NEW]

- MacdChart.vue: DIF/DEA线 + 红绿柱
- RsiKdjChart.vue: 左右各一个ECharts，RSI三线 + KDJ三线
- ScoreCards.vue: 5个评分卡片 grid

- [ ] Step 1-3: 创建三个组件

### Task 6: Store + API + 主视图 [NEW/MOD]

- stores/technical.ts: Pinia store
- api/index.ts: technical 模块
- TechnicalView.vue: 主视图（搜索+周期+K线+指标+打分+AI研报）

- [ ] Step 1-3: 创建

### Task 7: 路由 + 导航 + 验证

- [ ] Step 1: router 加 /technical/:code?
- [ ] Step 2: App.vue 加 📊
- [ ] Step 3: vue-tsc + vite build
- [ ] Step 4: 启动后端，curl 验证 API
- [ ] Step 5: commit
