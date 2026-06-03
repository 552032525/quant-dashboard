<template>
  <div class="p-6 max-w-3xl mx-auto h-full flex flex-col">
    <h2 class="text-xl font-medium mb-4">AI 行情分析</h2>
    <div class="bg-surface rounded-xl p-4 mb-4 border border-surface-2">
      <div class="flex gap-3 items-center">
        <input v-model="code" placeholder="股票代码" class="bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm w-32 outline-none focus:ring-1 focus:ring-primary" />
        <button @click="analyze" :disabled="loading" class="bg-primary text-white px-5 py-2 rounded-pill text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50">{{ loading?'分析中...':'一键分析' }}</button>
      </div>
      <div v-if="result" class="mt-4 p-3 bg-surface-2 rounded-lg text-sm leading-relaxed">{{ result }}</div>
    </div>
    <div class="flex-1 bg-surface rounded-xl border border-surface-2 flex flex-col overflow-hidden">
      <div ref="box" class="flex-1 overflow-auto p-4 space-y-3">
        <div v-for="(m,i) in msgs" :key="i" :class="m.role==='user'?'text-right':''">
          <div :class="m.role==='user'?'bg-primary text-white ml-auto':'bg-surface-2 text-text-primary'" class="inline-block max-w-[80%] px-4 py-2 rounded-xl text-sm">{{ m.content }}</div>
        </div>
        <div v-if="!msgs.length" class="text-text-secondary text-sm text-center py-8">输入问题开始 AI 对话</div>
      </div>
      <div class="border-t border-surface-2 p-3 flex gap-2">
        <input v-model="input" @keyup.enter="chat" placeholder="输入问题..." class="flex-1 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <button @click="chat" class="bg-primary text-white px-4 py-2 rounded-pill text-sm hover:opacity-90 transition-opacity">发送</button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, nextTick } from "vue"; import { api } from "../api";
const code=ref("600519"); const loading=ref(false); const result=ref(""); const input=ref("");
const msgs=ref<{role:string;content:string}[]>([]); const box=ref<HTMLDivElement>();
async function analyze(){loading.value=true;try{const r=await api.ai.analyze(code.value);result.value=r.content;}finally{loading.value=false;}}
async function chat(){if(!input.value.trim())return;const msg=input.value.trim();msgs.value.push({role:"user",content:msg});input.value="";await nextTick();box.value?.scrollTo({top:box.value.scrollHeight,behavior:"smooth"});const r=await api.ai.chat(msg,code.value);msgs.value.push({role:"assistant",content:r.content});await nextTick();box.value?.scrollTo({top:box.value.scrollHeight,behavior:"smooth"});}
</script>
