<template>
  <div class="grid grid-cols-2 gap-4">
    <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
      <h3 class="text-sm font-semibold text-white mb-2">RSI</h3>
      <div ref="rsiRef" class="w-full" style="height:160px"></div>
    </div>
    <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
      <h3 class="text-sm font-semibold text-white mb-2">KDJ (9,3,3)</h3>
      <div ref="kdjRef" class="w-full" style="height:160px"></div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps<{ data: any }>();
const rsiRef = ref<HTMLElement>();
const kdjRef = ref<HTMLElement>();
let rsiChart: echarts.ECharts | null = null;
let kdjChart: echarts.ECharts | null = null;

function render() {
  if (!props.data) return;
  const dates = props.data.dates || [];
  
  if (rsiRef.value) {
    if (!rsiChart) rsiChart = echarts.init(rsiRef.value);
    rsiChart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["RSI6","RSI12","RSI24"], textStyle: { color: "#8fa5c6" } },
      grid: { left: 40, right: 10, top: 20, bottom: 25 },
      xAxis: { type: "category", data: dates, axisLabel: { color: "#8fa5c6", show: false } },
      yAxis: { type: "value", min: 0, max: 100, axisLabel: { color: "#8fa5c6" } },
      series: [
        { name: "RSI6", type: "line", data: props.data.rsi6, itemStyle: { color: "#f59e0b" }, showSymbol: false },
        { name: "RSI12", type: "line", data: props.data.rsi12, itemStyle: { color: "#3b82f6" }, showSymbol: false },
        { name: "RSI24", type: "line", data: props.data.rsi24, itemStyle: { color: "#a855f7" }, showSymbol: false },
      ],
    });
  }

  if (kdjRef.value) {
    if (!kdjChart) kdjChart = echarts.init(kdjRef.value);
    kdjChart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["K","D","J"], textStyle: { color: "#8fa5c6" } },
      grid: { left: 40, right: 10, top: 20, bottom: 25 },
      xAxis: { type: "category", data: dates, axisLabel: { color: "#8fa5c6", show: false } },
      yAxis: { type: "value", min: 0, max: 100, axisLabel: { color: "#8fa5c6" } },
      series: [
        { name: "K", type: "line", data: props.data.kdj_k, itemStyle: { color: "#f59e0b" }, showSymbol: false },
        { name: "D", type: "line", data: props.data.kdj_d, itemStyle: { color: "#3b82f6" }, showSymbol: false },
        { name: "J", type: "line", data: props.data.kdj_j, itemStyle: { color: "#ef4444" }, showSymbol: false },
      ],
    });
  }
}

watch(() => props.data, () => nextTick(render), { deep: true });
onMounted(() => nextTick(render));
</script>
