<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-3">
      风险筛查
      <span class="ml-2 px-2 py-0.5 rounded text-xs" :class="riskClass">{{ risk?.risk_level }}风险</span>
    </h3>
    <div class="space-y-2">
      <div class="flex justify-between text-xs">
        <span class="text-blue-300">资产负债率</span>
        <span :class="risk?.debt_ratio > 70 ? 'text-red-400' : 'text-green-400'">{{ risk?.debt_ratio?.toFixed(1) }}%</span>
      </div>
      <div class="flex justify-between text-xs">
        <span class="text-blue-300">质押比例</span>
        <span :class="risk?.pledge_ratio > 30 ? 'text-red-400' : 'text-green-400'">{{ risk?.pledge_ratio?.toFixed(1) }}%</span>
      </div>
      <div class="flex justify-between text-xs">
        <span class="text-blue-300">商誉占比</span>
        <span :class="risk?.goodwill_ratio > 10 ? 'text-yellow-400' : 'text-green-400'">{{ risk?.goodwill_ratio?.toFixed(1) }}%</span>
      </div>
      <div class="flex justify-between text-xs">
        <span class="text-blue-300">现金流健康度</span>
        <span :class="risk?.cash_flow_health === '健康' ? 'text-green-400' : risk?.cash_flow_health === '预警' ? 'text-red-400' : 'text-yellow-400'">{{ risk?.cash_flow_health }}</span>
      </div>
      <div v-if="risk?.risk_items?.length" class="mt-2 pt-2 border-t border-[#1a314a]">
        <div v-for="(item, i) in risk.risk_items" :key="i" class="text-xs text-yellow-400 flex items-start gap-1">
          <span>!</span><span>{{ item }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";
const props = defineProps<{ risk: any }>();
const riskClass = computed(() => {
  if (!props.risk) return "";
  if (props.risk.risk_level === "高") return "bg-red-500/20 text-red-400";
  if (props.risk.risk_level === "中") return "bg-yellow-500/20 text-yellow-400";
  return "bg-green-500/20 text-green-400";
});
</script>
