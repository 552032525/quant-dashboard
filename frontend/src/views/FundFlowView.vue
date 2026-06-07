<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <!-- 搜索栏 -->
    <div class="flex gap-3 mb-6 items-center">
      <h2 class="text-xl font-semibold text-white">💰 智能资金监控</h2>
      <input
        v-model="searchCode"
        @keyup.enter="search"
        placeholder="输入股票代码"
        class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-36 outline-none focus:ring-1 focus:ring-[#0052ff] border border-[#1a314a]"
      />
      <button @click="search" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm font-medium hover:opacity-90">
        搜索
      </button>
    </div>

    <!-- 股票头部信息 -->
    <div v-if="store.stockFlow" class="mb-4 flex items-center gap-3">
      <span class="text-lg font-bold text-white">{{ store.name }}</span>
      <span class="text-sm text-[#8fa5c6]">{{ store.code }}</span>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-1 mb-4 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button
        v-for="t in tabs"
        :key="t.key"
        @click="store.tab = t.key"
        :class="store.tab === t.key ? 'bg-[#0052ff] text-white' : 'text-[#8fa5c6] hover:text-white'"
        class="px-4 py-1.5 rounded-md text-sm transition-colors"
      >{{ t.label }}</button>
    </div>

    <!-- Tab: 个股资金 -->
    <div v-show="store.tab === 'stock'" class="space-y-4">
      <div v-if="!store.stockFlow" class="text-center text-[#8fa5c6] py-20 text-sm">请输入股票代码查看资金流向</div>
      <template v-else>
        <FundFlowChart :data="store.stockFlow" />
        <!-- 资金流明细表 -->
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
          <h3 class="text-sm font-semibold text-white p-4 pb-2">近20日资金流向明细</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-xs text-[#8fa5c6]">
              <thead>
                <tr class="border-b border-[#1a314a]">
                  <th class="px-4 py-2 text-left">日期</th>
                  <th class="px-4 py-2 text-right">主力净流入</th>
                  <th class="px-4 py-2 text-right">超大单</th>
                  <th class="px-4 py-2 text-right">大单</th>
                  <th class="px-4 py-2 text-right">中单</th>
                  <th class="px-4 py-2 text-right">小单</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(f, i) in store.stockFlow.flows.slice().reverse()" :key="i" class="border-b border-[#1a314a] hover:bg-[#132438]">
                  <td class="px-4 py-2 font-mono">{{ f.date }}</td>
                  <td class="px-4 py-2 text-right font-mono" :class="f.main_net >= 0 ? 'text-[#05b169]' : 'text-[#cf202f]'">{{ f.main_net.toFixed(0) }}</td>
                  <td class="px-4 py-2 text-right font-mono" :class="f.super_large_net >= 0 ? 'text-[#05b169]' : 'text-[#cf202f]'">{{ f.super_large_net.toFixed(0) }}</td>
                  <td class="px-4 py-2 text-right font-mono" :class="f.large_net >= 0 ? 'text-[#05b169]' : 'text-[#cf202f]'">{{ f.large_net.toFixed(0) }}</td>
                  <td class="px-4 py-2 text-right font-mono">{{ f.mid_net.toFixed(0) }}</td>
                  <td class="px-4 py-2 text-right font-mono">{{ f.small_net.toFixed(0) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>

    <!-- Tab: 北向资金 -->
    <div v-show="store.tab === 'north'" class="space-y-4">
      <!-- 当日概况卡片 -->
      <div v-if="store.northboundDaily" class="grid grid-cols-3 gap-3">
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 text-center">
          <div class="text-xs text-[#8fa5c6] mb-1">沪股通净买入</div>
          <div class="text-lg font-bold font-mono" :class="store.northboundDaily.sh_net >= 0 ? 'text-[#05b169]' : 'text-[#cf202f]'">
            {{ store.northboundDaily.sh_net.toFixed(2) }} 亿
          </div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 text-center">
          <div class="text-xs text-[#8fa5c6] mb-1">深股通净买入</div>
          <div class="text-lg font-bold font-mono" :class="store.northboundDaily.sz_net >= 0 ? 'text-[#05b169]' : 'text-[#cf202f]'">
            {{ store.northboundDaily.sz_net.toFixed(2) }} 亿
          </div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 text-center">
          <div class="text-xs text-[#8fa5c6] mb-1">合计净买入</div>
          <div class="text-lg font-bold font-mono" :class="store.northboundDaily.total_net >= 0 ? 'text-[#05b169]' : 'text-[#cf202f]'">
            {{ store.northboundDaily.total_net.toFixed(2) }} 亿
          </div>
        </div>
      </div>
      <NorthBoundChart :data="store.northbound" :daily="store.northboundDaily" />
    </div>

    <!-- Tab: 板块资金 -->
    <div v-show="store.tab === 'sector'">
      <SectorFlowRank :data="store.sectors" />
    </div>

    <!-- Tab: AI 资金解读 -->
    <div v-show="store.tab === 'ai'" class="space-y-4">
      <div v-if="!store.report && !store.loading" class="text-center text-[#8fa5c6] py-20 text-sm">
        请先搜索个股后点击生成 AI 资金解读
      </div>
      <div v-if="store.loading" class="text-center text-[#8fa5c6] py-10">AI 分析中...</div>
      <div v-if="store.report" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5">
        <h3 class="text-sm font-semibold text-white mb-3">AI 资金面解读</h3>
        <p class="text-sm text-[#c5d0e0] leading-relaxed whitespace-pre-wrap">{{ store.report.content }}</p>
      </div>
      <div v-if="store.stockFlow" class="text-center">
        <button @click="genReport" :disabled="store.loading" class="bg-[#0052ff] text-white px-6 py-2 rounded-full text-sm font-medium hover:opacity-90 disabled:opacity-50">
          {{ store.loading ? '生成中...' : '生成 AI 资金解读' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useFundFlowStore } from "../stores/fundFlow";
import FundFlowChart from "../components/FundFlowChart.vue";
import NorthBoundChart from "../components/NorthBoundChart.vue";
import SectorFlowRank from "../components/SectorFlowRank.vue";

const route = useRoute();
const router = useRouter();
const store = useFundFlowStore();
const searchCode = ref("");

const tabs = [
  { key: "stock", label: "个股资金" },
  { key: "north", label: "北向资金" },
  { key: "sector", label: "板块资金" },
  { key: "ai", label: "资金解读" },
];

async function search() {
  const c = searchCode.value.trim();
  if (!c) return;
  router.replace(`/fundflow/${c}`);
}

async function load(code: string) {
  searchCode.value = code;
  await Promise.all([
    store.fetchStockFlow(code),
    store.fetchNorthbound(),
    store.fetchSectors(),
  ]);
}

async function genReport() {
  await store.fetchReport(store.code);
}

// 根据 tab 加载对应数据
watch(() => store.tab, (t) => {
  if (t === "north" && !store.northbound) store.fetchNorthbound();
  if (t === "sector" && !store.sectors) store.fetchSectors();
});

onMounted(() => {
  const code = route.params.code as string;
  if (code) load(code);
});
</script>
