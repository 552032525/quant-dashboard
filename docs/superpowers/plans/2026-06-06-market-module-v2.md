# 实时行情模块 V2 实施计划

> **For agentic workers:** 按任务顺序执行，每步完成后再做下一步。使用 `[ ]` checkbox 语法跟踪进度。

**目标**: 将行情模块升级为市场总览仪表盘 + 多周期个股深度页

**架构**: 扩展 AkshareAdapter → 新增 5 个 API 端点 → 构建 6 个前端组件 → 重构路由

**技术栈**: FastAPI + akshare, Vue 3 + TypeScript + ECharts + Pinia

---

### Task 1: 扩展 data schema

**Files:**
- Modify: `backend/app/schemas/market.py`

- [ ] **Step 1: 新增 IndexQuote / MarketHeat / SectorInfo / RankingItem / IntradayPoint 模型**

```python
from pydantic import BaseModel

class KLineItem(BaseModel):
    date: str; open: float; high: float; low: float; close: float; volume: float

class RealtimeQuote(BaseModel):
    code: str; name: str; price: float; change: float; change_pct: float
    volume: float; high: float; low: float; open: float; pre_close: float

class SymbolInfo(BaseModel):
    code: str; name: str; market: str; type: str

# --- 新增 ---

class IndexQuote(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_pct: float

class MarketHeat(BaseModel):
    up_count: int
    down_count: int
    flat_count: int
    limit_up: int
    limit_down: int
    total_volume: float
    north_flow: float

class SectorInfo(BaseModel):
    name: str
    change_pct: float
    lead_stock: str
    stock_count: int

class RankingItem(BaseModel):
    code: str
    name: str
    price: float
    change_pct: float

class IntradayPoint(BaseModel):
    time: str
    price: float
    avg_price: float
    volume: float
```

- [ ] **Step 2: 验证 schema 导入无报错**

Run: `cd backend && python -c "from app.schemas.market import IndexQuote, MarketHeat, SectorInfo, RankingItem, IntradayPoint; print('OK')"`
Expected: 输出 `OK`

---

### Task 2: 扩展 AkshareAdapter — 指数行情 & 市场热度

**Files:**
- Modify: `backend/app/adapters/akshare_adapter.py`

- [ ] **Step 1: 添加 get_index_quotes 方法**

```python
async def get_index_quotes(self) -> list[dict]:
    return await asyncio.to_thread(self._get_index_quotes)

def _get_index_quotes(self) -> list[dict]:
    import akshare as ak
    df = ak.stock_zh_index_spot_em()
    targets = {"000001": "上证指数", "399001": "深证成指", "399006": "创业板指"}
    result = []
    for _, row in df.iterrows():
        code = str(row["代码"])
        if code in targets:
            result.append({
                "code": code, "name": row["名称"],
                "price": float(row["最新价"]), "change": float(row["涨跌额"]),
                "change_pct": float(row["涨跌幅"]),
            })
    return result
```

- [ ] **Step 2: 添加 get_market_heat 方法**

```python
async def get_market_heat(self) -> dict:
    return await asyncio.to_thread(self._get_market_heat)

def _get_market_heat(self) -> dict:
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    up_count = int((df["涨跌幅"] > 0).sum())
    down_count = int((df["涨跌幅"] < 0).sum())
    flat_count = int((df["涨跌幅"] == 0).sum())
    total_volume = round(float(df["成交额"].sum()) / 1e8, 2)
    # 北向资金
    try:
        north_df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
        north_flow = float(north_df.iloc[-1]["当日净流入"]) if len(north_df) > 0 else 0.0
    except Exception:
        north_flow = 0.0
    return {
        "up_count": up_count, "down_count": down_count, "flat_count": flat_count,
        "limit_up": 0, "limit_down": 0,
        "total_volume": total_volume, "north_flow": north_flow,
    }
```

- [ ] **Step 3: 验证两个方法可调用**

