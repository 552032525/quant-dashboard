<template>
  <div class="h-full flex flex-col">
    <IndexBar :data="m.indexQuotes" />
    <HeatBar :data="m.heat" />
    <div class="flex-1 flex overflow-hidden">
      <div class="flex-1 border-r border-surface-2">
        <SectorHeatmap :data="m.sectors" :type="sectorType"
          @toggle="sectorType = sectorType === 'industry' ? 'concept' : 'industry'; m.fetchSectors(sectorType)" />
      </div>
      <div class="w-80">
        <RankingList :data="m.rankings" :rankType="rankType"
          @toggle="rankType = rankType === 'up' ? 'down' : 'up'; m.fetchRankings(rankType)"
          @select="(code: string) => $router.push(`/stock/${code}`)" />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useMarketStore } from "../stores/market";
import IndexBar from "../components/IndexBar.vue";
import HeatBar from "../components/HeatBar.vue";
import SectorHeatmap from "../components/SectorHeatmap.vue";
import RankingList from "../components/RankingList.vue";

const m = useMarketStore();
const sectorType = ref("industry");
const rankType = ref("up");

onMounted(async () => {
  await Promise.all([m.fetchIndex(), m.fetchHeat(), m.fetchSectors("industry"), m.fetchRankings("up")]);
});
</script>