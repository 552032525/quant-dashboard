<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-2">板块资金排名</h3>
    <div ref="chartRef" class="w-full" style="height:340px"></div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any }>();
const chartRef = ref<HTMLElement>();
let chart: echarts.ECharts | null = null;

function render() {
  if (!chartRef.value) return;
  if (!chart) chart = echarts.init(chartRef.value);

  const inflow = props.data?.inflow_top10 || [];
  const outflow = props.data?.outflow_top10 || [];

  if (!inflow.length && !outflow.length) {
    chart.setOption({
      title: { text: "暂无板块资金数据", left: "center", top: "center", textStyle: { color: "#8fa5c6", fontSize: 14 } },
    });
    return;
  }

  const all = [...inflow, ...outflow];
  const names = all.map((s: any) => s.name.length > 6 ? s.name.slice(0, 6) + "..." : s.name);
  const amounts = all.map((s: any) => s.net_amount);

  chart.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 100, right: 30, top: 10, bottom: 20 },
    xAxis: { type: "value", name: "万元", axisLabel: { color: "#8fa5c6" } },
    yAxis: { type: "category", data: names, inverse: true, axisLabel: { color: "#8fa5c6" } },
    series: [{
      type: "bar", data: amounts,
      itemStyle: {
        color: (p: any) => {
          const idx = p.dataIndex;
          return idx < inflow.length ? "#ef4444" : "#22c55e";
        },
      },
      label: { show: true, position: "right", color: "#8fa5c6", fontSize: 10,
        formatter: (p: any) => (p.value / 10000).toFixed(1) + "亿" },
    }],
  });
}

watch(() => props.data, () => nextTick(render), { deep: true });
onMounted(() => nextTick(render));
</script>