Run: `cd backend && python -c "import asyncio; from app.adapters.akshare_adapter import AkshareAdapter; a=AkshareAdapter(); print(asyncio.run(a.get_index_quotes())); print(asyncio.run(a.get_market_heat()))"`
Expected: 返回指数列表和市场热度数据

---

### Task 3: 扩展 AkshareAdapter — 板块 & 排行

**Files:**
- Modify: `backend/app/adapters/akshare_adapter.py`

- [ ] **Step 1: 添加 get_sectors 方法**

```python
async def get_sectors(self, sector_type: str = "industry") -> list[dict]:
    return await asyncio.to_thread(self._get_sectors, sector_type)

def _get_sectors(self, sector_type: str) -> list[dict]:
    import akshare as ak
    fn = ak.stock_board_industry_spot_em if sector_type == "industry" else ak.stock_board_concept_spot_em
    df = fn()
    result = []
    for _, row in df.iterrows():
        result.append({
            "name": row["板块名称"],
            "change_pct": float(row["涨跌幅"]),
            "lead_stock": row.get("领涨股票", ""),
            "stock_count": int(row.get("公司家数", 0)),
        })
    return result
```

- [ ] **Step 2: 添加 get_rankings 方法**

```python
async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]:
    return await asyncio.to_thread(self._get_rankings, rank_type, limit)

def _get_rankings(self, rank_type: str, limit: int) -> list[dict]:
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    ascending = rank_type != "up"
    df_sorted = df.sort_values("涨跌幅", ascending=ascending).head(limit)
    result = []
    for _, row in df_sorted.iterrows():
        result.append({
            "code": row["代码"], "name": row["名称"],
            "price": float(row["最新价"]), "change_pct": float(row["涨跌幅"]),
        })
    return result
```

- [ ] **Step 3: 验证**

Run: `cd backend && python -c "import asyncio; from app.adapters.akshare_adapter import AkshareAdapter; a=AkshareAdapter(); print(len(asyncio.run(a.get_sectors('industry')))); print(len(asyncio.run(a.get_rankings('up', 5))))"`
Expected: 返回行业板块数量和5条涨幅排行

---

### Task 4: 扩展 AkshareAdapter — 分时 & 分钟K线

**Files:**
- Modify: `backend/app/adapters/akshare_adapter.py`

- [ ] **Step 1: 修改 get_kline 支持分钟周期**

在现有 `_get_kline` 方法中，`period` 参数扩展映射：

```python
def _get_kline(self, code: str, start_date: date, end_date: date, period: str = "daily") -> list[dict]:
    import akshare as ak
    # 分钟周期映射
    minute_periods = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
    if period in minute_periods:
        df = ak.stock_zh_a_hist_min_em(symbol=code, period=period,
            start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date=end_date.strftime("%Y-%m-%d %H:%M:%S"), adjust="qfq")
        return [{"date": str(row["时间"]), "open": float(row["开盘"]), "high": float(row["最高"]),
                 "low": float(row["最低"]), "close": float(row["收盘"]), "volume": float(row["成交量"])}
                for _, row in df.iterrows()]
    # 日/周/月
    period_map = {"weekly": "week", "monthly": "month"}
    ak_period = period_map.get(period, "daily")
    df = ak.stock_zh_a_hist(symbol=code, period=ak_period,
        start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
    return [{"date": str(row["日期"]), "open": float(row["开盘"]), "high": float(row["最高"]),
             "low": float(row["最低"]), "close": float(row["收盘"]), "volume": float(row["成交量"])}
            for _, row in df.iterrows()]
```

- [ ] **Step 2: 添加 get_intraday 方法**

```python
async def get_intraday(self, code: str) -> list[dict]:
    return await asyncio.to_thread(self._get_intraday, code)

def _get_intraday(self, code: str) -> list[dict]:
    import akshare as ak
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    df = ak.stock_zh_a_hist_min_em(symbol=code, period="1",
        start_date=f"{today} 09:30:00", end_date=f"{today} 15:00:00", adjust="")
    result = []
    for _, row in df.iterrows():
        result.append({
            "time": str(row["时间"]),
            "price": float(row["收盘"]),
            "avg_price": float(row["收盘"]),
            "volume": float(row["成交量"]),
        })
    return result
```

