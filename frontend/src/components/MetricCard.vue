<template>
  <div class="bg-surface rounded-xl p-3 border border-surface-2">
    <div class="text-text-secondary text-xs mb-1">{{ label }}</div>
    <div class="text-xl font-mono" :class="trend==='up'?'text-gain':trend==='down'?'text-loss':'text-text-primary'">{{ value.toFixed(decimals??2) }}</div>
    <div v-if="sub" class="text-xs mt-1" :class="trend==='up'?'text-gain':'text-loss'">{{ sub }}</div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ label: string; value: number; decimals?: number; sub?: string; trend?: "up"|"down"|"neutral" }>();
</script>
