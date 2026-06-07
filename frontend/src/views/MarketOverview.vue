<template>
  <div class="h-full flex flex-col">
    <IndexBar :data="m.indexQuotes" />
    <HeatBar :data="m.heat" />
    <div class="flex-1 flex overflow-hidden">
      <div class="flex-1 border-r border-[#1a314a]">
        <SectorHeatmap :data="m.sectors" :type="sectorType"
          @toggle="sectorType = sectorType === 'industry' ? 'concept' : 'industry'; m.fetchSectors(sectorType)" />
      </div>
      <div class="w-80 flex flex-col">
        <div class="flex-1 overflow-auto">
          <RankingList :data="m.rankings" :rankType="rankType"
            @toggle="rankType = rankType === 'up' ? 'down' : 'up'; m.fetchRankings(rankType)"
            @select="(code: string) => $router.push(`/stock/${code}`)" />
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

async function loadWatchlist() {
  try { watchlist.value = await api.monitor.watchlist(); } catch(e){}
}
async function addWatch() {
  const c = watchInput.value.trim(); if (!c) return;
  try { await api.monitor.addWatch(c); watchInput.value = ""; await loadWatchlist(); } catch(e){}
}
async function removeWatch(code: string) {
  try { await api.monitor.removeWatch(code); await loadWatchlist(); } catch(e){}
}

onMounted(async () => {
  await Promise.all([m.fetchIndex(), m.fetchHeat(), m.fetchSectors("industry"), m.fetchRankings("up"), loadWatchlist()]);
});
</script>