- [ ] **Step 3: 同步更新 base adapter 抽象接口**

在 `backend/app/adapters/base.py` 添加新抽象方法：

```python
@abstractmethod
async def get_index_quotes(self) -> list[dict]: ...

@abstractmethod
async def get_market_heat(self) -> dict: ...

@abstractmethod
async def get_sectors(self, sector_type: str = "industry") -> list[dict]: ...

@abstractmethod
async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]: ...

@abstractmethod
async def get_intraday(self, code: str) -> list[dict]: ...
```

- [ ] **Step 4: 验证分时和分钟K线**

Run: `cd backend && python -c "import asyncio; from app.adapters.akshare_adapter import AkshareAdapter; a=AkshareAdapter(); r=asyncio.run(a.get_intraday('600519')); print(len(r)); r2=asyncio.run(a.get_kline('600519', __import__('datetime').date.today()-__import__('datetime').timedelta(5), __import__('datetime').date.today(), '60')); print(len(r2))"`

---

### Task 5: 新增 API 端点

**Files:**
- Modify: `backend/app/api/market.py`

- [ ] **Step 1: 在 market.py 末尾添加 5 个新端点**

```python
from app.schemas.market import IndexQuote, MarketHeat, SectorInfo, RankingItem, IntradayPoint

@router.get("/index", response_model=list[IndexQuote])
async def get_index():
    try:
        data = await get_adapter().get_index_quotes()
        return [IndexQuote(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/heat", response_model=MarketHeat)
async def get_heat():
    try:
        data = await get_adapter().get_market_heat()
        return MarketHeat(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectors", response_model=list[SectorInfo])
async def get_sectors(type: str = "industry"):
    try:
        data = await get_adapter().get_sectors(type)
        return [SectorInfo(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rankings", response_model=list[RankingItem])
async def get_rankings(type: str = "up", limit: int = 20):
    try:
        data = await get_adapter().get_rankings(type, limit)
        return [RankingItem(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intraday/{code}", response_model=list[IntradayPoint])
async def get_intraday(code: str):
    try:
        data = await get_adapter().get_intraday(code)
        return [IntradayPoint(**item) for item in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: 修改现有 kline 端点，扩展 period 参数**

在 `get_kline` 函数签名中，将 `period: str = "daily"` 改为接受任意周期字符串（FastAPI 默认已接受 string，无需改动）。

- [ ] **Step 3: 启动后端验证 API**

Run: `cd backend && python -m uvicorn app.main:app --port 8000 &` 然后 `curl http://localhost:8000/api/market/index`

---

### Task 6: 切换默认数据源 & baostock 适配器兼容

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/adapters/baostock_adapter.py`

- [ ] **Step 1: 默认数据源改为 akshare**

```python
data_source: str = "akshare"  # was "baostock"
```

- [ ] **Step 2: baostock 适配器添加新方法占位**

在 `baostock_adapter.py` 中为新增的 5 个抽象方法添加实现，返回空或抛 NotImplementedError：

```python
async def get_index_quotes(self) -> list[dict]:
    return []

async def get_market_heat(self) -> dict:
    return {"up_count":0,"down_count":0,"flat_count":0,"limit_up":0,"limit_down":0,"total_volume":0,"north_flow":0}

async def get_sectors(self, sector_type: str = "industry") -> list[dict]:
    return []

async def get_rankings(self, rank_type: str = "up", limit: int = 20) -> list[dict]:
    return []

async def get_intraday(self, code: str) -> list[dict]:
    return []
```

---

### Task 7: 前端 API 层扩展 & Store 更新

**Files:**
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/stores/market.ts`

- [ ] **Step 1: api/index.ts 新增 market 子 API**

