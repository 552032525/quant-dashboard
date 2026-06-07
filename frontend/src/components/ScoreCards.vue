<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-3">量化评分</h3>
    <div v-if="score" class="space-y-3">
      <div class="grid grid-cols-4 gap-2 text-center">
        <div v-for="item in cardItems" :key="item.key" class="p-2 rounded bg-[#162436]">
          <div class="text-xs text-blue-300">{{ item.label }}</div>
          <div class="text-lg font-bold" :class="item.color">{{ item.value }}</div>
          <div class="text-xs text-gray-500">/20</div>
        </div>
      </div>
      <div class="flex items-center justify-between px-2">
        <span class="text-sm text-white font-semibold">综合评分</span>
        <span class="text-2xl font-bold" :class="totalColor">{{ score.total }}</span>
      </div>
      <div class="text-xs text-blue-300 text-center">{{ score.description }}</div>
    </div>
    <div v-else class="text-center py-4 text-gray-500 text-xs">暂无评分数据</div>
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ score: any }>();

const cardItems = computed(() => {
  if (!props.score) return [];
  const s = props.score;
  return [
    { key: "trend", label: "趋势", value: s.trend, color: s.trend >= 15 ? "text-green-400" : s.trend >= 10 ? "text-yellow-400" : "text-red-400" },
    { key: "momentum", label: "动量", value: s.momentum, color: s.momentum >= 15 ? "text-green-400" : s.momentum >= 10 ? "text-yellow-400" : "text-red-400" },
    { key: "volatility", label: "波动", value: s.volatility, color: s.volatility >= 15 ? "text-green-400" : "text-yellow-400" },
    { key: "volume_score", label: "量能", value: s.volume_score, color: s.volume_score >= 15 ? "text-green-400" : s.volume_score >= 10 ? "text-yellow-400" : "text-red-400" },
  ];
});

const totalColor = computed(() => {
  if (!props.score) return "text-gray-400";
  const t = props.score.total;
  if (t >= 70) return "text-green-400";
  if (t >= 40) return "text-yellow-400";
  return "text-red-400";
});
</script>
