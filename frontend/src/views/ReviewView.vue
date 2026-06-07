<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-6">📝 AI 自动复盘 & 投研报告</h2>

    <div class="flex gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- 每日复盘 -->
    <div v-show="tab==='daily'" class="space-y-4">
      <button @click="store.genDaily()" :disabled="store.loading" class="bg-[#0052ff] text-white px-6 py-2 rounded-full text-sm font-medium hover:opacity-90">{{ store.loading?'生成中...':'生成本日复盘' }}</button>
      <div v-if="store.daily" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-3">
        <h3 class="text-sm font-semibold text-white">📅 {{ store.daily.date }} 复盘</h3>
        <p class="text-sm text-[#c5d0e0] leading-relaxed whitespace-pre-wrap">{{ store.daily.content }}</p>
        <div v-if="store.daily.hot_sectors?.length" class="flex gap-2 flex-wrap">
          <span v-for="s in store.daily.hot_sectors" :key="s" class="bg-[#132438] text-[#f59e0b] px-2 py-0.5 rounded text-xs">{{ s }}</span>
        </div>
        <div v-if="store.daily.risk_alert" class="text-xs text-[#cf202f]">⚠ {{ store.daily.risk_alert }}</div>
      </div>
    </div>

    <!-- 个股研报 -->
    <div v-show="tab==='stock'" class="space-y-4">
      <div class="flex gap-3">
        <input v-model="stockCode" @keyup.enter="genStock" placeholder="股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-36 border border-[#1a314a] outline-none" />
        <button @click="genStock" :disabled="store.loading" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm hover:opacity-90">生成研报</button>
      </div>
      <div v-if="store.stock" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-3">
        <div class="flex items-center gap-3">
          <h3 class="text-sm font-semibold text-white">{{ store.stock.name }} ({{ store.stock.code }})</h3>
          <span :class="ratingBadge(store.stock.overall_rating)" class="text-xs px-2 py-0.5 rounded">{{ store.stock.overall_rating }}</span>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-[#132438] rounded p-3">
            <div class="text-xs text-[#8fa5c6] mb-1">技术面</div>
            <div class="text-sm text-[#c5d0e0]">{{ store.stock.technical_view }}</div>
          </div>
          <div class="bg-[#132438] rounded p-3">
            <div class="text-xs text-[#8fa5c6] mb-1">基本面</div>
            <div class="text-sm text-[#c5d0e0]">{{ store.stock.fundamental_view }}</div>
          </div>
        </div>
        <p class="text-sm text-[#c5d0e0] leading-relaxed">{{ store.stock.content }}</p>
      </div>
    </div>

    <!-- 周度总结 -->
    <div v-show="tab==='weekly'" class="space-y-4">
      <button @click="store.genWeekly()" :disabled="store.loading" class="bg-[#0052ff] text-white px-6 py-2 rounded-full text-sm font-medium hover:opacity-90">{{ store.loading?'生成中...':'生成周度总结' }}</button>
      <div v-if="store.weekly" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-3">
        <h3 class="text-sm font-semibold text-white">📊 {{ store.weekly.week_range }}</h3>
        <p class="text-sm text-[#c5d0e0] leading-relaxed">{{ store.weekly.content }}</p>
        <div v-if="store.weekly.key_events?.length" class="space-y-1">
          <div v-for="(e,i) in store.weekly.key_events" :key="i" class="text-xs text-[#8fa5c6] flex gap-2"><span class="text-[#0052ff]">•</span>{{ e }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useReviewStore } from "../stores/reviewMonitor";

const store = useReviewStore();
const tab = ref("daily");
const stockCode = ref("");

const tabs = [
  { key: "daily", label: "每日复盘" },
  { key: "stock", label: "个股研报" },
  { key: "weekly", label: "周度总结" },
];

function genStock() { const c = stockCode.value.trim(); if (c) store.genStock(c); }
function ratingBadge(r: string) {
  if (r.includes("买入")||r.includes("推荐")) return "bg-[#05b169]/20 text-[#05b169]";
  if (r.includes("卖出")||r.includes("回避")) return "bg-[#cf202f]/20 text-[#cf202f]";
  return "bg-[#f59e0b]/20 text-[#f59e0b]";
}
</script>
