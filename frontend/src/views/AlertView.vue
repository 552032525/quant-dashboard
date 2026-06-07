<template>
  <div class="p-3 md:p-6 max-w-7xl mx-auto h-full overflow-auto">
    <h2 class="text-xl font-semibold text-white mb-4">🔔 预警管理</h2>

    <div class="flex flex-wrap gap-1 mb-6 bg-[#0f1a2e] rounded-lg p-1 inline-flex">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-xs md:text-sm transition-colors">{{ t.label }}</button>
    </div>

    <div v-if="error" class="text-xs text-[#cf202f] mb-4 px-3 py-2 bg-[#cf202f]/10 rounded-lg">{{ error }}</div>

    <!-- Tab 1: 预警规则 -->
    <div v-show="tab==='rules'" class="space-y-4">
      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
        <h3 class="text-sm font-medium mb-3 text-[#8fa5c6]">新建预警</h3>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <input v-model="form.code" placeholder="股票代码" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none focus:ring-1 focus:ring-[#0052ff] w-full" />
          <input v-model="form.name" placeholder="股票名称" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none focus:ring-1 focus:ring-[#0052ff] w-full" />
          <select v-model="form.type" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none">
            <option value="price_break">价格突破</option>
            <option value="change_pct">涨跌幅</option>
          </select>
          <input v-model.number="form.threshold" type="number" step="0.01" placeholder="阈值" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none focus:ring-1 focus:ring-[#0052ff] w-full" />
          <select v-model="form.direction" class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm border border-[#1a314a] outline-none">
            <option value="above">向上突破</option>
            <option value="below">向下跌破</option>
          </select>
          <button @click="addAlert" :disabled="store.loading" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm font-medium hover:opacity-90 disabled:opacity-50">{{ store.loading ? '添加中...' : '添加' }}</button>
        </div>
      </div>

      <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
        <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead><tr class="border-b border-[#1a314a] text-[#8fa5c6] text-xs uppercase">
            <th class="text-left px-4 py-3">代码</th>
            <th class="text-left px-4 py-3">名称</th>
            <th class="text-left px-4 py-3">类型</th>
            <th class="text-right px-4 py-3">阈值</th>
            <th class="text-center px-4 py-3">方向</th>
            <th class="text-center px-4 py-3">状态</th>
            <th class="text-right px-4 py-3">操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="a in store.alerts" :key="a.id" class="border-b border-[#1a314a] hover:bg-[#132438] transition-colors">
              <td class="px-4 py-3 font-mono text-white">{{ a.code }}</td>
              <td class="px-4 py-3 text-white">{{ a.name }}</td>
              <td class="px-4 py-3 text-[#8fa5c6]">{{ typeLabel(a.type) }}</td>
              <td class="px-4 py-3 text-right font-mono text-white">{{ a.threshold }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="a.direction==='above'?'text-[#05b169]':'text-[#cf202f]'" class="text-xs">{{ a.direction==='above'?'↑ 向上':'↓ 向下' }}</span>
              </td>
              <td class="px-4 py-3 text-center">
                <button @click="store.toggle(a.id, !a.enabled)" :class="a.enabled?'bg-[#05b169]':'bg-[#4a5568]'" class="w-9 h-5 rounded-full relative transition-colors">
                  <span :class="a.enabled?'translate-x-4':'translate-x-0.5'" class="inline-block w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform"></span>
                </button>
              </td>
              <td class="px-4 py-3 text-right">
                <button @click="delAlert(a.id)" class="text-[#cf202f] hover:opacity-80 text-xs">删除</button>
              </td>
            </tr>
            <tr v-if="!store.alerts.length"><td colspan="7" class="px-4 py-8 text-center text-[#8fa5c6]">暂无预警规则</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab 2: 触发记录 -->
    <div v-show="tab==='events'" class="space-y-4">
      <button @click="checkAlerts" :disabled="store.loading" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm font-medium hover:opacity-90 disabled:opacity-50">{{ store.loading ? '检查中...' : '🔍 检查触发' }}</button>

      <div v-if="store.events.length" class="space-y-2">
        <div v-for="(e,i) in store.events" :key="i" class="bg-[#cf202f]/10 rounded-lg border border-[#cf202f]/30 p-3">
          <div class="flex items-center gap-2">
            <span class="text-xs text-[#cf202f]">🔔</span>
            <span class="text-sm text-white flex-1">{{ e.message || e.alert_message }}</span>
            <span class="text-xs text-[#8fa5c6] whitespace-nowrap">{{ e.time || e.trigger_time }}</span>
          </div>
          <div v-if="e.code" class="text-xs text-[#8fa5c6] mt-1 ml-6">
            <span class="font-mono">{{ e.code }}</span>
            <span v-if="e.name" class="ml-2">{{ e.name }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="!store.loading" class="text-center text-[#8fa5c6] py-16 text-sm">暂无触发</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { useAlertStore } from "../stores/alert";

const store = useAlertStore();
const tab = ref("rules");
const error = ref("");

const tabs = [
  { key: "rules", label: "预警规则" },
  { key: "events", label: "触发记录" },
];

const form = reactive({ code: "", name: "", type: "price_break", threshold: 0, direction: "above" });

function typeLabel(t: string) { return t === "price_break" ? "价格突破" : "涨跌幅"; }

async function addAlert() {
  if (!form.code || !form.threshold) return;
  error.value = "";
  try {
    await store.create({ code: form.code, name: form.name, type: form.type, threshold: form.threshold, direction: form.direction });
    form.code = ""; form.name = ""; form.threshold = 0;
  } catch (e: any) {
    error.value = "添加失败: " + (e.message || "未知错误");
  }
}

async function delAlert(id: number) {
  error.value = "";
  try { await store.remove(id); } catch (e: any) { error.value = "删除失败: " + (e.message || "未知错误"); }
}

async function checkAlerts() {
  error.value = "";
  try { await store.check(); } catch (e: any) { error.value = "检查失败: " + (e.message || "未知错误"); }
}

onMounted(async () => {
  try { await store.fetchAlerts(); } catch (e: any) { error.value = "加载失败: " + (e.message || "网络错误"); }
});
</script>


