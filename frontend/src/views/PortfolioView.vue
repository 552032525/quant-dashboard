<template>
  <div class="p-6">
    <h2 class="text-xl font-medium mb-4">持仓管理</h2>
    <div class="grid grid-cols-4 gap-3 mb-6" v-if="p.summary">
      <MetricCard label="总资产" :value="p.summary.total_assets" trend="neutral" />
      <MetricCard label="持仓市值" :value="p.summary.total_market_value" trend="neutral" />
      <MetricCard label="浮动盈亏" :value="p.summary.total_profit_loss" :trend="p.summary.total_profit_loss>=0?'up':'down'" />
      <MetricCard label="盈亏比例" :value="p.summary.total_profit_loss_pct" trend="neutral" />
    </div>
    <div class="bg-surface rounded-xl p-4 mb-4 border border-surface-2">
      <h3 class="text-sm font-medium mb-3 text-text-secondary">添加持仓</h3>
      <div class="flex gap-3">
        <input v-model="f.code" placeholder="股票代码" class="flex-1 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <input v-model.number="f.qty" type="number" placeholder="数量" class="w-24 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <input v-model.number="f.cost" type="number" step="0.01" placeholder="成本价" class="w-28 bg-surface-2 text-text-primary px-3 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-primary" />
        <button @click="add" class="bg-primary text-white px-5 py-2 rounded-pill text-sm font-medium hover:opacity-90 transition-opacity">添加</button>
      </div>
    </div>
    <div class="bg-surface rounded-xl border border-surface-2 overflow-hidden">
      <table class="w-full text-sm">
        <thead><tr class="border-b border-surface-2 text-text-secondary text-xs uppercase">
          <th class="text-left px-4 py-3">代码</th><th class="text-left px-4 py-3">名称</th><th class="text-right px-4 py-3">数量</th><th class="text-right px-4 py-3">成本价</th><th class="text-right px-4 py-3">操作</th>
        </tr></thead>
        <tbody>
          <tr v-for="pos in p.positions" :key="pos.id" class="border-b border-surface-2 hover:bg-surface-2 transition-colors">
            <td class="px-4 py-3 font-mono">{{ pos.symbol_code }}</td><td class="px-4 py-3">{{ pos.symbol_name }}</td>
            <td class="px-4 py-3 text-right font-mono">{{ pos.quantity }}</td><td class="px-4 py-3 text-right font-mono">{{ pos.cost_price?.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right"><button @click="del(pos.id)" class="text-loss hover:opacity-80 text-xs">删除</button></td>
          </tr>
          <tr v-if="!p.positions.length"><td colspan="5" class="px-4 py-8 text-center text-text-secondary">暂无持仓记录</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, onMounted } from "vue"; import { usePortfolioStore } from "../stores/portfolio"; import MetricCard from "../components/MetricCard.vue";
const p = usePortfolioStore(); const f = reactive({ code:"", qty:0, cost:0 });
async function add() { if(!f.code||f.qty<=0||f.cost<=0)return; await p.add({symbol_code:f.code,quantity:f.qty,cost_price:f.cost}); f.code="";f.qty=0;f.cost=0; }
async function del(id:number) { await p.remove(id); }
onMounted(()=>p.fetchAll());
</script>
