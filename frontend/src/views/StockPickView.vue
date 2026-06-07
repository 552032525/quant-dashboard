<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-6">🎯 AI 智能选股 & 策略回测</h2>

    <div class="flex gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- 多因子选股 -->
    <div v-show="tab==='screen'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 grid grid-cols-4 gap-3">
        <div>
          <label class="text-xs text-[#8fa5c6]">PE 上限</label>
          <input v-model.number="store.filters.pe_max" type="number" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">PB 上限</label>
          <input v-model.number="store.filters.pb_max" type="number" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">ROE 最低%</label>
          <input v-model.number="store.filters.roe_min" type="number" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div class="flex items-end">
          <button @click="doScreen" :disabled="store.loading" class="bg-[#0052ff] text-white px-5 py-1.5 rounded-full text-sm font-medium hover:opacity-90 w-full">开始选股</button>
        </div>
      </div>

      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <h3 class="text-sm font-semibold text-white p-4 pb-2">选股结果 ({{ store.candidates.length }} 只)</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-[#8fa5c6]">
            <thead><tr class="border-b border-[#1a314a]">
              <th class="px-4 py-2 text-left">代码</th><th class="px-4 py-2 text-left">名称</th>
              <th class="px-4 py-2 text-right">PE</th><th class="px-4 py-2 text-right">PB</th>
              <th class="px-4 py-2 text-right">ROE</th><th class="px-4 py-2 text-right">得分</th>
            </tr></thead>
            <tbody>
              <tr v-for="c in store.candidates" :key="c.code" class="border-b border-[#1a314a] hover:bg-[#132438]">
                <td class="px-4 py-2 font-mono text-[#0052ff]">{{ c.code }}</td>
                <td class="px-4 py-2">{{ c.name }}</td>
                <td class="px-4 py-2 text-right font-mono">{{ c.pe.toFixed(1) }}</td>
                <td class="px-4 py-2 text-right font-mono">{{ c.pb.toFixed(1) }}</td>
                <td class="px-4 py-2 text-right font-mono">{{ c.roe.toFixed(1) }}%</td>
                <td class="px-4 py-2 text-right font-mono text-[#f59e0b]">{{ c.score }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 策略回测 -->
    <div v-show="tab==='backtest'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4 grid grid-cols-4 gap-3">
        <div>
          <label class="text-xs text-[#8fa5c6]">股票代码</label>
          <input v-model="btCode" placeholder="600519" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">策略</label><br/>
          <select v-model="btStrategy" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]">
            <option value="ma_cross">双均线交叉</option>
            <option value="momentum">动量策略</option>
            <option value="grid">网格交易</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-[#8fa5c6]">开始日期</label>
          <input v-model="btStart" type="date" class="w-full bg-[#132438] text-white px-2 py-1.5 rounded text-sm mt-1 border border-[#1a314a]" />
        </div>
        <div class="flex items-end">
          <button @click="doBacktest" :disabled="store.loading" class="bg-[#0052ff] text-white px-5 py-1.5 rounded-full text-sm font-medium hover:opacity-90 w-full">开始回测</button>
        </div>
      </div>

      <div v-if="store.backtestResult" class="grid grid-cols-5 gap-3">
        <div v-for="m in metrics" :key="m.key" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
          <div class="text-xs text-[#8fa5c6] mb-1">{{ m.label }}</div>
          <div class="text-lg font-bold font-mono" :class="m.color(store.backtestResult[m.key])">{{ m.fmt(store.backtestResult[m.key]) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useStockPickStore } from "../stores/stockPick";

const store = useStockPickStore();
const tab = ref("screen");
const btCode = ref("600519");
const btStrategy = ref("ma_cross");
const btStart = ref("2025-01-01");

const tabs = [
  { key: "screen", label: "多因子选股" },
  { key: "backtest", label: "策略回测" },
];

const metrics = [
  { key: "total_return", label: "总收益率", fmt: (v:number)=>v.toFixed(1)+"%", color: (v:number)=>v>=0?"text-[#05b169]":"text-[#cf202f]" },
  { key: "annual_return", label: "年化收益", fmt: (v:number)=>v.toFixed(1)+"%", color: (v:number)=>v>=0?"text-[#05b169]":"text-[#cf202f]" },
  { key: "max_drawdown", label: "最大回撤", fmt: (v:number)=>v.toFixed(1)+"%", color: ()=> "text-[#cf202f]" },
  { key: "sharpe", label: "夏普比率", fmt: (v:number)=>v.toFixed(2), color: ()=> "text-[#f59e0b]" },
  { key: "win_rate", label: "胜率", fmt: (v:number)=>v.toFixed(1)+"%", color: (v:number)=>v>50?"text-[#05b169]":"text-[#cf202f]" },
];

function doScreen() { store.screen(store.filters); }
function doBacktest() { store.runBacktest({ code: btCode.value, strategy: btStrategy.value, start_date: btStart.value, end_date: "2026-06-08" }); }

onMounted(() => store.loadStrategies());
</script>