```typescript
market: {
  realtime: (code: string) => request(`/api/market/realtime/${code}`),
  kline: (code: string, period = "daily", start?: string, end?: string) => {
    const p = new URLSearchParams({ period });
    if (start) p.set("start_date", start);
    if (end) p.set("end_date", end);
    return request(`/api/market/kline/${code}?${p}`);
  },
  search: (keyword: string) => request(`/api/market/search?keyword=${encodeURIComponent(keyword)}`),
  index: () => request("/api/market/index"),
  heat: () => request("/api/market/heat"),
  sectors: (type = "industry") => request(`/api/market/sectors?type=${type}`),
  rankings: (type = "up", limit = 20) => request(`/api/market/rankings?type=${type}&limit=${limit}`),
  intraday: (code: string) => request(`/api/market/intraday/${code}`),
},
```

- [ ] **Step 2: 扩展 market store**

```typescript
import { defineStore } from "pinia";
import { api } from "../api";

export const useMarketStore = defineStore("market", {
  state: () => ({
    activeSymbol: "600519",
    quote: null as any,
    klineData: [] as any[],
    loading: false,
    error: "",
    period: "daily" as string,
    // 新增
    indexQuotes: [] as any[],
    heat: null as any,
    sectors: [] as any[],
    rankings: [] as any[],
    intradayData: [] as any[],
  }),
  actions: {
    async fetchKline(code: string) {
      this.activeSymbol = code; this.loading = true; this.error = "";
      try {
        const [q, k] = await Promise.all([
          api.market.realtime(code),
          api.market.kline(code, this.period),
        ]);
        this.quote = q; this.klineData = k;
      } catch (e: any) { this.error = e.message || "加载失败"; }
      finally { this.loading = false; }
    },
    async fetchIndex() {
      this.indexQuotes = await api.market.index();
    },
    async fetchHeat() {
      this.heat = await api.market.heat();
    },
    async fetchSectors(type = "industry") {
      this.sectors = await api.market.sectors(type);
    },
    async fetchRankings(type = "up") {
      this.rankings = await api.market.rankings(type);
    },
    async fetchIntraday(code: string) {
      this.intradayData = await api.market.intraday(code);
    },
  },
});
```

---

### Task 8: 创建 IndexBar.vue

**Files:**
- Create: `frontend/src/components/IndexBar.vue`

```vue
<template>
  <div class="flex gap-4 px-4 py-3 bg-surface border-b border-surface-2">
    <div v-for="idx in data" :key="idx.code" class="flex items-center gap-2 text-sm">
      <span class="text-text-secondary">{{ idx.name }}</span>
      <span class="font-mono">{{ idx.price?.toFixed(2) }}</span>
      <span class="font-mono text-xs" :class="idx.change_pct >= 0 ? 'text-gain' : 'text-loss'">
        {{ idx.change_pct >= 0 ? '+' : '' }}{{ idx.change_pct?.toFixed(2) }}%
      </span>
    </div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ data: any[] }>();
</script>
```

---

### Task 9: 创建 HeatBar.vue

**Files:**
- Create: `frontend/src/components/HeatBar.vue`

```vue
<template>
  <div v-if="data" class="flex gap-6 px-4 py-2 bg-surface border-b border-surface-2 text-xs text-text-secondary">
    <span>上涨 <b class="text-gain">{{ data.up_count }}</b></span>
    <span>下跌 <b class="text-loss">{{ data.down_count }}</b></span>
    <span>平盘 {{ data.flat_count }}</span>
    <span>成交额 <b class="text-text-primary">{{ data.total_volume }}亿</b></span>
    <span>北向 <b :class="data.north_flow >= 0 ? 'text-gain' : 'text-loss'">{{ data.north_flow >= 0 ? '+' : '' }}{{ data.north_flow }}亿</b></span>
  </div>
</template>
<script setup lang="ts">
defineProps<{ data: any }>();
</script>
```

---

### Task 10: 创建 SectorHeatmap.vue

**Files:**
- Create: `frontend/src/components/SectorHeatmap.vue`

