<template>
  <div class="h-full flex flex-col bg-[#0a1628] text-white">
    <!-- Search Header -->
    <div class="flex items-center gap-3 px-4 py-3 border-b border-[#1a314a]">
      <input v-model="searchCode" @keyup.enter="doSearch" placeholder="输入股票代码，如 600519"
        class="flex-1 bg-[#162436] border border-[#1a314a] rounded px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500" />
      <button @click="doSearch" class="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm text-white">搜索</button>
    </div>
    <!-- Stock Header -->
    <div v-if="store.name" class="flex items-center gap-4 px-4 py-2 border-b border-[#1a314a] text-sm">
      <span class="text-white font-semibold">{{ store.name }}</span>
      <span class="text-blue-300">{{ store.code }}</span>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 px-4 py-2 border-b border-[#1a314a]">
      <button v-for="t in tabs" :key="t.key" @click="activeTab = t.key"
        class="px-4 py-1 text-xs rounded" :class="activeTab === t.key ? 'bg-blue-600 text-white' : 'text-blue-300 hover:bg-[#162436]'">
        {{ t.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="flex-1 overflow-auto p-4">
      <!-- Tab 1: AI Report -->
      <div v-if="activeTab === 'report'" v-show="store.code" class="grid grid-cols-2 gap-4">
        <FinancialChart :data="store.overview?.data" />
        <ValuationGauge :valuation="store.valuation" />
        <RiskRadar :risk="store.risk" />
        <AIReportCard :report="store.report" :loading="store.loading" @refresh="store.fetchReport(store.code)" />
      </div>

      <!-- Tab 2: Q&A -->
      <div v-if="activeTab === 'chat'" v-show="store.code" class="grid grid-cols-3 gap-4 h-full">
        <div class="col-span-1 overflow-auto">
          <DataCards :overview="store.overview" :valuation="store.valuation" :risk="store.risk" />
        </div>
        <div class="col-span-2 flex flex-col bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
          <div class="flex-1 overflow-auto p-4 space-y-2">
            <div v-for="(msg, i) in messages" :key="i" :class="msg.role === 'user' ? 'text-right' : 'text-left'">
              <div :class="msg.role === 'user' ? 'bg-blue-600 inline-block' : 'bg-[#162436] inline-block'"
                class="px-3 py-2 rounded-lg text-sm max-w-[80%]">
                <pre class="whitespace-pre-wrap font-sans">{{ msg.content }}</pre>
              </div>
            </div>
            <div v-if="chatLoading" class="text-blue-300 text-xs">AI 思考中...</div>
          </div>
          <div class="flex gap-2 p-3 border-t border-[#1a314a]">
            <input v-model="chatInput" @keyup.enter="sendChat" placeholder="基于财务数据提问..."
              class="flex-1 bg-[#162436] border border-[#1a314a] rounded px-3 py-1.5 text-sm text-white placeholder-gray-500" />
            <button @click="sendChat" class="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm text-white">发送</button>
          </div>
        </div>
      </div>

      <!-- Tab 3: Compare -->
      <div v-if="activeTab === 'compare'" class="space-y-4 max-w-3xl mx-auto">
        <div class="flex gap-2">
          <input v-model="compareInput" @keyup.enter="addCompare" placeholder="输入代码如 600519 回车添加"
            class="flex-1 bg-[#162436] border border-[#1a314a] rounded px-3 py-1.5 text-sm text-white" />
          <button @click="startCompare" class="px-4 py-1.5 bg-green-600 hover:bg-green-500 rounded text-sm text-white"
            :disabled="compareCodes.length < 2">开始对比</button>
        </div>
        <div class="flex flex-wrap gap-2">
          <span v-for="c in compareCodes" :key="c" class="px-2 py-1 bg-[#162436] rounded text-xs text-blue-300 flex items-center gap-1">
            {{ c }} <button @click="compareCodes = compareCodes.filter(x => x !== c)" class="text-red-400 hover:text-red-300">&times;</button>
          </span>
        </div>
        <CompareTable :result="store.compareResult" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useFundamentalStore } from "../stores/fundamental";
import FinancialChart from "../components/FinancialChart.vue";
import ValuationGauge from "../components/ValuationGauge.vue";
import RiskRadar from "../components/RiskRadar.vue";
import AIReportCard from "../components/AIReportCard.vue";
import DataCards from "../components/DataCards.vue";
import CompareTable from "../components/CompareTable.vue";

const route = useRoute();
const router = useRouter();
const store = useFundamentalStore();

const activeTab = ref("report");
const searchCode = ref("");
const chatInput = ref("");
const chatLoading = ref(false);
const compareInput = ref("");
const compareCodes = ref<string[]>([]);
const messages = ref<{ role: string; content: string }[]>([]);

const tabs = [
  { key: "report", label: "AI研报" },
  { key: "chat", label: "交互问答" },
  { key: "compare", label: "批量对比" },
];

async function doSearch() {
  const code = searchCode.value.trim();
  if (!code) return;
  searchCode.value = code;
  router.replace(`/fundamental/${code}`);
}

async function loadCode(code: string) {
  searchCode.value = code;
  await store.fetchAll(code);
  store.fetchReport(code);
}

async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg || !store.code) return;
  messages.value.push({ role: "user", content: msg });
  chatInput.value = "";
  chatLoading.value = true;
  const reply = await store.chat(store.code, msg);
  messages.value.push({ role: "assistant", content: reply });
  chatLoading.value = false;
}

function addCompare() {
  const code = compareInput.value.trim();
  if (code && !compareCodes.value.includes(code)) {
    compareCodes.value.push(code);
  }
  compareInput.value = "";
}

async function startCompare() {
  if (compareCodes.value.length < 2) return;
  await store.compare(compareCodes.value);
}

watch(() => route.params.code, async (c) => {
  if (c && typeof c === "string") await loadCode(c);
}, { immediate: true });

onMounted(() => {
  const c = route.params.code;
  if (c && typeof c === "string") loadCode(c);
});
</script>
