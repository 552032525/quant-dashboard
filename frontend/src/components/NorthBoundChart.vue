<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-2">北向资金净买入趋势</h3>
    <div ref="chartRef" class="w-full" style="height:260px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any; daily?: any }>();
const chartRef = ref<HTMLElement>();
let chart: echarts.ECharts | null = null;

function render() {
  if (!chartRef.value) return;
  if (!chart) chart = echarts.init(chartRef.value);

  const items = props.data?.items || [];
  if (!items.length) {
    chart.setOption({
      title: { text: "暂无北向资金数据", left: "center", top: "center", textStyle: { color: "#8fa5c6", fontSize: 14 } },
    });
    return;
  }

  const dates = items.map((f: any) => f.date);
  const shNet = items.map((f: any) => f.sh_net);
  const szNet = items.map((f: any) => f.sz_net);
  const totalNet = items.map((f: any) => f.total_net);

  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["沪股通", "深股通", "合计"], textStyle: { color: "#8fa5c6" }, top: 0 },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: { type: "category", data: dates, axisLabel: { color: "#8fa5c6", rotate: 30 } },
    yAxis: { type: "value", name: "亿元", axisLabel: { color: "#8fa5c6" } },
    series: [
      {
        name: "沪股通", type: "bar", data: shNet, barGap: 0,
        itemStyle: { color: "#ef4444" },
      },
      {
        name: "深股通", type: "bar", data: szNet,
        itemStyle: { color: "#3b82f6" },
      },
      {
        name: "合计", type: "line", data: totalNet, showSymbol: false,
        itemStyle: { color: "#f59e0b" }, lineStyle: { width: 2 },
      },
    ],
  });
}

watch(() => props.data, () => nextTick(render), { deep: true });
onMounted(() => nextTick(render));
</script>
