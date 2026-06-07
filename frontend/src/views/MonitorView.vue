<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-6">🔔 个性化智能盯盘</h2>

    <!-- 总览 -->
    <div class="grid grid-cols-4 gap-3 mb-6" v-if="store.summary">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
        <div class="text-xs text-[#8fa5c6]">活跃提醒</div>
        <div class="text-xl font-bold text-[#f59e0b]">{{ store.summary.active_alerts }}</div>
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
        <div class="text-xs text-[#8fa5c6]">今日触发</div>
        <div class="text-xl font-bold text-[#cf202f]">{{ store.summary.triggered_today }}</div>
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
        <div class="text-xs text-[#8fa5c6]">自选股</div>
        <div class="text-xl font-bold text-white">{{ store.summary.watchlist_count }}</div>
      </div>
      <div class="flex items-end">
        <button @click="refresh" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-xs hover:opacity-90 w-full">刷新检查</button>
      </div>
    </div>

    <div class="flex gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- 自选股 -->
    <div v-show="tab==='watch'" class="space-y-4">
      <div class="flex gap-3">
        <input v-model="newWatch" @keyup.enter="addWatch" placeholder="添加股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-36 border border-[#1a314a]" />
        <button @click="addWatch" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm hover:opacity-90">添加</button>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div v-for="w in store.watchlist" :key="w.code" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 flex justify-between items-center">
          <div>
            <div class="text-sm font-medium text-white">{{ w.name }}</div>
            <div class="text-xs text-[#8fa5c6]">{{ w.code }}</div>
          </div>
          <div class="text-right">
            <div class="text-sm font-mono" :class="w.change_pct>=0?'text-[#05b169]':'text-[#cf202f]'">{{ w.change_pct>=0?'+':''}}{{ w.change_pct.toFixed(2) }}%</div>
            <div class="text-xs text-[#8fa5c6] font-mono">{{ w.price.toFixed(2) }}</div>
          </div>
          <button @click="store.removeWatch(w.code)" class="text-[#cf202f] text-xs hover:opacity-80">✕</button>
        </div>
      </div>
    </div>

    <!-- 提醒规则 -->
    <div v-show="tab==='alerts'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 grid grid-cols-5 gap-2">
        <input v-model="alertForm.code" placeholder="代码" class="bg-[#132438] text-white px-2 py-1.5 rounded text-xs border border-[#1a314a]" />
        <select v-model="alertForm.type" class="bg-[#132438] text-white px-2 py-1.5 rounded text-xs border border-[#1a314a]">
          <option value="price_break">价格突破</option>
          <option value="change_pct">涨跌幅</option>
        </select>
        <input v-model.number="alertForm.threshold" type="number" placeholder="阈值" class="bg-[#132438] text-white px-2 py-1.5 rounded text-xs border border-[#1a314a]" />
        <select v-model="alertForm.direction" class="bg-[#132438] text-white px-2 py-1.5 rounded text-xs border border-[#1a314a]">
          <option value="above">向上突破</option>
          <option value="below">向下跌破</option>
        </select>
        <button @click="createAlert" class="bg-[#0052ff] text-white px-3 py-1.5 rounded-full text-xs hover:opacity-90">添加</button>
      </div>

      <div v-for="a in store.alerts" :key="a.id" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 flex justify-between items-center">
        <div>
          <span class="text-sm font-medium text-white">{{ a.name }}</span>
          <span class="text-xs text-[#8fa5c6] ml-2">{{ a.code }}</span>
          <span class="text-xs text-[#f59e0b] ml-2">{{ alertTypeLabel(a.type) }} {{ a.direction==='above'?'≥':'≤' }} {{ a.threshold }}</span>
        </div>
        <button @click="store.deleteAlert(a.id)" class="text-[#cf202f] text-xs hover:opacity-80">删除</button>
      </div>
    </div>

    <!-- 触发事件 -->
    <div v-show="tab==='events' && store.alertEvents.length" class="space-y-2">
      <div v-for="(e,i) in store.alertEvents" :key="i" class="bg-[#cf202f]/10 rounded-lg border border-[#cf202f]/30 p-3">
        <div class="flex items-center gap-2">
          <span class="text-xs text-[#cf202f]">🔔</span>
          <span class="text-sm text-white">{{ e.message }}</span>
          <span class="text-xs text-[#8fa5c6] ml-auto">{{ e.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useMonitorStore } from "../stores/reviewMonitor";

const store = useMonitorStore();
const tab = ref("watch");
const newWatch = ref("");
const alertForm = ref({ code: "", type: "price_break", threshold: 0, direction: "above" });

const tabs = [
  { key: "watch", label: "自选股" },
  { key: "alerts", label: "提醒规则" },
  { key: "events", label: "触发事件" },
];

function alertTypeLabel(t: string) { return t==='price_break'?'价格':'涨跌幅'; }

async function addWatch() { const c = newWatch.value.trim(); if (c) { await store.addWatch(c); newWatch.value = ""; } }
async function createAlert() {
  if (!alertForm.value.code || !alertForm.value.threshold) return;
  await store.createAlert(alertForm.value);
  alertForm.value = { code: "", type: "price_break", threshold: 0, direction: "above" };
}
async function refresh() {
  await Promise.all([store.checkAlerts(), store.fetchSummary(), store.fetchWatchlist()]);
}

onMounted(() => refresh());
</script>
