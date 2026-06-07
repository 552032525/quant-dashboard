<template>
  <div class="h-full flex flex-col bg-[#0a1628] text-white overflow-auto">
    <!-- Header -->
    <div class="flex items-center gap-3 px-4 py-3 border-b border-[#1a314a] sticky top-0 bg-[#0a1628] z-10">
      <input v-model="searchCode" @keyup.enter="doSearch" placeholder="输入股票代码，如 600519"
        class="flex-1 bg-[#162436] border border-[#1a314a] rounded px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500" />
      <button @click="doSearch" class="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm text-white">搜索</button>
      <select v-model="period" @change="changePeriod" class="bg-[#162436] border border-[#1a314a] rounded px-2 py-1.5 text-sm text-white">
        <option value="daily">日K</option>
        <option value="weekly">周K</option>
        <option value="60">60分</option>
        <option value="30">30分</option>
      </select>
    </div>

    <!-- Stock Info -->
    <div v-if="store.name" class="flex items-center gap-4 px-4 py-2 border-b border-[#1a314a] text-sm">
      <span class="text-white font-semibold">{{ store.name }}</span>
      <span class="text-blue-300">{{ store.code }}</span>
      <span v-if="store.anomalies?.anomalies?.length" class="text-yellow-400 text-xs">
        {{ store.anomalies.anomalies.length }} 个异动
      </span>
    </div>

    <!-- Charts -->
    <div v-if="store.indicators" class="p-4 space-y-4">
      <!-- K-line -->
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a]" style="height:400px">
        <KLineChart :data="klineData" :period="store.period"
          :ma5="store.indicators.ma5" :ma10="store.indicators.ma10"
          :ma20="store.indicators.ma20" :ma60="store.indicators.ma60"
          :boll_up="store.indicators.boll_up" :boll_mid="store.indicators.boll_mid"
          :boll_dn="store.indicators.boll_dn" />
      </div>

      <!-- MACD -->
      <MacdChart :data="store.indicators" />

      <!-- RSI + KDJ -->
      <RsiKdjChart :data="store.indicators" />

      <!-- Score + Report -->
      <div class="grid grid-cols-2 gap-4">
        <ScoreCards :score="store.score" />
        <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-white">AI 技术面研报</h3>
            <button @click="store.fetchReport(store.code)" class="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white">
              刷新
            </button>
          </div>
          <div v-if="store.report" class="prose prose-sm prose-invert max-w-none">
            <div class="text-green-400 text-sm font-semibold mb-2">{{ store.report.summary }}</div>
            <pre class="text-sm text-blue-200 whitespace-pre-wrap font-sans">{{ store.report.content }}</pre>
          </div>
          <div v-else class="text-center py-8 text-gray-500 text-sm">点击刷新生成 AI 研报</div>
        </div>
      </div>
    </div>
    <div v-else class="flex-1 flex items-center justify-center text-gray-500">输入股票代码开始分析</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTechnicalStore } from "../stores/technical";
import KLineChart from "../components/KLineChart.vue";
import MacdChart from "../components/MacdChart.vue";
import RsiKdjChart from "../components/RsiKdjChart.vue";
import ScoreCards from "../components/ScoreCards.vue";

const route = useRoute();
const router = useRouter();
const store = useTechnicalStore();

const searchCode = ref("");
const period = ref("daily");

const klineData = computed(() => {
  const d = store.indicators;
  if (!d) return [];
  return d.dates.map((date: string, i: number) => ({
    date,
    open: d.open[i],
    close: d.close[i],
    high: d.high[i],
    low: d.low[i],
    volume: d.volume[i],
  }));
});

async function doSearch() {
  const c = searchCode.value.trim();
  if (!c) return;
  searchCode.value = c;
  router.replace(`/technical/${c}`);
}

async function loadCode(c: string) {
  searchCode.value = c;
  await store.fetchAll(c, period.value);
  store.fetchReport(c);
}

function changePeriod() {
  if (store.code) store.fetchAll(store.code, period.value);
}

watch(() => route.params.code, (c) => {
  if (c && typeof c === "string") loadCode(c);
}, { immediate: true });

onMounted(() => {
  const c = route.params.code;
  if (c && typeof c === "string") loadCode(c);
});
</script>
