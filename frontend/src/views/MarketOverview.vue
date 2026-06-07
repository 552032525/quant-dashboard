<template>
  <div class="h-full flex flex-col">
    <IndexBar :data="m.indexQuotes" :breadth="breadthData" />
    <div v-if="m.indexError" class="text-xs text-[#cf202f] px-4 py-1 bg-[#cf202f]/10">{{ m.indexError }}</div>
    <!-- 指数历史走势迷你图 -->
    <div v-if="indexHistoryData && Object.keys(indexHistoryData).length" class="px-4 py-2 bg-surface border-b border-surface-2">
      <div class="text-xs text-text-secondary mb-2">指数近期走势</div>
      <div class="flex gap-4">
        <div v-for="(item, code) in indexHistoryData" :key="code" class="flex-1 bg-surface-2 rounded px-3 py-2">
          <div class="flex justify-between items-center mb-1">
            <span class="text-xs text-text-secondary">{{ item.name }}</span>
            <span class="text-xs font-mono" :class="getTrendClass(item.data)">{{ getTrendLabel(item.data) }}</span>
          </div>
          <svg :viewBox="'0 0 ' + sparkWidth + ' 40'" class="w-full h-10">
            <polyline
              :points="sparkPoints(item.data, sparkWidth, 40)"
              fill="none"
              :stroke="getTrendColor(item.data)"
              stroke-width="1.5"
            />
          </svg>
        </div>
      </div>
    </div>
    <HeatBar :data="m.heat" />
    <div v-if="m.heatError" class="text-xs text-[#cf202f] px-4 py-1 bg-[#cf202f]/10">{{ m.heatError }}</div>
    <div class="flex-1 flex flex-col lg:flex-row overflow-hidden">
      <div class="flex-1 border-r border-[#1a314a]">
        <SectorHeatmap :data="m.sectors" :type="sectorType"
          @toggle="sectorType = sectorType === 'industry' ? 'concept' : 'industry'; m.fetchSectors(sectorType)" />
        <div v-if="m.sectorsError" class="text-xs text-[#cf202f] px-3 py-1">{{ m.sectorsError }}</div>
      </div>
      <div class="w-full lg:w-80 flex flex-col">
        <div class="flex-1 overflow-auto">
          <RankingList :data="m.rankings" :rankType="rankType"
            @toggle="rankType = rankType === 'up' ? 'down' : 'up'; m.fetchRankings(rankType)"
            @select="(code: string) => $router.push(`/stock/${code}`)" />
          <div v-if="m.rankingsError" class="text-xs text-[#cf202f] px-3 py-1">{{ m.rankingsError }}</div>
        </div>
        <!-- 自选股面板 -->
        <div class="border-t border-[#1a314a] p-3 max-h-48 overflow-auto">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-[#8fa5c6]">⭐ 自选股</span>
            <div class="flex gap-1">
              <input v-model="watchInput" @keyup.enter="addWatch" placeholder="代码" class="w-20 bg-[#132438] text-white px-2 py-0.5 rounded text-xs border border-[#1a314a]" />
              <button @click="addWatch" class="text-[#0052ff] text-xs hover:opacity-80">+</button>
            </div>
          </div>
          <div v-if="watchMsg" class="text-xs mb-2 px-2 py-1 rounded" :class="watchMsgType==='ok'?'text-[#05b169] bg-[#05b169]/10':'text-[#f59e0b] bg-[#f59e0b]/10'">{{ watchMsg }}</div>
          <div v-for="w in watchlist" :key="w.code" class="flex justify-between items-center py-1.5 border-b border-[#1a314a] last:border-0 cursor-pointer hover:bg-[#132438] px-1 rounded" @click="$router.push(`/analysis/${w.code}`)">
            <div>
              <span class="text-xs text-white">{{ w.name }}</span>
              <span class="text-xs text-[#8fa5c6] ml-1 font-mono">{{ w.code }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono" :class="w.change_pct>=0?'text-[#05b169]':'text-[#cf202f]'">{{ w.change_pct>=0?'+':''}}{{ w.change_pct.toFixed(2) }}%</span>
              <button @click.stop="removeWatch(w.code)" class="text-[#cf202f] text-xs">✕</button>
            </div>
          </div>
          <div v-if="!watchlist.length" class="text-xs text-[#8fa5c6] text-center py-2">添加自选股跟踪</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useMarketStore } from "../stores/market";
import { api } from "../api";
import IndexBar from "../components/IndexBar.vue";
import HeatBar from "../components/HeatBar.vue";
import SectorHeatmap from "../components/SectorHeatmap.vue";
import RankingList from "../components/RankingList.vue";

const m = useMarketStore();
const sectorType = ref("industry");
const rankType = ref("up");
const watchInput = ref("");
const watchlist = ref<any[]>([]);
const watchMsg = ref("");
const watchMsgType = ref("ok");
let watchMsgTimer: ReturnType<typeof setTimeout> | null = null;

function showWatchMsg(msg: string, type: "ok" | "warn" = "ok") {
  watchMsg.value = msg;
  watchMsgType.value = type;
  if (watchMsgTimer) clearTimeout(watchMsgTimer);
  watchMsgTimer = setTimeout(() => { watchMsg.value = ""; }, 3000);
}

async function loadWatchlist() {
  try { watchlist.value = await api.monitor.watchlist(); } catch(e: any) { showWatchMsg("自选列表加载失败: " + (e.message || "未知错误"), "warn"); }
}
async function addWatch() {
  const c = watchInput.value.trim(); if (!c) return;
  try {
    const result = await api.monitor.addWatch(c);
    watchInput.value = "";
    showWatchMsg(result.message || (result.added ? "添加成功" : "已存在"), result.added ? "ok" : "warn");
    await loadWatchlist();
  } catch(e: any) {
    showWatchMsg("添加失败: " + (e.message || "网络错误"), "warn");
  }
}
async function removeWatch(code: string) {
  try {
    const result = await api.monitor.removeWatch(code);
    showWatchMsg(result.message || "已移除", "ok");
    await loadWatchlist();
  } catch(e: any) {
    showWatchMsg("移除失败: " + (e.message || "网络错误"), "warn");
  }
}

// 市场广度 + 指数历史
const breadthData = ref<any>(null);
const indexHistoryData = ref<any>(null);
const sparkWidth = 160;

async function loadMarketExtras() {
  try { breadthData.value = await api.market.breadth(); } catch (e) { /* 静默降级 */ }
  try { indexHistoryData.value = await api.market.indexHistory(30); } catch (e) { /* 静默降级 */ }
}

function sparkPoints(data: any[], w: number, h: number): string {
  if (!data || data.length < 2) return "";
  const closes = data.map(d => d.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const padding = 2;
  const xStep = (w - padding * 2) / (closes.length - 1);
  return closes.map((v, i) => {
    const x = padding + i * xStep;
    const y = h - padding - ((v - min) / range) * (h - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function getTrendLabel(data: any[]): string {
  if (!data || data.length < 2) return "—";
  const first = data[0].close;
  const last = data[data.length - 1].close;
  const pct = ((last - first) / first * 100);
  return (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%";
}

function getTrendClass(data: any[]): string {
  if (!data || data.length < 2) return "text-text-secondary";
  const first = data[0].close;
  const last = data[data.length - 1].close;
  return last >= first ? "text-gain" : "text-loss";
}

function getTrendColor(data: any[]): string {
  if (!data || data.length < 2) return "#8fa5c6";
  return data[0].close <= data[data.length - 1].close ? "#05b169" : "#cf202f";
}

onMounted(async () => {
  await Promise.all([m.fetchIndex(), m.fetchHeat(), m.fetchSectors("industry"), m.fetchRankings("up"), loadWatchlist(), loadMarketExtras()]);
});
</script>
