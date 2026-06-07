<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <div class="flex gap-3 mb-6 items-center">
      <h2 class="text-xl font-semibold text-white">📰 NLP 舆情资讯</h2>
      <input v-model="searchCode" @keyup.enter="search" placeholder="输入股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-36 outline-none focus:ring-1 focus:ring-[#0052ff] border border-[#1a314a]" />
      <button @click="search" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm font-medium hover:opacity-90">搜索</button>
    </div>

    <div v-if="store.name" class="mb-4 flex items-center gap-3">
      <span class="text-lg font-bold text-white">{{ store.name }}</span>
      <span class="text-sm text-[#8fa5c6]">{{ store.code }}</span>
    </div>

    <div class="flex gap-1 mb-4 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="switchTab(t.key)" :class="store.tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- 个股舆情 -->
    <div v-show="store.tab==='news'" class="space-y-4">
      <div v-if="!store.news" class="text-center text-[#8fa5c6] py-20 text-sm">请输入股票代码查看舆情资讯</div>
      <template v-else>
        <div v-if="store.sentiment" class="grid grid-cols-5 gap-3 mb-4">
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6] mb-1">舆情总分</div>
            <div class="text-xl font-bold font-mono" :class="store.sentiment.overall>0.2?'text-[#05b169]':store.sentiment.overall<-0.2?'text-[#cf202f]':'text-[#8fa5c6]'">{{ store.sentiment.overall.toFixed(2) }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6] mb-1">利好</div>
            <div class="text-lg font-bold text-[#05b169]">{{ store.sentiment.positive_count }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6] mb-1">利空</div>
            <div class="text-lg font-bold text-[#cf202f]">{{ store.sentiment.negative_count }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6] mb-1">中性</div>
            <div class="text-lg font-bold text-[#8fa5c6]">{{ store.sentiment.neutral_count }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3">
            <div class="text-xs text-[#8fa5c6] mb-2">关键议题</div>
            <div class="flex flex-wrap gap-1">
              <span v-for="t in store.sentiment.key_topics" :key="t" class="bg-[#132438] text-[#8fa5c6] px-2 py-0.5 rounded text-xs">{{ t }}</span>
            </div>
          </div>
        </div>
        <div class="flex gap-2 mb-3">
          <button @click="doAnalyze" :disabled="store.loading" class="bg-[#0052ff] text-white px-4 py-1.5 rounded-full text-xs hover:opacity-90">AI 情感分析</button>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
          <h3 class="text-sm font-semibold text-white p-4 pb-2">相关资讯</h3>
          <div class="divide-y divide-[#1a314a]">
            <div v-for="(n,i) in store.news.items" :key="i" class="px-4 py-3 hover:bg-[#132438]">
              <div class="text-sm text-[#c5d0e0] leading-relaxed">{{ n.title }}</div>
              <div class="flex gap-3 mt-1 text-xs text-[#8fa5c6]">
                <span>{{ n.source }}</span>
                <span>{{ n.time }}</span>
              </div>
            </div>
            <div v-if="!store.news.items.length" class="px-4 py-8 text-center text-[#8fa5c6] text-sm">暂无相关资讯</div>
          </div>
        </div>
      </template>
    </div>

    <!-- 市场热点 -->
    <div v-show="store.tab==='hot'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <h3 class="text-sm font-semibold text-white p-4 pb-2">市场热点</h3>
        <div class="divide-y divide-[#1a314a]">
          <div v-for="(n,i) in (store.marketNews?.hot_topics||[])" :key="i" class="px-4 py-3 hover:bg-[#132438]">
            <div class="text-sm text-[#c5d0e0]">{{ n.title }}</div>
            <div class="text-xs text-[#8fa5c6] mt-1">{{ n.source }} · {{ n.time }}</div>
          </div>
          <div v-if="!(store.marketNews?.hot_topics?.length)" class="px-4 py-8 text-center text-[#8fa5c6] text-sm">加载中...</div>
        </div>
      </div>
    </div>

    <!-- 研报摘要 -->
    <div v-show="store.tab==='research'" class="space-y-4">
      <div v-if="!store.summary && !store.loading" class="text-center text-[#8fa5c6] py-20 text-sm">请先搜索个股后生成研报摘要</div>
      <div v-if="store.loading" class="text-center text-[#8fa5c6] py-10">AI 处理中...</div>
      <div v-if="store.summary" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-4">
        <div class="flex items-center gap-3">
          <h3 class="text-sm font-semibold text-white">研报摘要</h3>
          <span v-if="store.summary.rating" class="text-xs px-2 py-0.5 rounded" :class="store.summary.rating.includes('买入')?'bg-[#05b169]/20 text-[#05b169]':store.summary.rating.includes('卖出')?'bg-[#cf202f]/20 text-[#cf202f]':'bg-[#f59e0b]/20 text-[#f59e0b]'">{{ store.summary.rating }}</span>
        </div>
        <p class="text-sm text-[#c5d0e0] leading-relaxed">{{ store.summary.content }}</p>
        <div v-if="store.summary.key_points?.length">
          <h4 class="text-xs text-[#8fa5c6] mb-2">关键要点</h4>
          <ul class="space-y-1">
            <li v-for="(p,i) in store.summary.key_points" :key="i" class="text-sm text-[#c5d0e0] flex gap-2">
              <span class="text-[#0052ff]">•</span> {{ p }}
            </li>
          </ul>
        </div>
      </div>
      <div v-if="store.code" class="text-center">
        <button @click="doSummary" :disabled="store.loading" class="bg-[#0052ff] text-white px-6 py-2 rounded-full text-sm font-medium hover:opacity-90 disabled:opacity-50">{{ store.loading?'生成中...':'生成研报摘要' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useSentimentStore } from "../stores/sentiment";

const route = useRoute();
const router = useRouter();
const store = useSentimentStore();
const searchCode = ref("");

const tabs = [
  { key: "news", label: "个股舆情" },
  { key: "hot", label: "市场热点" },
  { key: "research", label: "研报摘要" },
];

function search() {
  const c = searchCode.value.trim();
  if (!c) return;
  router.replace(`/sentiment/${c}`);
}

async function load(code: string) {
  searchCode.value = code;
  await store.fetchNews(code);
}

function switchTab(t: string) {
  store.tab = t;
  if (t === "hot" && !store.marketNews) store.fetchMarketNews();
}

async function doAnalyze() {
  if (!store.news) return;
  const texts = store.news.items.map((n: any) => n.title);
  await store.analyze(store.code, texts);
}

async function doSummary() {
  await store.summarize(store.code);
}

onMounted(() => {
  const code = route.params.code as string;
  if (code) load(code);
});
</script>
