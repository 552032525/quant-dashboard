<template>
  <div class="flex gap-6 px-4 py-3 bg-surface border-b border-surface-2">
    <div v-for="idx in data" :key="idx.code" class="flex items-center gap-2 text-sm">
      <span class="text-text-secondary">{{ idx.name }}</span>
      <span class="font-mono text-text-primary">{{ idx.price?.toFixed(2) }}</span>
      <span class="font-mono text-xs" :class="idx.change_pct >= 0 ? 'text-gain' : 'text-loss'">
        {{ idx.change_pct >= 0 ? '+' : '' }}{{ idx.change_pct?.toFixed(2) }}%
      </span>
    </div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ data: any[] }>();
</script>