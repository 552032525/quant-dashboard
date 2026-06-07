<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-2">MACD (12,26,9)</h3>
    <div ref="chartRef" class="w-full" style="height:180px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any }>();
const chartRef = ref<HTMLElement>();
let chart: echarts.ECharts | null = null;

function render() {
  if (!chartRef.value || !props.data) return;
  if (!chart) chart = echarts.init(chartRef.value);
  const dates = props.data.dates || [];
  const dif = props.data.macd_dif || [];
  const dea = props.data.macd_dea || [];
  const bar = props.data.macd_bar || [];
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["DIF", "DEA", "BAR"], textStyle: { color: "#8fa5c6" } },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: "category", data: dates, axisLabel: { color: "#8fa5c6" } },
    yAxis: { type: "value", axisLabel: { color: "#8fa5c6" } },
    series: [
      { name: "DIF", type: "line", data: dif, itemStyle: { color: "#f59e0b" }, showSymbol: false },
      { name: "DEA", type: "line", data: dea, itemStyle: { color: "#3b82f6" }, showSymbol: false },
      { name: "BAR", type: "bar", data: bar.map((v: number, i: number) => v >= 0 ? v : v), 
        itemStyle: { color: (p: any) => p.value >= 0 ? "#ef4444" : "#22c55e" } },
    ],
  });
}

watch(() => props.data, () => nextTick(render), { deep: true });
onMounted(() => nextTick(render));
</script>
