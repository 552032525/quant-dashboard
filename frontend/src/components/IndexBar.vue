<template>
  <div class="bg-surface border-b border-surface-2">
    <!-- 指数行情行 -->
    <div class="flex items-center gap-6 px-4 py-3">
      <div v-for="idx in data" :key="idx.code" class="flex items-center gap-2 text-sm">
        <span class="text-text-secondary">{{ idx.name }}</span>
        <span class="font-mono text-text-primary">{{ idx.price?.toFixed(2) }}</span>
        <span class="font-mono text-xs" :class="idx.change_pct >= 0 ? 'text-gain' : 'text-loss'">
          {{ idx.change_pct >= 0 ? '+' : '' }}{{ idx.change_pct?.toFixed(2) }}%
        </span>
      </div>
      <button
        v-if="breadth"
        @click="expanded = !expanded"
        class="ml-auto text-xs text-text-secondary hover:text-text-primary transition-colors flex items-center gap-1"
      >
        <span>市场广度</span>
        <span class="transform transition-transform" :class="expanded ? 'rotate-180' : ''">▾</span>
      </button>
    </div>

    <!-- 市场广度面板 -->
    <div v-if="breadth && expanded" class="px-4 pb-3 border-t border-surface-2 pt-3">
      <!-- 涨跌比进度条 -->
      <div class="flex items-center gap-2 mb-3">
        <span class="text-xs text-gain font-mono">{{ breadth.up_count }}家涨</span>
        <div class="flex-1 h-2 rounded-full overflow-hidden flex bg-surface-2">
          <div
            class="h-full bg-gain transition-all duration-500"
            :style="{ width: breadth.ratio + '%' }"
          ></div>
          <div
            class="h-full bg-loss transition-all duration-500"
            :style="{ width: (100 - breadth.ratio) + '%' }"
          ></div>
        </div>
        <span class="text-xs text-loss font-mono">{{ breadth.down_count }}家跌</span>
      </div>

      <!-- 详细统计 -->
      <div class="grid grid-cols-4 gap-3">
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">上涨家数</div>
          <div class="text-sm font-mono text-gain">{{ breadth.up_count }}</div>
        </div>
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">下跌家数</div>
          <div class="text-sm font-mono text-loss">{{ breadth.down_count }}</div>
        </div>
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">平盘</div>
          <div class="text-sm font-mono text-text-secondary">{{ breadth.flat_count }}</div>
        </div>
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">涨跌比</div>
          <div class="text-sm font-mono" :class="breadth.ratio >= 50 ? 'text-gain' : 'text-loss'">{{ breadth.ratio }}%</div>
        </div>
      </div>

      <!-- 涨停跌停 + 成交额 -->
      <div class="grid grid-cols-3 gap-3 mt-2">
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">涨停</div>
          <div class="text-sm font-mono text-gain">{{ breadth.limit_up }}</div>
        </div>
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">跌停</div>
          <div class="text-sm font-mono text-loss">{{ breadth.limit_down }}</div>
        </div>
        <div class="bg-surface-2 rounded px-3 py-2">
          <div class="text-xs text-text-secondary">总成交额(亿)</div>
          <div class="text-sm font-mono text-text-primary">{{ breadth.total_volume }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
defineProps<{ data: any[]; breadth?: any }>();
const expanded = ref(false);
</script>
