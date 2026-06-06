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
  const max = Math.max(...data.map((d: any) => Math.abs(d.change_pct)), 0.01);
  return {
    tooltip: {
      formatter: (p: any) => `${p.name}<br/>涨跌幅: ${p.data.change_pct > 0 ? '+' : ''}${p.data.change_pct}%`,
    },
    series: [{
      type: "treemap", roam: false, nodeClick: false,
      width: "100%", height: "100%",
      data: data.map((d: any) => ({
        name: d.name.substring(0, 6),
        value: Math.abs(d.change_pct) + 0.01,
        change_pct: d.change_pct,
        itemStyle: {
          color: d.change_pct >= 0
            ? `rgba(5, 177, 105, ${0.3 + Math.abs(d.change_pct) / max * 0.7})`
            : `rgba(207, 32, 47, ${0.3 + Math.abs(d.change_pct) / max * 0.7})`,
        },
      })),
      levels: [{ itemStyle: { borderColor: "#0d1b2a", borderWidth: 1, gapWidth: 1 } }],
      label: { show: true, fontSize: 9, color: "#8899aa",
        formatter: (p: any) => `${p.name}\n${p.data.change_pct > 0 ? '+' : ''}${p.data.change_pct}%` },
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