```vue
<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center gap-2 px-3 py-2">
      <span class="text-sm font-medium text-text-primary">板块热力图</span>
      <button @click="$emit('toggle')" class="text-xs text-primary hover:opacity-80">{{ type === 'industry' ? '行业' : '概念' }} ▸</button>
    </div>
    <div ref="chartRef" class="flex-1"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any[]; type: string }>();
defineEmits<{ toggle: [] }>();
const chartRef = ref<HTMLDivElement>();
let chart: echarts.ECharts | null = null;

function buildOption(data: any[]) {
  const max = Math.max(...data.map(d => Math.abs(d.change_pct)), 1);
  return {
    tooltip: { formatter: (p: any) => `${p.name}<br/>涨跌幅: ${p.value > 0 ? '+' : ''}${p.value}%` },
    series: [{
      type: "treemap", roam: false, nodeClick: false,
      width: "100%", height: "100%",
      data: data.map(d => ({
        name: d.name,
        value: Math.abs(d.change_pct) + 0.01,
        change_pct: d.change_pct,
        itemStyle: {
          color: d.change_pct >= 0
            ? `rgba(5, 177, 105, ${0.3 + Math.abs(d.change_pct) / max * 0.7})`
            : `rgba(207, 32, 47, ${0.3 + Math.abs(d.change_pct) / max * 0.7})`,
        },
      })),
      levels: [{
        itemStyle: { borderColor: "#0d1b2a", borderWidth: 1, gapWidth: 1 },
      }],
      label: { show: true, fontSize: 9, color: "#8899aa", formatter: (p: any) => `${p.name}\n${p.data.change_pct > 0 ? '+' : ''}${p.data.change_pct}%` },
    }],
  };
}

onMounted(() => {
  if (chartRef.value) { chart = echarts.init(chartRef.value); render(); window.addEventListener("resize", () => chart?.resize()); }
});
watch(() => props.data, render);
function render() { if (chart && props.data.length) chart.setOption(buildOption(props.data), true); }
onUnmounted(() => chart?.dispose());
</script>
```

---

### Task 11: 创建 RankingList.vue

**Files:**
- Create: `frontend/src/components/RankingList.vue`

```vue
<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center gap-2 px-3 py-2">
      <span class="text-sm font-medium text-text-primary">涨跌排行</span>
      <button @click="$emit('toggle')" class="text-xs text-primary hover:opacity-80">{{ rankType === 'up' ? '涨幅榜' : '跌幅榜' }} ▸</button>
    </div>
    <div class="flex-1 overflow-auto">
      <div v-for="(item, i) in data" :key="item.code"
        @click="$emit('select', item.code)"
        class="flex items-center px-3 py-1.5 hover:bg-surface-2 cursor-pointer text-xs border-b border-surface-2">
        <span class="w-5 text-text-secondary">{{ i + 1 }}</span>
        <span class="flex-1 font-mono">{{ item.code }}</span>
        <span class="w-28 truncate">{{ item.name }}</span>
        <span class="w-16 text-right font-mono">{{ item.price?.toFixed(2) }}</span>
        <span class="w-20 text-right font-mono" :class="item.change_pct >= 0 ? 'text-gain' : 'text-loss'">
          {{ item.change_pct >= 0 ? '+' : '' }}{{ item.change_pct?.toFixed(2) }}%
        </span>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ data: any[]; rankType: string }>();
defineEmits<{ toggle: []; select: [code: string] }>();
</script>
```

---

### Task 12: 创建 MarketOverview.vue（首页）

**Files:**
- Create: `frontend/src/views/MarketOverview.vue`

```vue
<template>
  <div class="h-full flex flex-col">
    <IndexBar :data="m.indexQuotes" />
    <HeatBar :data="m.heat" />
    <div class="flex-1 flex overflow-hidden">
      <div class="flex-1 border-r border-surface-2">
        <SectorHeatmap :data="m.sectors" :type="sectorType" @toggle="sectorType = sectorType === 'industry' ? 'concept' : 'industry'; m.fetchSectors(sectorType)" />
      </div>
      <div class="w-80">
        <RankingList :data="m.rankings" :rankType="rankType"
          @toggle="rankType = rankType === 'up' ? 'down' : 'up'; m.fetchRankings(rankType)"
          @select="code => $router.push(`/stock/${code}`)" />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useMarketStore } from "../stores/market";
import IndexBar from "../components/IndexBar.vue";
import HeatBar from "../components/HeatBar.vue";
import SectorHeatmap from "../components/SectorHeatmap.vue";
import RankingList from "../components/RankingList.vue";

const m = useMarketStore();
const sectorType = ref("industry");
const rankType = ref("up");

onMounted(async () => {
  await Promise.all([m.fetchIndex(), m.fetchHeat(), m.fetchSectors("industry"), m.fetchRankings("up")]);
});
</script>
```

