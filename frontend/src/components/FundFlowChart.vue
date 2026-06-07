<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-2">资金流向趋势 (主力净流入)</h3>
    <div ref="chartRef" class="w-full" style="height:280px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any }>();
const chartRef = ref<HTMLElement>();
let chart: echarts.ECharts | null = null;

function render() {
  if (!chartRef.value || !props.data?.flows?.length) return;
  if (!chart) chart = echarts.init(chartRef.value);
  const flows = props.data.flows;
  const dates = flows.map((f: any) => f.date);
  const mainNet = flows.map((f: any) => f.main_net);
  const superLarge = flows.map((f: any) => f.super_large_net);

  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["主力净流入", "超大单"], textStyle: { color: "#8fa5c6" }, top: 0 },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: { type: "category", data: dates, axisLabel: { color: "#8fa5c6", rotate: 30 } },
    yAxis: { type: "value", name: "万元", axisLabel: { color: "#8fa5c6" } },
    series: [
      {
        name: "主力净流入", type: "bar", data: mainNet,
        itemStyle: { color: (p: any) => p.value >= 0 ? "#ef4444" : "#22c55e" },
      },
      {
        name: "超大单", type: "line", data: superLarge, showSymbol: false,
        itemStyle: { color: "#f59e0b" },
      },
    ],
  });
}

watch(() => props.data, () => nextTick(render), { deep: true });
onMounted(() => nextTick(render));
</script>
