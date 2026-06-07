<template>
  <div class="p-4 bg-[#0f1a2e] rounded-lg border border-[#1a314a]">
    <h3 class="text-sm font-semibold text-white mb-3">横向对比</h3>
    <div v-if="!result" class="text-center py-4 text-gray-500 text-xs">添加股票并点击开始对比</div>
    <template v-else>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-[#1a314a]">
              <th class="p-2 text-left text-blue-300">指标</th>
              <th v-for="item in result.table" :key="item.code" class="p-2 text-right text-blue-300">{{ item.name }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in ['pe','pb','roe','debt_ratio','revenue_growth']" :key="key" class="border-b border-[#1a314a]">
              <td class="p-2 text-blue-300">{{ labels[key] }}</td>
              <td v-for="item in result.table" :key="item.code" class="p-2 text-right text-white">
                {{ item[key]?.toFixed?.(1) ?? item[key] }}{{ key === 'roe' || key === 'debt_ratio' || key === 'revenue_growth' ? '%' : '' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="result.ai_comment" class="mt-3 p-3 bg-[#162436] rounded text-xs text-blue-200">
        <div class="text-green-400 font-semibold mb-1">AI 点评</div>
        <pre class="whitespace-pre-wrap font-sans">{{ result.ai_comment }}</pre>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
defineProps<{ result: any }>();
const labels: Record<string, string> = { pe: "PE", pb: "PB", roe: "ROE", debt_ratio: "负债率", revenue_growth: "营收增速" };
</script>
