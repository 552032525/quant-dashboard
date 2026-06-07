<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-6">🛡️ 智能风控预警</h2>

    <div class="flex gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- 个股风险 -->
    <div v-show="tab==='stock'" class="space-y-4">
      <div class="flex gap-3">
        <input v-model="code" @keyup.enter="checkStock" placeholder="股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-36 border border-[#1a314a] outline-none focus:ring-1 focus:ring-[#0052ff]" />
        <button @click="checkStock" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm hover:opacity-90">风险筛查</button>
      </div>

      <div v-if="store.stockRisk" class="space-y-4">
        <div class="flex items-center gap-3">
          <span class="text-lg font-bold text-white">{{ store.stockRisk.name }}</span>
          <span :class="riskBadge(store.stockRisk.overall_risk)" class="px-3 py-0.5 rounded-full text-xs font-medium">{{ riskLabel(store.stockRisk.overall_risk) }}</span>
        </div>
        <div v-for="(r,i) in store.stockRisk.items" :key="i" :class="severityBg(r.severity)" class="rounded-lg border p-4">
          <div class="text-sm font-medium text-white">{{ r.description }}</div>
          <div v-if="r.detail" class="text-xs text-[#8fa5c6] mt-1">{{ r.detail }}</div>
        </div>
        <div v-if="store.stockRisk.suggestion" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">AI 建议</div>
          <div class="text-sm text-[#c5d0e0]">{{ store.stockRisk.suggestion }}</div>
        </div>
      </div>
      <div v-if="!store.stockRisk && !store.loading" class="text-center text-[#8fa5c6] py-20 text-sm">输入股票代码进行风险筛查</div>
    </div>

    <!-- 大盘风险 -->
    <div v-show="tab==='market'">
      <div v-if="store.marketRisk" class="space-y-4">
        <div :class="marketRiskBg(store.marketRisk.risk_level)" class="rounded-lg border p-5">
          <div class="text-lg font-bold text-white mb-2">大盘风险等级：{{ marketRiskLabel(store.marketRisk.risk_level) }}</div>
          <div class="text-sm text-[#c5d0e0]">{{ store.marketRisk.description }}</div>
          <div v-if="store.marketRisk.signals.length" class="mt-3 space-y-1">
            <div v-for="(s,i) in store.marketRisk.signals" :key="i" class="text-xs text-[#cf202f]">⚠ {{ s }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 持仓风控 -->
    <div v-show="tab==='portfolio'">
      <div v-if="store.portfolioRisks.length" class="space-y-2">
        <div v-for="(p,i) in store.portfolioRisks" :key="i" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="flex justify-between items-center">
            <div>
              <span class="text-sm font-medium text-white">{{ p.name }}</span>
              <span class="text-xs text-[#8fa5c6] ml-2">{{ p.code }}</span>
            </div>
            <div class="flex gap-2">
              <span v-if="p.risk_flags.length" class="text-xs text-[#cf202f]">⚠ 风险</span>
              <span v-else class="text-xs text-[#05b169]">✓ 正常</span>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 mt-2 text-xs text-[#8fa5c6]">
            <div>止损价: {{ p.stop_loss_price }}</div>
            <div>止盈价: {{ p.take_profit_price }}</div>
            <div>权重: {{ p.weight_pct }}%</div>
          </div>
        </div>
      </div>
      <div v-if="!store.portfolioRisks.length && !store.loading" class="text-center text-[#8fa5c6] py-20 text-sm">加载持仓数据后可查看风控分析</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRiskStore } from "../stores/risk";
import { api } from "../api";

const store = useRiskStore();
const tab = ref("stock");
const code = ref("");

const tabs = [
  { key: "stock", label: "个股风险" },
  { key: "market", label: "大盘风险" },
  { key: "portfolio", label: "持仓风控" },
];

function checkStock() { const c = code.value.trim(); if (c) store.checkStock(c); }
function riskBadge(level: string) { return level==='high'?'bg-[#cf202f]/20 text-[#cf202f]':level==='medium'?'bg-[#f59e0b]/20 text-[#f59e0b]':'bg-[#05b169]/20 text-[#05b169]'; }
function riskLabel(level: string) { return level==='high'?'高风险':level==='medium'?'中风险':'低风险'; }
function severityBg(s: string) { return s==='high'?'bg-[#cf202f]/10 border-[#cf202f]/30':s==='medium'?'bg-[#f59e0b]/10 border-[#f59e0b]/30':'bg-[#0f1a2e] border-[#1a314a]'; }
function marketRiskBg(l: string) { return l==='high'?'bg-[#cf202f]/10 border-[#cf202f]/30':l==='medium'?'bg-[#f59e0b]/10 border-[#f59e0b]/30':'bg-[#05b169]/10 border-[#05b169]/30'; }
function marketRiskLabel(l: string) { return l==='high'?'⚠ 高风险':l==='medium'?'⚡ 中风险':'✅ 低风险'; }

onMounted(async () => {
  store.fetchMarketRisk();
  try {
    const positions = await api.portfolio.list();
    if (positions.length) store.checkPortfolio(positions);
  } catch(e) {}
});
</script>
