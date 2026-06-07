<template>
  <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3" v-if="data">
    <div class="text-xs font-medium text-[#8fa5c6] mb-2">📊 五档盘口</div>

    <!-- 卖盘 (asks 按价格升序 → 上方) -->
    <div class="space-y-0.5 mb-2">
      <div v-for="(a, i) in reversedAsks" :key="'a'+i" class="flex justify-between text-xs">
        <span class="text-[#cf202f] font-mono">{{ a.price.toFixed(2) }}</span>
        <span class="text-[#8fa5c6] font-mono">{{ formatVol(a.volume) }}</span>
        <div class="flex-1 mx-2 relative">
          <div class="absolute right-0 top-0 h-full bg-[#cf202f]/20 rounded" :style="{ width: barWidth(a.volume, maxVol) + '%' }"></div>
        </div>
        <span class="text-[#8fa5c6]">卖{{ asks.length - i }}</span>
      </div>
    </div>

    <!-- 当前价 -->
    <div class="text-center py-1.5 border-y border-[#1a314a] mb-2">
      <span class="text-lg font-bold text-white font-mono">{{ data.price?.toFixed(2) }}</span>
    </div>

    <!-- 买盘 (bids 按价格降序 → 下方) -->
    <div class="space-y-0.5">
      <div v-for="(b, i) in data.bids.slice(0, 5)" :key="'b'+i" class="flex justify-between text-xs">
        <span class="text-[#05b169] font-mono">{{ b.price.toFixed(2) }}</span>
        <span class="text-[#8fa5c6] font-mono">{{ formatVol(b.volume) }}</span>
        <div class="flex-1 mx-2 relative">
          <div class="absolute right-0 top-0 h-full bg-[#05b169]/20 rounded" :style="{ width: barWidth(b.volume, maxVol) + '%' }"></div>
        </div>
        <span class="text-[#8fa5c6]">买{{ i + 1 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ data: any }>();

const asks = computed(() => props.data?.asks || []);
const reversedAsks = computed(() => [...asks.value].reverse());

const maxVol = computed(() => {
  const all = [...(props.data?.bids || []), ...(props.data?.asks || [])];
  if (!all.length) return 1;
  return Math.max(...all.map((x: any) => x.volume));
});

function formatVol(v: number): string {
  if (v >= 10000) return (v / 10000).toFixed(1) + "万";
  return v.toString();
}

function barWidth(vol: number, max: number): number {
  return Math.min((vol / max) * 100, 100);
}
</script>
