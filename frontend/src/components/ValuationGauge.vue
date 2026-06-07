<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-3">估值概览</h3>
    <div class="grid grid-cols-2 gap-3">
      <div v-for="item in items" :key="item.label" class="text-center p-2 rounded bg-[#162436]">
        <div class="text-xs text-blue-300">{{ item.label }}</div>
        <div class="text-lg font-bold" :class="item.color">{{ item.value }}</div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ valuation: any }>();
const items = computed(() => {
  const v = props.valuation;
  if (!v) return [];
  const peColor = v.pe < 15 ? "text-green-400" : v.pe < 30 ? "text-yellow-400" : "text-red-400";
  const pbColor = v.pb < 2 ? "text-green-400" : v.pb < 5 ? "text-yellow-400" : "text-red-400";
  return [
    { label: "市盈率(PE)", value: v.pe?.toFixed(1) || "-", color: peColor },
    { label: "市净率(PB)", value: v.pb?.toFixed(1) || "-", color: pbColor },
    { label: "市销率(PS)", value: v.ps?.toFixed(1) || "-", color: "text-blue-300" },
    { label: "ROE(%)", value: v.roe?.toFixed(1) || "-", color: v.roe > 15 ? "text-green-400" : "text-yellow-400" },
    { label: "股息率(%)", value: v.dividend_yield?.toFixed(2) || "-", color: "text-blue-300" },
    { label: "行业PE", value: v.industry_pe?.toFixed(1) || "-", color: "text-gray-400" },
  ];
});
</script>