---

### Task 13: 改造 MarketView → MarketDetail.vue（增加多周期/分时）

**Files:**
- Modify: `frontend/src/views/MarketView.vue` → 重命名为 `MarketDetail.vue` 并改造

方案：复制 `MarketView.vue` 内容，添加周期切换 Tab，增加分时图支持。

实际做法：直接修改 `MarketView.vue` 的内容（保持在原文件位置），router 中把 `MarketView` 挂到 `/stock/:code`。

Modifications to MarketView.vue (keep file, change content):

1. 在搜索框下方增加周期 Tab：
```html
<div class="flex gap-1 px-4 py-1 border-b border-surface-2">
  <button v-for="p in periods" :key="p.value"
    @click="switchPeriod(p.value)"
    class="px-3 py-1 text-xs rounded"
    :class="m.period === p.value ? 'bg-primary text-white' : 'text-text-secondary hover:bg-surface-2'">
    {{ p.label }}
  </button>
</div>
```

2. script 中添加：
```typescript
const periods = [
  { label: "分时", value: "intraday" },
  { label: "30分", value: "30" },
  { label: "60分", value: "60" },
  { label: "日K", value: "daily" },
  { label: "周K", value: "weekly" },
  { label: "月K", value: "monthly" },
];

async function switchPeriod(p: string) {
  m.period = p;
  if (p === "intraday") {
    m.intradayData = await api.market.intraday(m.activeSymbol);
    m.klineData = m.intradayData;
  } else {
    await m.fetchKline(m.activeSymbol);
  }
}
```

3. KLineChart 在分时模式下改为 line 图而非 candlestick。传入 `period` prop 给 KLineChart。

4. 从路由 params 读取 code：`import { useRoute } from "vue-router"; const route = useRoute();` onMounted 中 `m.fetchKline(route.params.code as string || "600519")`

---

### Task 14: 更新路由

**Files:**
- Modify: `frontend/src/router/index.ts`

```typescript
import { createRouter, createWebHistory } from "vue-router";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "market", component: () => import("../views/MarketOverview.vue") },
    { path: "/stock/:code", name: "stock-detail", component: () => import("../views/MarketView.vue") },
    { path: "/portfolio", name: "portfolio", component: () => import("../views/PortfolioView.vue") },
    { path: "/ai", name: "ai", component: () => import("../views/AIChatView.vue") },
  ],
});
export default router;
```

---

### Task 15: 全链路验证

- [ ] **Step 1: 启动后端**
Run: `cd backend && python -m uvicorn app.main:app --port 8000 --reload`

- [ ] **Step 2: 验证所有新 API**
```bash
curl http://localhost:8000/api/market/index
curl http://localhost:8000/api/market/heat
curl "http://localhost:8000/api/market/sectors?type=industry"
curl "http://localhost:8000/api/market/rankings?type=up&limit=10"
curl http://localhost:8000/api/market/intraday/600519
curl "http://localhost:8000/api/market/kline/600519?period=60"
```

- [ ] **Step 3: 启动前端**
Run: `cd frontend && npm run dev`

- [ ] **Step 4: 浏览器验证**
  1. 打开 `http://localhost:5173` → 看到市场总览首页（指数条 + 热度 + 板块热力图 + 排行）
  2. 点击排行中任意股票 → 跳转 `/stock/代码` 详情页
  3. 切换周期 Tab → K线/分时图更新
  4. 板块热力图切换行业/概念
