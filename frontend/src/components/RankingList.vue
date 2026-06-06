<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center gap-2 px-3 py-2">
      <span class="text-sm font-medium text-text-primary">涨跌排行</span>
      <button @click="$emit('toggle')" class="text-xs text-primary hover:opacity-80">{{ rankType === 'up' ? '涨幅榜' : '跌幅榜' }} ▸</button>
    </div>
    <div class="flex-1 overflow-auto">
      <div v-for="(item, i) in data" :key="item.code"
        @click="$emit('select', item.code)"
        class="flex items-center px-3 py-1.5 hover:bg-surface-2 cursor-pointer text-xs border-b border-surface-2">
        <span class="w-5 text-text-secondary">{{ i + 1 }}</span>
        <span class="flex-1 font-mono">{{ item.code }}</span>
        <span class="w-24 truncate">{{ item.name }}</span>
        <span class="w-16 text-right font-mono">{{ item.price?.toFixed(2) }}</span>
        <span class="w-20 text-right font-mono" :class="item.change_pct >= 0 ? 'text-gain' : 'text-loss'">
          {{ item.change_pct >= 0 ? '+' : '' }}{{ item.change_pct?.toFixed(2) }}%
        </span>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ data: any[]; rankType: string }>();
defineEmits<{ toggle: []; select: [code: string] }>();
</script>