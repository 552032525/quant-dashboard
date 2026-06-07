<template>
  <div class="space-y-2">
    <div v-for="section in sections" :key="section.title" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
      <div @click="section.open = !section.open" class="flex items-center justify-between p-3 cursor-pointer hover:bg-[#162436]">
        <span class="text-sm text-white font-semibold">{{ section.title }}</span>
        <span class="text-xs text-blue-300">{{ section.open ? '收起' : '展开' }}</span>
      </div>
      <div v-if="section.open" class="px-3 pb-3">
        <div v-for="item in section.items" :key="item.label" class="flex justify-between text-xs py-1 border-b border-[#1a314a] last:border-0">
          <span class="text-blue-300">{{ item.label }}</span>
          <span class="text-white">{{ item.value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, watch } from "vue";

const props = defineProps<{ overview: any; valuation: any; risk: any }>();
const sections = reactive([
  { title: "财务摘要", open: false, items: [] as any[] },
  { title: "估值指标", open: false, items: [] as any[] },
  { title: "风险数据", open: false, items: [] as any[] },
]);

watch(() => [props.overview, props.valuation, props.risk], () => {
  const ov = props.overview;
  if (ov?.data?.length) {
    const last = ov.data[ov.data.length - 1];
    sections[0].items = [
      { label: "最新营收", value: last.revenue + " 亿" },
      { label: "最新净利润", value: last.net_profit + " 亿" },
      { label: "最新现金流", value: last.cash_flow + " 亿" },
    ];
  }
  const v = props.valuation;
  if (v) {
    sections[1].items = [
      { label: "PE", value: v.pe?.toFixed(1) || "-" },
      { label: "PB", value: v.pb?.toFixed(1) || "-" },
      { label: "PS", value: v.ps?.toFixed(1) || "-" },
      { label: "ROE", value: (v.roe?.toFixed(1) || "-") + "%" },
      { label: "股息率", value: (v.dividend_yield?.toFixed(2) || "-") + "%" },
    ];
  }
  const r = props.risk;
  if (r) {
    sections[2].items = [
      { label: "资产负债率", value: r.debt_ratio?.toFixed(1) + "%" },
      { label: "质押比例", value: r.pledge_ratio?.toFixed(1) + "%" },
      { label: "商誉占比", value: r.goodwill_ratio?.toFixed(1) + "%" },
      { label: "现金流健康度", value: r.cash_flow_health },
      { label: "风险等级", value: r.risk_level + "风险" },
    ];
  }
}, { deep: true });
</script>
