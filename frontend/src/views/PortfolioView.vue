<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-4">💼 持仓 & 风控</h2>

    <div class="flex gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <div v-if="portfolioError" class="text-xs text-[#cf202f] mb-4 px-3 py-2 bg-[#cf202f]/10 rounded-lg">{{ portfolioError }}</div>

    <!-- 持仓管理 -->
    <div v-show="tab==='manage'" class="space-y-4">
      <div class="grid grid-cols-4 gap-3" v-if="p.summary">
        <MetricCard label="总资产" :value="p.summary.total_assets" trend="neutral" />
        <MetricCard label="持仓市值" :value="p.summary.total_market_value" trend="neutral" />
        <MetricCard label="浮动盈亏" :value="p.summary.total_profit_loss" :trend="p.summary.total_profit_loss>=0?'up':'down'" />
        <MetricCard label="盈亏比例" :value="p.summary.total_profit_loss_pct" trend="neutral" />
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
        <h3 class="text-sm font-medium mb-3 text-[#8fa5c6]">添加持仓</h3>
        <div class="flex gap-3">
          <input v-model="f.code" placeholder="股票代码" class="flex-1 bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none focus:ring-1 focus:ring-[#0052ff]" />
          <input v-model.number="f.qty" type="number" placeholder="数量" class="w-24 bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none" />
          <input v-model.number="f.cost" type="number" step="0.01" placeholder="成本价" class="w-28 bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none" />
          <button @click="add" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm font-medium hover:opacity-90">添加</button>
        </div>
      </div>
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <table class="w-full text-sm">
          <thead><tr class="border-b border-[#1a314a] text-[#8fa5c6] text-xs uppercase">
            <th class="text-left px-4 py-3">代码</th><th class="text-left px-4 py-3">名称</th><th class="text-right px-4 py-3">数量</th><th class="text-right px-4 py-3">成本价</th><th class="text-right px-4 py-3">现价</th><th class="text-right px-4 py-3">盈亏</th><th class="text-right px-4 py-3">操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="pos in p.positions" :key="pos.id" class="border-b border-[#1a314a] hover:bg-[#132438] transition-colors">
              <td class="px-4 py-3 font-mono text-white">{{ pos.symbol_code }}</td><td class="px-4 py-3 text-white">{{ pos.symbol_name }}</td>
              <td class="px-4 py-3 text-right font-mono text-white">{{ pos.quantity }}</td><td class="px-4 py-3 text-right font-mono text-white">{{ pos.cost_price?.toFixed(2) }}</td>
              <td class="px-4 py-3 text-right font-mono text-[#8fa5c6]">{{ pos.current_price?.toFixed(2) || '--' }}</td>
              <td class="px-4 py-3 text-right font-mono" :class="(pos.profit_loss||0)>=0?'text-[#05b169]':'text-[#cf202f]'">
                {{ pos.profit_loss != null ? (pos.profit_loss>=0?'+':'') + pos.profit_loss.toFixed(2) : '--' }}
                <span class="text-xs">{{ pos.profit_loss_pct != null ? ' (' + (pos.profit_loss_pct>=0?'+':'') + pos.profit_loss_pct.toFixed(2) + '%)' : '' }}</span>
              </td>
              <td class="px-4 py-3 text-right"><button @click="del(pos.id)" class="text-[#cf202f] hover:opacity-80 text-xs">删除</button></td>
            </tr>
            <tr v-if="!p.positions.length"><td colspan="7" class="px-4 py-8 text-center text-[#8fa5c6]">暂无持仓记录</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 风控检查 -->
    <div v-show="tab==='risk'" class="space-y-4">
      <button @click="checkRisks" :disabled="riskLoading" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm hover:opacity-90">{{ riskLoading?'检查中...':'执行持仓风控检查' }}</button>
      <div v-if="riskError" class="text-xs text-[#cf202f] px-3 py-2 bg-[#cf202f]/10 rounded-lg">{{ riskError }}</div>
      <div v-if="riskResults.length" class="space-y-2">
        <div v-for="(r,i) in riskResults" :key="i" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="flex justify-between items-center">
            <div><span class="text-sm font-medium text-white">{{ r.name }}</span><span class="text-xs text-[#8fa5c6] ml-2">{{ r.code }}</span></div>
            <div><span v-if="r.risk_flags.length" class="text-xs text-[#cf202f]">⚠ 风险</span><span v-else class="text-xs text-[#05b169]">✓ 正常</span></div>
          </div>
          <div class="grid grid-cols-3 gap-2 mt-2 text-xs text-[#8fa5c6]">
            <div>止损价: {{ r.stop_loss_price.toFixed(2) }}</div>
            <div>止盈价: {{ r.take_profit_price.toFixed(2) }}</div>
            <div>权重: {{ r.weight_pct }}%</div>
          </div>
          <div v-if="r.risk_flags.length" class="mt-2"><div v-for="f in r.risk_flags" :key="f" class="text-xs text-[#cf202f]">{{ f }}</div></div>
        </div>
      </div>
      <div v-if="!p.positions.length" class="text-center text-[#8fa5c6] py-10 text-sm">暂无持仓数据</div>
    </div>

    <!-- AI 调仓建议 -->
    <div v-show="tab==='advice'" class="space-y-4">
      <button @click="getAdvice" :disabled="adviceLoading" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm hover:opacity-90">{{ adviceLoading?'生成中...':'生成 AI 调仓建议' }}</button>
      <div v-if="adviceError" class="text-xs text-[#cf202f] px-3 py-2 bg-[#cf202f]/10 rounded-lg">{{ adviceError }}</div>
      <div v-if="adviceResult" class="space-y-4">
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-xs text-[#8fa5c6] mb-2">总体建议</div>
          <div class="text-sm text-[#c5d0e0]">{{ adviceResult.summary }}</div>
        </div>
        <div v-for="(a,i) in adviceResult.advice" :key="i" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 flex justify-between items-center">
          <div>
            <span class="text-sm font-medium text-white">{{ a.name }}</span>
            <span class="text-xs text-[#8fa5c6] ml-2">{{ a.code }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span :class="actionColor(a.action)" class="text-xs px-2 py-0.5 rounded">{{ actionLabel(a.action) }}</span>
            <span class="text-xs text-[#8fa5c6]">建议权重: {{ a.suggested_weight }}%</span>
          </div>
          <div class="text-xs text-[#8fa5c6] max-w-xs text-right">{{ a.reason }}</div>
        </div>
      </div>
      <div v-if="!p.positions.length" class="text-center text-[#8fa5c6] py-10 text-sm">暂无持仓数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { usePortfolioStore } from "../stores/portfolio";
import { api } from "../api";
import MetricCard from "../components/MetricCard.vue";

const p = usePortfolioStore();
const f = reactive({ code:"", qty:0, cost:0 });
const tab = ref("manage");
const portfolioError = ref("");

const tabs = [
  { key: "manage", label: "持仓管理" },
  { key: "risk", label: "风控检查" },
  { key: "advice", label: "AI 调仓" },
];

async function add() {
  if(!f.code||f.qty<=0||f.cost<=0) return;
  portfolioError.value = "";
  try {
    await p.add({symbol_code:f.code,quantity:f.qty,cost_price:f.cost});
    f.code="";f.qty=0;f.cost=0;
  } catch(e: any) {
    portfolioError.value = "添加失败: " + (e.message || "未知错误");
  }
}
async function del(id:number) {
  portfolioError.value = "";
  try { await p.remove(id); } catch(e: any) { portfolioError.value = "删除失败: " + (e.message || "未知错误"); }
}

// 风控
const riskLoading = ref(false); const riskResults = ref<any[]>([]); const riskError = ref("");
async function checkRisks() {
  if (!p.positions.length) return;
  riskLoading.value = true; riskError.value = "";
  try {
    const positions = p.positions.map(pos => ({ code: pos.symbol_code, name: pos.symbol_name, cost_price: pos.cost_price, weight_pct: 0 }));
    riskResults.value = await api.risk.checkPortfolio(positions);
  } catch(e:any) {
    riskError.value = "风控检查失败: " + (e.message || "网络错误");
  } finally { riskLoading.value = false; }
}

// AI 调仓
const adviceLoading = ref(false); const adviceResult = ref<any>(null); const adviceError = ref("");
async function getAdvice() {
  if (!p.positions.length) return;
  adviceLoading.value = true; adviceError.value = "";
  try {
    const positions = p.positions.map(pos => ({ code: pos.symbol_code, name: pos.symbol_name, quantity: pos.quantity, cost_price: pos.cost_price }));
    adviceResult.value = await api.rebalance.advice(positions);
  } catch(e:any) {
    adviceError.value = "调仓建议生成失败: " + (e.message || "网络错误");
  } finally { adviceLoading.value = false; }
}

function actionColor(a:string) { return a==='reduce'||a==='sell'?'bg-[#cf202f]/20 text-[#cf202f]':a==='buy_more'||a==='add'?'bg-[#05b169]/20 text-[#05b169]':'bg-[#f59e0b]/20 text-[#f59e0b]'; }
function actionLabel(a:string) { return ({reduce:'减仓',buy_more:'加仓',add:'买入',hold:'持有'})[a]||a; }

onMounted(async () => {
  try {
    await p.fetchAll();
  } catch(e: any) {
    portfolioError.value = "加载持仓数据失败: " + (e.message || "网络错误");
  }
});
</script>
