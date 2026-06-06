<template>
  <div ref="chartRef" class="w-full h-full"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any[]; period?: string }>();
const chartRef = ref<HTMLDivElement>();
let chart: echarts.ECharts | null = null;

function calcMA(data: any[], period: number) {
  const r: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) { r.push(null); continue; }
    let s = 0;
    for (let j = 0; j < period; j++) s += data[i - j].close;
    r.push(+(s / period).toFixed(2));
  }
  return r;
}

function buildIntradayOption(data: any[]) {
  const dates = data.map((d) => d.date);
  return {
    backgroundColor: "transparent",
    grid: [
      { left: "3%", right: "3%", top: "5%", height: "60%" },
      { left: "3%", right: "3%", top: "72%", height: "20%" },
    ],
    xAxis: [
      { type: "category", data: dates, axisLine: { lineStyle: { color: "#1a314a" } }, axisLabel: { color: "#8899aa", fontSize: 10, interval: Math.floor(dates.length / 6) } },
      { type: "category", gridIndex: 1, data: dates, axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false } },
    ],
    yAxis: [
      { type: "value", axisLine: { show: false }, axisLabel: { color: "#8899aa", fontSize: 10 }, splitLine: { lineStyle: { color: "#1a314a" } } },
      { type: "value", gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } },
    ],
    series: [
      { name: "价格", type: "line", data: data.map((d) => d.close), lineStyle: { color: "#4a90d9", width: 1.5 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(74,144,217,0.3)" }, { offset: 1, color: "rgba(74,144,217,0.02)" }]) }, symbol: "none", smooth: true },
      { name: "量", type: "bar", xAxisIndex: 1, yAxisIndex: 1, data: data.map((d) => d.volume), itemStyle: { color: "#4a90d9" } },
    ],
    tooltip: { trigger: "axis", backgroundColor: "#132438", borderColor: "#1a314a", textStyle: { color: "#f0f4f8" } },
  };
}

function buildOption(data: any[]) {
  const dates = data.map((d) => d.date);
  const ma5 = calcMA(data, 5);
  const ma10 = calcMA(data, 10);
  const ma20 = calcMA(data, 20);
  return {
    backgroundColor: "transparent",
    grid: [
      { left: "3%", right: "3%", top: "5%", height: "60%" },
      { left: "3%", right: "3%", top: "72%", height: "20%" },
    ],
    xAxis: [
      { type: "category", data: dates, axisLine: { lineStyle: { color: "#1a314a" } }, axisLabel: { color: "#8899aa", fontSize: 10 } },
      { type: "category", gridIndex: 1, data: dates, axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false } },
    ],
    yAxis: [
      { type: "value", axisLine: { show: false }, axisLabel: { color: "#8899aa", fontSize: 10 }, splitLine: { lineStyle: { color: "#1a314a" } } },
      { type: "value", gridIndex: 1, axisLabel: { show: false }, splitLine: { show: false } },
    ],
    series: [
      { name: "K线", type: "candlestick", data: data.map((d) => [d.open, d.close, d.low, d.high]), itemStyle: { color: "#05b169", color0: "#cf202f", borderColor: "#05b169", borderColor0: "#cf202f" } },
      { name: "MA5", type: "line", data: ma5, smooth: true, lineStyle: { color: "#f5a623", width: 1 }, symbol: "none" },
      { name: "MA10", type: "line", data: ma10, smooth: true, lineStyle: { color: "#4a90d9", width: 1 }, symbol: "none" },
      { name: "MA20", type: "line", data: ma20, smooth: true, lineStyle: { color: "#e066ff", width: 1 }, symbol: "none" },
      { name: "量", type: "bar", xAxisIndex: 1, yAxisIndex: 1, data: data.map((d) => d.volume), itemStyle: { color: (params: any) => { const i = params.dataIndex; return data[i]?.close >= data[i]?.open ? "#05b169" : "#cf202f"; } } },
    ],
    tooltip: { trigger: "axis", backgroundColor: "#132438", borderColor: "#1a314a", textStyle: { color: "#f0f4f8" } },
  };
}

onMounted(() => {
  if (chartRef.value) { chart = echarts.init(chartRef.value); render(); window.addEventListener("resize", () => chart?.resize()); }
});
watch(() => [props.data, props.period], render);
function render() {
  if (!chart || !props.data.length) return;
  const opt = props.period === "intraday" ? buildIntradayOption(props.data) : buildOption(props.data);
  chart.setOption(opt, true);
}
onUnmounted(() => chart?.dispose());
</script>