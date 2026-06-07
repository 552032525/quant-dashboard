<template>
  <div class="p-3 md:p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-6">🤖 AI 智能助手</h2>

    <div class="flex flex-wrap gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-xs md:text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- AI 对话 -->
    <div v-show="tab==='chat'" class="h-full flex flex-col max-h-[50vh] md:max-h-[calc(100vh-160px)]">
      <div class="flex gap-2 items-center mb-3">
        <input v-model="chatCode" placeholder="可选: 股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-28 border border-[#1a314a] outline-none" />
      </div>
      <div ref="chatBox" class="flex-1 overflow-auto space-y-3 mb-3">
        <div v-for="(m,i) in msgs" :key="i" :class="m.role==='user'?'text-right':''">
          <div :class="m.role==='user'?'bg-[#0052ff] text-white ml-auto':'bg-[#0f1a2e] text-[#c5d0e0] border border-[#1a314a]'" class="inline-block max-w-[80%] px-4 py-2 rounded-xl text-sm">{{ m.content }}</div>
        </div>
        <div v-if="!msgs.length" class="text-[#8fa5c6] text-sm text-center py-8">输入问题开始 AI 对话</div>
      </div>
      <div class="flex gap-2">
        <input v-model="input" @keyup.enter="chat" placeholder="输入问题..." class="flex-1 bg-[#132438] text-white px-4 py-2 rounded-lg text-sm border border-[#1a314a] outline-none" />
        <button @click="chat" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm hover:opacity-90">发送</button>
      </div>
    </div>

    <!-- 复盘 -->
    <div v-show="tab==='review'" class="space-y-4">
      <div class="flex gap-2">
        <button @click="genDaily" :disabled="loading" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm hover:opacity-90">每日复盘</button>
        <button @click="genWeekly" :disabled="loading" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm hover:opacity-90">周度总结</button>
      </div>
      <div v-if="daily" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-3">
        <h3 class="text-sm font-semibold text-white">📅 {{ daily.date }}</h3>
        <p class="text-sm text-[#c5d0e0] leading-relaxed whitespace-pre-wrap">{{ daily.content }}</p>
        <div v-if="daily.hot_sectors?.length" class="flex gap-2 flex-wrap">
          <span v-for="s in daily.hot_sectors" :key="s" class="bg-[#132438] text-[#f59e0b] px-2 py-0.5 rounded text-xs">{{ s }}</span>
        </div>
        <div v-if="daily.risk_alert" class="text-xs text-[#cf202f]">⚠ {{ daily.risk_alert }}</div>
      </div>
      <div v-if="weekly" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-3">
        <h3 class="text-sm font-semibold text-white">📊 {{ weekly.week_range }}</h3>
        <p class="text-sm text-[#c5d0e0] leading-relaxed">{{ weekly.content }}</p>
        <div v-if="weekly.key_events?.length" class="space-y-1">
          <div v-for="(e,i) in weekly.key_events" :key="i" class="text-xs text-[#8fa5c6] flex gap-2"><span class="text-[#0052ff]">•</span>{{ e }}</div>
        </div>
      </div>
    </div>

    <!-- 个股调研 -->
    <div v-show="tab==='research'" class="space-y-4">
      <div class="flex flex-col md:flex-row gap-3">
        <input v-model="researchCode" @keyup.enter="genResearch" placeholder="股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-full md:w-36 border border-[#1a314a] outline-none" />
        <button @click="genResearch" :disabled="loading" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm hover:opacity-90">生成调研报告</button>
      </div>
      <div v-if="stockReview" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-5 space-y-3">
        <div class="flex items-center gap-3">
          <h3 class="text-sm font-semibold text-white">{{ stockReview.name }} ({{ stockReview.code }})</h3>
          <span :class="ratingBadge(stockReview.overall_rating)" class="text-xs px-2 py-0.5 rounded">{{ stockReview.overall_rating }}</span>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-[#132438] rounded p-3"><div class="text-xs text-[#8fa5c6] mb-1">技术面</div><div class="text-sm text-[#c5d0e0]">{{ stockReview.technical_view }}</div></div>
          <div class="bg-[#132438] rounded p-3"><div class="text-xs text-[#8fa5c6] mb-1">基本面</div><div class="text-sm text-[#c5d0e0]">{{ stockReview.fundamental_view }}</div></div>
        </div>
        <p class="text-sm text-[#c5d0e0] leading-relaxed">{{ stockReview.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";
import { api } from "../api";

const tab = ref("chat");
const tabs = [
  { key: "chat", label: "AI 对话" },
  { key: "review", label: "智能复盘" },
  { key: "research", label: "个股调研" },
];

// AI 对话
const msgs = ref<{role:string;content:string}[]>([]);
const input = ref(""); const chatCode = ref(""); const chatBox = ref<HTMLElement>();

async function chat() {
  if (!input.value.trim()) return;
  msgs.value.push({role:"user",content:input.value.trim()});
  const q = input.value.trim(); input.value = "";
  await nextTick(); chatBox.value?.scrollTo({top:chatBox.value.scrollHeight,behavior:"smooth"});
  try {
    const r = await api.ai.chat(q, chatCode.value || undefined);
    msgs.value.push({role:"assistant",content:r.content||r});
  } catch(e:any) { msgs.value.push({role:"assistant",content:"请求失败: "+e.message}); }
  await nextTick(); chatBox.value?.scrollTo({top:chatBox.value.scrollHeight,behavior:"smooth"});
}

// 复盘
const loading = ref(false);
const daily = ref<any>(null); const weekly = ref<any>(null);

async function genDaily() { loading.value=true; try { daily.value = await api.review.daily(); } catch(e:any){} finally{loading.value=false;} }
async function genWeekly() { loading.value=true; try { weekly.value = await api.review.weekly(); } catch(e:any){} finally{loading.value=false;} }

// 个股调研
const researchCode = ref(""); const stockReview = ref<any>(null);
async function genResearch() { const c=researchCode.value.trim(); if(!c)return; loading.value=true; try { stockReview.value = await api.review.stock(c); } catch(e:any){} finally{loading.value=false;} }

function ratingBadge(r:string) {
  if (r.includes("买入")||r.includes("推荐")) return "bg-[#05b169]/20 text-[#05b169]";
  if (r.includes("卖出")||r.includes("回避")) return "bg-[#cf202f]/20 text-[#cf202f]";
  return "bg-[#f59e0b]/20 text-[#f59e0b]";
}
</script>


