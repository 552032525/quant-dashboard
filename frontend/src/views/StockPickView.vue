<template>
  <div class="p-3 md:p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-6">🎯 AI 智能选股 & 策略回测</h2>

    <div class="flex flex-wrap gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-xs md:text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- 多因子选股 -->
    <div v-show="tab==='screen'" class="space-y-4">
            <div class="flex gap-2 mb-3">
        <label class="text-xs text-[#8fa5c6] self-center">筛选模式：</label>
        <select v-model="screenMode" class="bg-[#132438] text-white px-3 py-1.5 rounded text-sm border border-[#1a314a]">
          <option value="simple">综合打分</option>
          <option value="volume_break">放量上涨</option>
          <option value="breakout">突破新高</option>
        </select>
      </div>
<div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label class="text-xs text-[#8fa5c6]">PE 上限</label>
          <input v-model.number="store.filters.pe_max" type="number" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">PB 上限</label>
          <input v-model.number="store.filters.pb_max" type="number" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">ROE 最低%</label>
          <input v-model.number="store.filters.roe_min" type="number" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div class="flex items-end">
          <button @click="doScreen" :disabled="store.loading" class="bg-[#0052ff] text-white px-5 py-1.5 rounded-full text-sm font-medium hover:opacity-90 w-full">开始选股</button>
        </div>
      </div>

      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <h3 class="text-sm font-semibold text-white p-4 pb-2">选股结果 ({{ store.candidates.length }} 只)</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-[#8fa5c6]">
            <thead><tr class="border-b border-[#1a314a]">
              <th class="px-4 py-2 text-left">代码</th><th class="px-4 py-2 text-left">名称</th>
              <th class="px-4 py-2 text-right">PE</th><th class="px-4 py-2 text-right">PB</th>
              <th class="px-4 py-2 text-right">ROE</th><th class="px-4 py-2 text-right">得分</th>
            </tr></thead>
            <tbody>
              <tr v-for="c in store.candidates" :key="c.code" class="border-b border-[#1a314a] hover:bg-[#132438]">
                <td class="px-4 py-2 font-mono text-[#0052ff]">{{ c.code }}</td>
                <td class="px-4 py-2">{{ c.name }}</td>
                <td class="px-4 py-2 text-right font-mono">{{ c.pe.toFixed(1) }}</td>
                <td class="px-4 py-2 text-right font-mono">{{ c.pb.toFixed(1) }}</td>
                <td class="px-4 py-2 text-right font-mono">{{ c.roe.toFixed(1) }}%</td>
                <td class="px-4 py-2 text-right font-mono text-[#f59e0b]">{{ c.score }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 策略回测 -->
    <div v-show="tab==='backtest'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label class="text-xs text-[#8fa5c6]">股票代码</label>
          <input v-model="btCode" placeholder="600519" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">策略</label><br/>
          <select v-model="btStrategy" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]">
            <option value="ma_cross">双均线交叉</option>
            <option value="momentum">动量策略</option>
            <option value="grid">网格交易</option>
            <option value="mean_reversion">均值回归</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">开始日期</label>
          <input v-model="btStart" type="date" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div class="flex items-end">
          <button @click="doBacktest" :disabled="store.loading" class="bg-[#0052ff] text-white px-5 py-1.5 rounded-full text-sm font-medium hover:opacity-90 w-full">开始回测</button>
        </div>
      </div>

      <div v-if="store.backtestResult" class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        <div v-for="m in metrics" :key="m.key" class="bg-[#0f1a2e] border border-[#1a314a] rounded-lg p-3 text-center">
          <div class="text-xs text-[#8fa5c6] mb-1">{{ m.label }}</div>
          <div class="text-lg font-bold" :class="m.color(store.backtestResult[m.key])">{{ m.fmt(store.backtestResult[m.key]) }}</div>
        </div>
      </div>

      <!-- 净值曲线 -->
      <div v-if="store.backtestResult" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
        <h3 class="text-sm font-semibold text-white p-4 pb-2">净值曲线</h3>
        <div ref="navChartRef" class="w-full h-[250px] md:h-[300px]"></div>
      </div>

      <!-- 交易记录 -->
      <div v-if="store.backtestResult" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <h3 class="text-sm font-semibold text-white p-4 pb-2">交易记录 ({{ store.backtestResult.trade_count }} 笔)</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-[#8fa5c6]">
            <thead><tr class="border-b border-[#1a314a]">
              <th class="px-4 py-2 text-left">日期</th><th class="px-4 py-2 text-left">操作</th>
              <th class="px-4 py-2 text-right">价格</th><th class="px-4 py-2 text-right">数量</th><th class="px-4 py-2 text-right">盈亏</th>
            </tr></thead>
            <tbody>
              <tr v-for="(t,i) in store.backtestResult.trades" :key="i" class="border-b border-[#1a314a]" :class="t.action==='买入'?'bg-[#05b169]/10':'bg-[#cf202f]/10'">
                <td class="px-4 py-2 font-mono text-white">{{ t.date }}</td>
                <td class="px-4 py-2 font-medium" :class="t.action==='买入'?'text-[#05b169]':'text-[#cf202f]'">{{ t.action }}</td>
                <td class="px-4 py-2 text-right font-mono text-white">{{ typeof t.price==='number' ? t.price.toFixed(2) : t.price }}</td>
                <td class="px-4 py-2 text-right font-mono text-white">{{ t.shares }}</td>
                <td class="px-4 py-2 text-right font-mono" :class="(t.profit||0)>=0?'text-[#05b169]':'text-[#cf202f]'">{{ (t.profit||0)>=0?'+':'' }}{{ typeof t.profit==='number' ? t.profit.toFixed(2) : t.profit }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 策略对比 -->
    <div v-show="tab==='compare'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 space-y-3">
        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="text-xs text-[#8fa5c6]">股票代码</label>
            <input v-model="cmpCode" placeholder="600519" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
          </div>
          <div>
            <label class="text-xs text-[#8fa5c6]">开始日期</label>
            <input v-model="cmpStart" type="date" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
          </div>
          <div>
            <label class="text-xs text-[#8fa5c6]">结束日期</label>
            <input v-model="cmpEnd" type="date" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
          </div>
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">选择策略</label>
          <div class="flex flex-wrap gap-4 mt-1">
            <label v-for="s in store.strategies" :key="s.key" class="flex items-center gap-1.5 text-sm text-[#d0d8e8] cursor-pointer">
              <input type="checkbox" :value="s.key" v-model="cmpStrategies" class="accent-[#0052ff]" />
              {{ s.name }}
            </label>
          </div>
        </div>
        <div>
          <button @click="doCompare" :disabled="store.loading || cmpStrategies.length===0" class="bg-[#0052ff] text-white px-6 py-1.5 rounded-full text-sm font-medium hover:opacity-90 disabled:opacity-50">开始对比</button>
        </div>
      </div>

      <template v-if="store.compareResult">
        <!-- 对比指标表格 -->
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
          <h3 class="text-sm font-semibold text-white p-4 pb-2">
            对比指标 — {{ store.compareResult.code }} {{ store.compareResult.name }}
          </h3>
          <div class="overflow-x-auto">
            <table class="w-full text-xs text-[#8fa5c6]">
              <thead><tr class="border-b border-[#1a314a]">
                <th class="px-4 py-2 text-left">策略</th>
                <th class="px-4 py-2 text-right">总收益率</th>
                <th class="px-4 py-2 text-right">年化收益</th>
                <th class="px-4 py-2 text-right">最大回撤</th>
                <th class="px-4 py-2 text-right">夏普比率</th>
                <th class="px-4 py-2 text-right">胜率</th>
                <th class="px-4 py-2 text-right">交易次数</th>
              </tr></thead>
              <tbody>
                <tr v-for="r in store.compareResult.results" :key="r.strategy" class="border-b border-[#1a314a] hover:bg-[#132438]">
                  <td class="px-4 py-2 font-medium text-white">{{ r.strategy_name }}</td>
                  <td class="px-4 py-2 text-right font-mono" :class="isBest(r,'total_return')?'text-[#f59e0b] font-bold':'text-[#d0d8e8]'">{{ r.total_return.toFixed(1) }}%</td>
                  <td class="px-4 py-2 text-right font-mono" :class="isBest(r,'annual_return')?'text-[#f59e0b] font-bold':'text-[#d0d8e8]'">{{ r.annual_return.toFixed(1) }}%</td>
                  <td class="px-4 py-2 text-right font-mono" :class="isBestLow(r,'max_drawdown')?'text-[#f59e0b] font-bold':'text-[#d0d8e8]'">{{ r.max_drawdown.toFixed(1) }}%</td>
                  <td class="px-4 py-2 text-right font-mono" :class="isBest(r,'sharpe')?'text-[#f59e0b] font-bold':'text-[#d0d8e8]'">{{ r.sharpe.toFixed(2) }}</td>
                  <td class="px-4 py-2 text-right font-mono" :class="isBest(r,'win_rate')?'text-[#f59e0b] font-bold':'text-[#d0d8e8]'">{{ r.win_rate.toFixed(1) }}%</td>
                  <td class="px-4 py-2 text-right font-mono text-[#d0d8e8]">{{ r.trade_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 叠加净值曲线 -->
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
          <h3 class="text-sm font-semibold text-white p-4 pb-2">叠加净值曲线</h3>
          <div ref="cmpChartRef" class="w-full h-[250px] md:h-[300px]"></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { useStockPickStore } from "../stores/stockPick";
import * as echarts from "echarts";

const store = useStockPickStore();
const screenMode = ref("simple");
const tab = ref("screen");
const btCode = ref("600519");
const btStrategy = ref("ma_cross");
const btStart = ref("2025-01-01");
const btParams = ref({
  ma_short: 5,
  ma_long: 20,
  momentum_days: 20,
  grid_count: 10,
  boll_period: 20,
});

// 对比相关
const cmpCode = ref("600519");
const cmpStart = ref("2025-01-01");
const cmpEnd = ref("2026-06-08");
const cmpStrategies = ref<string[]>(["ma_cross", "momentum", "mean_reversion"]);

const navChartRef = ref<HTMLDivElement>();
let navChart: echarts.ECharts | null = null;
const cmpChartRef = ref<HTMLDivElement>();
let cmpChart: echarts.ECharts | null = null;

const tabs = [
  { key: "screen", label: "多因子选股" },
  { key: "backtest", label: "策略回测" },
  { key: "compare", label: "策略对比" },
];

const metrics = [
  { key: "total_return", label: "总收益率", fmt: (v:number)=>v.toFixed(1)+"%", color: (v:number)=>v>=0?"text-[#05b169]":"text-[#cf202f]" },
  { key: "annual_return", label: "年化收益", fmt: (v:number)=>v.toFixed(1)+"%", color: (v:number)=>v>=0?"text-[#05b169]":"text-[#cf202f]" },
  { key: "max_drawdown", label: "最大回撤", fmt: (v:number)=>v.toFixed(1)+"%", color: ()=> "text-[#cf202f]" },
  { key: "sharpe", label: "夏普比率", fmt: (v:number)=>v.toFixed(2), color: ()=> "text-[#f59e0b]" },
  { key: "win_rate", label: "胜率", fmt: (v:number)=>v.toFixed(1)+"%", color: (v:number)=>v>50?"text-[#05b169]":"text-[#cf202f]" },
];

const compareColors = ["#4a90d9", "#05b169", "#cf202f", "#f59e0b", "#a855f7", "#06b6d4"];

function doScreen() { store.screen({ ...store.filters.value, mode: screenMode.value }); }
function doBacktest() { store.runBacktest({ code: btCode.value, strategy: btStrategy.value, start_date: btStart.value, end_date: "2026-06-08", ...btParams.value }); }
function doCompare() {
  store.runCompare({ code: cmpCode.value, strategies: cmpStrategies.value, start_date: cmpStart.value, end_date: cmpEnd.value });
}

// 对比表格：标记最优值（越高越好）
function isBest(r: any, key: string): boolean {
  const results = store.compareResult?.results;
  if (!results) return false;
  const best = Math.max(...results.map((x: any) => x[key]));
  return r[key] === best && results.length > 1;
}
// 对比表格：回撤越低越好
function isBestLow(r: any, key: string): boolean {
  const results = store.compareResult?.results;
  if (!results) return false;
  const best = Math.min(...results.map((x: any) => x[key]));
  return r[key] === best && results.length > 1;
}

function renderNavChart() {
  if (!navChart || !navChartRef.value) return;
  const result = store.backtestResult;
  if (!result || !result.nav_curve || !result.nav_curve.length) return;
  const dates = result.nav_curve.map((d: any) => d.date);
  const navs = result.nav_curve.map((d: any) => d.nav);

  navChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "#132438",
      borderColor: "#1a314a",
      textStyle: { color: "#f0f4f8", fontSize: 11 },
      formatter: (params: any) => {
        const p = params[0];
        return p.axisValue + "<br/>净值: " + p.value.toFixed(4);
      },
    },
    grid: { left: "3%", right: "4%", top: "8%", bottom: "5%", containLabel: true },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "#1a314a" } },
      axisLabel: { color: "#8899aa", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: "净值",
      nameTextStyle: { color: "#8fa5c6", fontSize: 10 },
      axisLabel: { color: "#8899aa", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1a314a" } },
    },
    series: [
      {
        name: "净值",
        type: "line",
        data: navs,
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#4a90d9", width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(74,144,217,0.3)" },
            { offset: 1, color: "rgba(74,144,217,0.02)" },
          ]),
        },
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "rgba(245,158,11,0.6)", type: "dashed", width: 1 },
          data: [{ yAxis: 1.0, label: { formatter: "初始净值 1.0", color: "#f59e0b", fontSize: 10 } }],
        },
      },
    ],
  }, true);
}

