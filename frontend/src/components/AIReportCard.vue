<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-white">AI 综合研报</h3>
      <button @click="('refresh')" class="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white" :disabled="loading">
        {{ loading ? '生成中...' : '刷新' }}
      </button>
    </div>
    <div v-if="loading" class="text-center py-8 text-blue-300 text-sm">AI 正在分析中...</div>
    <div v-else-if="report" class="prose prose-sm prose-invert max-w-none">
      <div class="text-green-400 text-sm font-semibold mb-2">{{ report.summary }}</div>
      <pre class="text-sm text-blue-200 whitespace-pre-wrap font-sans">{{ report.content }}</pre>
    </div>
    <div v-else class="text-center py-8 text-gray-500 text-sm">点击刷新生成 AI 研报</div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ report: any; loading: boolean }>();
defineEmits<{ refresh: [] }>();
</script>
