<template>
  <div class="h-full flex flex-col">
    <div class="px-4 py-3 border-b border-surface-2 flex gap-3 items-center relative">
      <input v-model="kw" @keyup.enter="search" placeholder="搜索股票代码/名称..." class="bg-surface-2 text-text-primary px-3 py-1.5 rounded-lg text-sm w-64 outline-none focus:ring-1 focus:ring-primary" />
      <div v-if="results.length" class="absolute top-12 left-4 bg-surface-2 rounded-lg shadow-lg z-50 max-h-60 overflow-auto">
        <div v-for="r in results" :key="r.code" @click="select(r.code)" class="px-3 py-2 hover:bg-surface cursor-pointer text-sm whitespace-nowrap">{{ r.code }} {{ r.name }}</div>
      </div>
    </div>
    <div class="flex-1 flex">
      <div class="flex-1 p-4">
        <div class="flex items-center gap-3 mb-3">
          <h2 class="text-lg font-medium">{{ m.quote?.name || m.activeSymbol }}</h2>
          <span v-if="m.quote" class="font-mono text-lg" :class="m.quote.change_pct>=0?'text-gain':'text-loss'">{{ m.quote.price?.toFixed(2) }}</span>
          <span v-if="m.quote" class="text-sm font-mono" :class="m.quote.change_pct>=0?'text-gain':'text-loss'">{{ m.quote.change_pct>=0?'+':'' }}{{ m.quote.change_pct?.toFixed(2) }}%</span>
        </div>
        <KLineChart v-if="m.klineData.length" :data="m.klineData" class="h-[calc(100%-3rem)]" />
        <div v-else class="h-full flex items-center justify-center text-text-secondary">输入股票代码查看 K 线图</div>
      </div>
      <aside class="w-72 border-l border-surface-2 p-4 flex flex-col gap-3 overflow-auto">
        <MetricCard label="最新价" :value="m.quote?.price??0" :trend="m.quote?.change_pct>=0?'up':'down'" />
        <MetricCard label="涨跌幅" :value="m.quote?.change_pct??0" :sub="m.quote?.change?.toFixed(2)" :trend="m.quote?.change_pct>=0?'up':'down'" />
        <MetricCard label="成交量" :value="m.quote?.volume??0" :decimals="0" trend="neutral" />
        <MetricCard label="最高" :value="m.quote?.high??0" trend="neutral" />
        <MetricCard label="最低" :value="m.quote?.low??0" trend="neutral" />
        <MetricCard label="今开" :value="m.quote?.open??0" trend="neutral" />
        <MetricCard label="昨收" :value="m.quote?.pre_close??0" trend="neutral" />
      </aside>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue"; import { useMarketStore } from "../stores/market"; import { api } from "../api"; import KLineChart from "../components/KLineChart.vue"; import MetricCard from "../components/MetricCard.vue";
const m = useMarketStore(); const kw = ref(""); const results = ref<any[]>([]);
async function search() { if(kw.value.trim()) results.value = await api.market.search(kw.value.trim()); }
function select(code: string) { results.value=[]; kw.value=""; m.fetchKline(code); }
onMounted(()=>m.fetchKline("600519"));
</script>