function renderCmpChart() {
  if (!cmpChart || !cmpChartRef.value) return;
  const result = store.compareResult;
  if (!result || !result.results || !result.results.length) return;

  const dateSet = new Set<string>();
  result.results.forEach((r: any) => r.nav_curve?.forEach((d: any) => dateSet.add(d.date)));
  const dates = Array.from(dateSet).sort();

  const series = result.results.map((r: any, i: number) => {
    const dateNavMap: Record<string, number> = {};
    r.nav_curve?.forEach((d: any) => { dateNavMap[d.date] = d.nav; });
    return {
      name: r.strategy_name,
      type: "line",
      data: dates.map(d => dateNavMap[d] ?? null),
      smooth: true,
      symbol: "none",
      lineStyle: { color: compareColors[i % compareColors.length], width: 2 },
    };
  });

  cmpChart.setOption({
    backgroundColor: "transparent",
    legend: {
      data: result.results.map((r: any) => r.strategy_name),
      textStyle: { color: "#8fa5c6", fontSize: 11 },
      top: 4,
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#132438",
      borderColor: "#1a314a",
      textStyle: { color: "#f0f4f8", fontSize: 11 },
    },
    grid: { left: "3%", right: "4%", top: "12%", bottom: "5%", containLabel: true },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "#1a314a" } },
      axisLabel: { color: "#8899aa", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: "净值",
      nameTextStyle: { color: "#8fa5c6", fontSize: 10 },
      axisLabel: { color: "#8899aa", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1a314a" } },
    },
    series: [
      ...series,
      {
        name: "参考线",
        type: "line",
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "rgba(245,158,11,0.6)", type: "dashed", width: 1 },
          data: [{ yAxis: 1.0, label: { formatter: "基准 1.0", color: "#f59e0b", fontSize: 10 } }],
        },
        data: [],
      },
    ],
  }, true);
}

watch(() => store.backtestResult, () => { nextTick(() => renderNavChart()); });
watch(() => store.compareResult, () => { nextTick(() => { renderCmpChart(); }); });

onMounted(() => {
  store.loadStrategies();
  nextTick(() => {
    if (navChartRef.value) {
      navChart = echarts.init(navChartRef.value);
      window.addEventListener("resize", () => navChart?.resize());
      renderNavChart();
    }
    if (cmpChartRef.value) {
      cmpChart = echarts.init(cmpChartRef.value);
    }
  });
});

onUnmounted(() => {
  navChart?.dispose();
  cmpChart?.dispose();
});
</script>



