<template>
  <div class="p-3 md:p-6 max-w-7xl mx-auto h-full overflow-auto">
    <div class="flex flex-col md:flex-row items-start md:items-center justify-between mb-4 gap-3">
      <h2 class="text-xl font-semibold text-white">📊 收益统计</h2>
      <div class="flex items-center gap-3">
        <div class="flex flex-wrap gap-1 bg-[#0f1a2e] rounded-lg p-1">
          <button v-for="r in ranges" :key="r.key" @click="range=r.key; loadData()"
            :class="range===r.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'"
            class="px-3 py-1 rounded-md text-xs transition-colors">{{ r.label }}</button>
        </div>
        <button @click="snapshot" :disabled="snapping"
          class="bg-[#0052ff] text-white px-4 py-1.5 rounded-full text-xs font-medium hover:opacity-90 disabled:opacity-50">
          {{ snapping ? '快照中...' : '📸 手动快照' }}
        </button>
      </div>
    </div>

    <div v-if="store.error" class="text-xs text-[#cf202f] mb-4 px-3 py-2 bg-[#cf202f]/10 rounded-lg">{{ store.error }}</div>
    <div v-if="snapMsg" class="text-xs mb-4 px-3 py-2 rounded-lg" :class="snapOk?'text-[#05b169] bg-[#05b169]/10':'text-[#f59e0b] bg-[#f59e0b]/10'">{{ snapMsg }}</div>

    <!-- 最新统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6" v-if="store.latest">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
        <div class="text-xs text-[#8fa5c6] mb-1">总资产</div>
        <div class="text-lg font-bold text-white font-mono">{{ fmtNum(store.latest.total_assets) }}</div>
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
        <div class="text-xs text-[#8fa5c6] mb-1">日收益</div>
        <div class="text-lg font-bold font-mono" :class="store.latest.daily_profit>=0?'text-[#05b169]':'text-[#cf202f]'">
          {{ store.latest.daily_profit>=0?'+':'' }}{{ fmtNum(store.latest.daily_profit) }}
        </div>
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
        <div class="text-xs text-[#8fa5c6] mb-1">累计收益</div>
        <div class="text-lg font-bold font-mono" :class="store.latest.cumulative_profit>=0?'text-[#05b169]':'text-[#cf202f]'">
          {{ store.latest.cumulative_profit>=0?'+':'' }}{{ fmtNum(store.latest.cumulative_profit) }}
        </div>
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
        <div class="text-xs text-[#8fa5c6] mb-1">日收益率</div>
        <div class="text-lg font-bold font-mono" :class="store.latest.daily_profit_pct>=0?'text-[#05b169]':'text-[#cf202f]'">
          {{ store.latest.daily_profit_pct>=0?'+':'' }}{{ (store.latest.daily_profit_pct||0).toFixed(2) }}%
        </div>
      </div>
    </div>

    <!-- ECharts 图表 -->
    <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 mb-6">
      <h3 class="text-sm font-medium text-[#8fa5c6] mb-3">收益走势</h3>
      <div v-if="store.loading" class="text-center text-[#8fa5c6] py-20 text-sm">加载中...</div>
      <div v-else-if="!store.dailyStats.length" class="text-center text-[#8fa5c6] py-20 text-sm">暂无数据，请先创建快照</div>
      <div ref="chartRef" v-else class="w-full" style="height:360px"></div>
    </div>

    <!-- 历史统计表格 -->
    <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
      <div class="px-4 py-3 border-b border-[#1a314a]">
        <h3 class="text-sm font-medium text-[#8fa5c6]">历史记录</h3>
      </div>
      <div v-if="!store.dailyStats.length" class="text-center text-[#8fa5c6] py-10 text-sm">暂无数据</div>
      <table v-else class="w-full text-sm">
        <thead><tr class="border-b border-[#1a314a] text-[#8fa5c6] text-xs uppercase">
          <th class="text-left px-4 py-3">日期</th>
          <th class="text-right px-4 py-3">总资产</th>
          <th class="text-right px-4 py-3">日收益</th>
          <th class="text-right px-4 py-3">累计收益</th>
          <th class="text-right px-4 py-3">日收益率</th>
        </tr></thead>
        <tbody>
          <tr v-for="(d,i) in store.dailyStats" :key="d.date||i" class="border-b border-[#1a314a] hover:bg-[#132438] transition-colors">
            <td class="px-4 py-2.5 font-mono text-white">{{ d.date }}</td>
            <td class="px-4 py-2.5 text-right font-mono text-white">{{ fmtNum(d.total_assets) }}</td>
            <td class="px-4 py-2.5 text-right font-mono" :class="d.daily_profit>=0?'text-[#05b169]':'text-[#cf202f]'">
              {{ d.daily_profit>=0?'+':'' }}{{ fmtNum(d.daily_profit) }}
            </td>
            <td class="px-4 py-2.5 text-right font-mono" :class="d.cumulative_profit>=0?'text-[#05b169]':'text-[#cf202f]'">
              {{ d.cumulative_profit>=0?'+':'' }}{{ fmtNum(d.cumulative_profit) }}
            </td>
            <td class="px-4 py-2.5 text-right font-mono" :class="(d.daily_profit_pct||0)>=0?'text-[#05b169]':'text-[#cf202f]'">
              {{ (d.daily_profit_pct||0)>=0?'+':'' }}{{ (d.daily_profit_pct||0).toFixed(2) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
import * as echarts from "echarts";
import { useStatsStore } from "../stores/stats";

const store = useStatsStore();
const chartRef = ref<HTMLDivElement>();
let chart: echarts.ECharts | null = null;

const ranges = [
  { key: "7d", label: "近7天" },
  { key: "30d", label: "近30天" },
  { key: "90d", label: "近90天" },
  { key: "all", label: "全部" },
];
const range = ref("30d");

const snapping = ref(false);
const snapMsg = ref("");
const snapOk = ref(true);
let snapTimer: ReturnType<typeof setTimeout> | null = null;

function showSnapMsg(msg: string, ok: boolean) {
  snapMsg.value = msg; snapOk.value = ok;
  if (snapTimer) clearTimeout(snapTimer);
  snapTimer = setTimeout(() => { snapMsg.value = ""; }, 4000);
}

function getRangeDates(): { start?: string; end?: string } {
  if (range.value === "all") return {};
  const days = { "7d": 7, "30d": 30, "90d": 90 }[range.value] || 30;
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

function fmtNum(v: number | null | undefined): string {
  if (v == null) return "--";
  return v.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function loadData() {
  await store.fetchLatest();
  const { start, end } = getRangeDates();
  await store.fetchDaily(start, end);
  await nextTick();
  renderChart();
}

async function snapshot() {
  snapping.value = true;
  try {
    await store.createSnapshot();
    showSnapMsg("快照创建成功", true);
    await nextTick();
    renderChart();
  } catch {
    showSnapMsg(store.error || "快照失败", false);
  } finally {
    snapping.value = false;
  }
}

function renderChart() {
  if (!chart || !chartRef.value || !store.dailyStats.length) return;
  const data = store.dailyStats;
  const dates = data.map((d: any) => d.date);
  const assets = data.map((d: any) => d.total_assets);
  const dailyReturns = data.map((d: any) => d.daily_profit || 0);

  chart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "#132438",
      borderColor: "#1a314a",
      textStyle: { color: "#f0f4f8" },
    },
    legend: {
      data: ["总资产", "日收益"],
      textStyle: { color: "#8fa5c6", fontSize: 11 },
      top: 0,
    },
    grid: { left: "3%", right: "4%", top: "15%", bottom: "5%", containLabel: true },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "#1a314a" } },
      axisLabel: { color: "#8899aa", fontSize: 10 },
    },
    yAxis: [
      {
        type: "value",
        name: "总资产",
        nameTextStyle: { color: "#8fa5c6", fontSize: 10 },
        axisLabel: { color: "#8899aa", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1a314a" } },
      },
      {
        type: "value",
        name: "日收益",
        nameTextStyle: { color: "#8fa5c6", fontSize: 10 },
        axisLabel: { color: "#8899aa", fontSize: 10 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "总资产",
        type: "line",
        data: assets,
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#4a90d9", width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(74,144,217,0.25)" },
            { offset: 1, color: "rgba(74,144,217,0.02)" },
          ]),
        },
      },
      {
        name: "日收益",
        type: "bar",
        yAxisIndex: 1,
        data: dailyReturns,
        itemStyle: {
          color: (params: any) => (params.value >= 0 ? "#05b169" : "#cf202f"),
        },
      },
    ],
  }, true);
}

watch(() => store.dailyStats, () => { nextTick(() => renderChart()); });

onMounted(async () => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value);
    window.addEventListener("resize", () => chart?.resize());
  }
  await loadData();
});

onUnmounted(() => chart?.dispose());
</script>
