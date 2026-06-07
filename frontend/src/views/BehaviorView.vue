<template>
  <div class="p-3 md:p-6 max-w-7xl mx-auto h-full overflow-auto">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-semibold text-white">📋 交易行为分析</h2>
      <button @click="loadData" :disabled="store.loading"
        class="bg-[#0052ff] text-white px-4 py-1.5 rounded-full text-xs font-medium hover:opacity-90 disabled:opacity-50">
        {{ store.loading ? '加载中...' : '🔄 刷新' }}
      </button>
    </div>

    <div v-if="store.error" class="text-xs text-[#cf202f] mb-4 px-3 py-2 bg-[#cf202f]/10 rounded-lg">{{ store.error }}</div>

    <div v-if="store.loading" class="text-center text-[#8fa5c6] py-20 text-sm">加载中...</div>

    <template v-else-if="store.data">
      <!-- 汇总卡片 -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">总交易次数</div>
          <div class="text-lg font-bold text-white font-mono">{{ store.data.summary.total_trades }}</div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">总买入金额</div>
          <div class="text-lg font-bold text-[#4a90d9] font-mono">{{ fmtNum(store.data.summary.total_buy_amount) }}</div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">总卖出金额</div>
          <div class="text-lg font-bold text-[#f59e0b] font-mono">{{ fmtNum(store.data.summary.total_sell_amount) }}</div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">总盈亏</div>
          <div class="text-lg font-bold font-mono" :class="store.data.summary.total_profit>=0?'text-[#05b169]':'text-[#cf202f]'">
            {{ store.data.summary.total_profit>=0?'+':'' }}{{ fmtNum(store.data.summary.total_profit) }}
          </div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">整体胜率</div>
          <div class="text-lg font-bold font-mono" :class="store.data.summary.overall_win_rate>=50?'text-[#05b169]':'text-[#f59e0b]'">
            {{ store.data.summary.overall_win_rate }}%
          </div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-1">平均持股天数</div>
          <div class="text-lg font-bold text-white font-mono">{{ store.data.summary.avg_hold_days }}天</div>
        </div>
      </div>

      <!-- 最佳/最差股票 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
        <div v-if="store.data.summary.best_stock" class="bg-[#0f1a2e] rounded-lg border border-[#05b169]/30 p-4">
          <div class="text-xs text-[#05b169] mb-1">🏆 盈利最多</div>
          <div class="text-base font-bold text-white">{{ store.data.summary.best_stock.name }} ({{ store.data.summary.best_stock.code }})</div>
          <div class="text-sm font-mono text-[#05b169] mt-1">+{{ fmtNum(store.data.summary.best_stock.total_profit) }} ({{ store.data.summary.best_stock.profit_pct }}%)</div>
          <div class="text-xs text-[#8fa5c6] mt-1">交易{{ store.data.summary.best_stock.trade_count }}次 | 胜率{{ store.data.summary.best_stock.win_rate }}%</div>
        </div>
        <div v-if="store.data.summary.worst_stock" class="bg-[#0f1a2e] rounded-lg border border-[#cf202f]/30 p-4">
          <div class="text-xs text-[#cf202f] mb-1">💔 亏损最多</div>
          <div class="text-base font-bold text-white">{{ store.data.summary.worst_stock.name }} ({{ store.data.summary.worst_stock.code }})</div>
          <div class="text-sm font-mono text-[#cf202f] mt-1">{{ fmtNum(store.data.summary.worst_stock.total_profit) }} ({{ store.data.summary.worst_stock.profit_pct }}%)</div>
          <div class="text-xs text-[#8fa5c6] mt-1">交易{{ store.data.summary.worst_stock.trade_count }}次 | 胜率{{ store.data.summary.worst_stock.win_rate }}%</div>
        </div>
      </div>

      <!-- 图表行 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <h3 class="text-sm font-medium text-[#8fa5c6] mb-3">各股票盈亏金额</h3>
          <div ref="barRef" class="w-full h-[250px] md:h-[320px]"></div>
        </div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <h3 class="text-sm font-medium text-[#8fa5c6] mb-3">盈亏损分布</h3>
          <div ref="pieRef" class="w-full h-[250px] md:h-[320px]"></div>
        </div>
      </div>

      <!-- 股票分析表格 -->
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <div class="px-4 py-3 border-b border-[#1a314a]">
          <h3 class="text-sm font-medium text-[#8fa5c6]">股票分析明细</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead><tr class="border-b border-[#1a314a] text-[#8fa5c6] text-xs uppercase">
              <th class="text-left px-4 py-3">代码</th>
              <th class="text-left px-4 py-3">名称</th>
              <th class="text-right px-4 py-3">买入金额</th>
              <th class="text-right px-4 py-3">卖出金额</th>
              <th class="text-right px-4 py-3">交易次数</th>
              <th class="text-right px-4 py-3">平均持股(天)</th>
              <th class="text-right px-4 py-3">盈亏</th>
              <th class="text-right px-4 py-3">盈亏%</th>
              <th class="text-right px-4 py-3">胜率</th>
            </tr></thead>
            <tbody>
              <tr v-for="(s,i) in store.data.stocks" :key="s.code||i" class="border-b border-[#1a314a] hover:bg-[#132438] transition-colors">
                <td class="px-4 py-2.5 font-mono text-[#4a90d9]">{{ s.code }}</td>
                <td class="px-4 py-2.5 text-white">{{ s.name }}</td>
                <td class="px-4 py-2.5 text-right font-mono text-[#4a90d9]">{{ fmtNum(s.total_buy) }}</td>
                <td class="px-4 py-2.5 text-right font-mono text-[#f59e0b]">{{ fmtNum(s.total_sell) }}</td>
                <td class="px-4 py-2.5 text-right font-mono text-white">{{ s.trade_count }}</td>
                <td class="px-4 py-2.5 text-right font-mono text-white">{{ s.avg_hold_days }}</td>
                <td class="px-4 py-2.5 text-right font-mono" :class="s.total_profit>=0?'text-[#05b169]':'text-[#cf202f]'">
                  {{ s.total_profit>=0?'+':'' }}{{ fmtNum(s.total_profit) }}
                </td>
                <td class="px-4 py-2.5 text-right font-mono" :class="s.profit_pct>=0?'text-[#05b169]':'text-[#cf202f]'">
                  {{ s.profit_pct>=0?'+':'' }}{{ s.profit_pct }}%
                </td>
                <td class="px-4 py-2.5 text-right font-mono" :class="s.win_rate>=50?'text-[#05b169]':'text-[#f59e0b]'">
                  {{ s.win_rate }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else class="text-center text-[#8fa5c6] py-20 text-sm">暂无数据，请先添加交易记录</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import { useBehaviorStore } from '../stores/behavior';

const store = useBehaviorStore();
const barRef = ref<HTMLDivElement>();
const pieRef = ref<HTMLDivElement>();
let barChart: echarts.ECharts | null = null;
let pieChart: echarts.ECharts | null = null;

function fmtNum(v: number | null | undefined): string {
  if (v == null) return '--';
  return v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderCharts() {
  if (!store.data?.stocks?.length) return;

  const stocks = store.data.stocks;

  // 柱状图：各股票盈亏
  if (barRef.value) {
    if (!barChart) barChart = echarts.init(barRef.value);
    barChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#132438',
        borderColor: '#1a314a',
        textStyle: { color: '#f0f4f8' },
        formatter: (p: any) => {
          const d = p[0];
          return `${d.name}<br/>盈亏: ${d.value>=0?'+':''}${d.value.toFixed(2)}`;
        },
      },
      grid: { left: '3%', right: '4%', top: '8%', bottom: '5%', containLabel: true },
      xAxis: {
        type: 'category',
        data: stocks.map((s: any) => s.name),
        axisLine: { lineStyle: { color: '#1a314a' } },
        axisLabel: { color: '#8899aa', fontSize: 10, rotate: stocks.length > 8 ? 30 : 0 },
      },
      yAxis: {
        type: 'value',
        name: '盈亏金额',
        nameTextStyle: { color: '#8fa5c6', fontSize: 10 },
        axisLabel: { color: '#8899aa', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1a314a' } },
      },
      series: [{
        type: 'bar',
        data: stocks.map((s: any) => s.total_profit),
        itemStyle: {
          color: (params: any) => params.value >= 0 ? '#05b169' : '#cf202f',
          borderRadius: [4, 4, 0, 0],
        },
        barMaxWidth: 40,
      }],
    }, true);
  }

  // 饼图：盈亏损分布
  if (pieRef.value) {
    if (!pieChart) pieChart = echarts.init(pieRef.value);
    const totalWin = stocks.reduce((sum: number, s: any) => sum + s.win_count, 0);
    const totalLoss = stocks.reduce((sum: number, s: any) => sum + s.loss_count, 0);
    pieChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#132438',
        borderColor: '#1a314a',
        textStyle: { color: '#f0f4f8' },
        formatter: '{b}: {c} 次 ({d}%)',
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: { color: '#8fa5c6', fontSize: 11 },
      },
      series: [{
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['55%', '52%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#0f1a2e',
          borderWidth: 3,
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: '#8899aa',
          fontSize: 11,
        },
        emphasis: {
          label: { fontSize: 14, fontWeight: 'bold' },
        },
        data: [
          { value: totalWin, name: '盈利次数', itemStyle: { color: '#05b169' } },
          { value: totalLoss, name: '亏损次数', itemStyle: { color: '#cf202f' } },
        ],
      }],
    }, true);
  }
}

watch(() => store.data, () => { nextTick(() => renderCharts()); });

async function loadData() {
  await store.fetch();
  await nextTick();
  renderCharts();
}

function handleResize() {
  barChart?.resize();
  pieChart?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  barChart?.dispose();
  pieChart?.dispose();
  window.removeEventListener('resize', handleResize);
});
</script>