<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-3">核心财务趋势（亿元）</h3>
    <div ref="chartRef" class="w-full" style="height:300px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any[] }>();
const chartRef = ref<HTMLElement>();
let chart: echarts.ECharts | null = null;

function render() {
  if (!chartRef.value || !props.data?.length) return;
  if (!chart) chart = echarts.init(chartRef.value);
  const dates = props.data.map((d: any) => d.date);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["营业总收入", "净利润", "现金流"], textStyle: { color: "#8fa5c6" } },
    grid: { left: 60, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: dates, axisLabel: { color: "#8fa5c6", rotate: 45 } },
    yAxis: { type: "value", axisLabel: { color: "#8fa5c6" } },
    series: [
      { name: "营业总收入", type: "bar", data: props.data.map((d: any) => d.revenue), itemStyle: { color: "#3b82f6" } },
      { name: "净利润", type: "line", data: props.data.map((d: any) => d.net_profit), itemStyle: { color: "#22c55e" } },
      { name: "现金流", type: "line", data: props.data.map((d: any) => d.cash_flow), itemStyle: { color: "#f59e0b" } },
    ],
  });
}

watch(() => props.data, () => nextTick(render), { deep: true });
onMounted(() => nextTick(render));
</script>
