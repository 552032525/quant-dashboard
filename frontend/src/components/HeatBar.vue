<template>
  <div v-if="data" class="flex gap-6 px-4 py-2 bg-surface border-b border-surface-2 text-xs text-text-secondary">
    <span>上涨 <b class="text-gain">{{ data.up_count }}</b></span>
    <span>下跌 <b class="text-loss">{{ data.down_count }}</b></span>
    <span>平盘 {{ data.flat_count }}</span>
    <span>成交额 <b class="text-text-primary">{{ data.total_volume }}亿</b></span>
    <span>北向 <b :class="data.north_flow >= 0 ? 'text-gain' : 'text-loss'">{{ data.north_flow >= 0 ? '+' : '' }}{{ data.north_flow }}亿</b></span>
  </div>
</template>
<script setup lang="ts">
defineProps<{ data: any }>();
</script>