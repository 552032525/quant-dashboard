<template>
  <div class="p-6 max-w-7xl mx-auto h-full overflow-auto">
    <!-- 搜索栏 -->
    <div class="flex gap-3 mb-6 items-center">
      <h2 class="text-xl font-semibold text-white">🔍 个股深度分析</h2>
      <input v-model="code" @keyup.enter="search" placeholder="输入股票代码"
        class="bg-[#132438] text-white px-3 py-2 rounded-lg text-sm w-36 outline-none focus:ring-1 focus:ring-[#0052ff] border border-[#1a314a]" />
      <button @click="search" class="bg-[#0052ff] text-white px-4 py-2 rounded-full text-sm font-medium hover:opacity-90">分析</button>
    </div>

    <!-- 股票头 -->
    <div v-if="stockName" class="mb-4 flex items-center gap-3">
      <span class="text-lg font-bold text-white">{{ stockName }}</span>
      <span class="text-sm text-[#8fa5c6]">{{ code }}</span>
    </div>

    <!-- 四 Tab -->
    <div class="flex gap-1 mb-4 bg-[#0f1a2e] rounded-lg p-1 inline-flex flex-wrap">
      <button v-for="t in tabs" :key="t.key" @click="tab=t.key" :class="tab===t.key?'bg-[#0052ff] text-white':'text-[#8fa5c6] hover:text-white'" class="px-4 py-1.5 rounded-md text-sm transition-colors">{{ t.label }}</button>
    </div>

    <!-- === 技术面 === -->
    <div v-show="tab==='technical'" class="space-y-4">
      <div class="flex gap-2 mb-3">
        <button v-for="p in ['daily','weekly','monthly']" :key="p" @click="techPeriod=p;loadTechnical()" :class="techPeriod===p?'bg-[#0052ff] text-white':'text-[#8fa5c6]'" class="px-3 py-1 rounded text-xs">{{ {daily:'日K',weekly:'周K',monthly:'月K'}[p] }}</button>
      </div>
      <div v-if="tStore.indicators" class="space-y-4">
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3">
          <div ref="klineRef" class="w-full" style="height:320px"></div>
        </div>

        <!-- 盘口深度 -->
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-1">
            <DepthPanel :data="depthData" />
          </div>
          <div class="col-span-1 flex flex-col gap-2">
            <div ref="macdRef" class="w-full flex-1" style="min-height:180px"></div>
          </div>
        </div>
        <div ref="rsiRef" class="w-full" style="height:180px"></div>
        <div v-if="tStore.score" class="grid grid-cols-5 gap-3">
          <div v-for="m in scoreMetrics" :key="m.key" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">{{ m.label }}</div>
            <div class="text-lg font-bold" :class="m.color">{{ m.val(tStore.score) }}</div>
          </div>
        </div>
        <div v-if="tStore.report" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-sm text-[#c5d0e0] leading-relaxed">{{ tStore.report.content }}</div>
        </div>
        <div class="text-center">
          <button @click="tStore.fetchReport(code)" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm hover:opacity-90">AI 技术面研报</button>
        </div>
      </div>
      <div v-if="!tStore.indicators && !tStore.loading" class="text-center text-[#8fa5c6] py-20 text-sm">输入代码后加载技术指标</div>
    </div>

    <!-- === 基本面 === -->
    <div v-show="tab==='fundamental'" class="space-y-4">
      <div v-if="fStore.overview" class="space-y-4">
        <div ref="finRef" class="w-full" style="height:260px"></div>
        <div class="grid grid-cols-3 gap-3">
          <div v-for="m in finMetrics" :key="m.key" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">{{ m.label }}</div>
            <div class="text-lg font-bold" :class="m.color">{{ m.val }}</div>
          </div>
        </div>
        <div v-if="fStore.valuation" class="grid grid-cols-4 gap-3">
          <div v-for="v in valList" :key="v.key" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">{{ v.key }}</div>
            <div class="text-sm font-mono text-white">{{ fStore.valuation[v.key] }}</div>
          </div>
        </div>
        <div v-if="fStore.report" class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-4">
          <div class="text-sm text-[#c5d0e0] leading-relaxed">{{ fStore.report.content }}</div>
        </div>
        <div class="text-center">
          <button @click="fStore.fetchReport(code)" class="bg-[#0052ff] text-white px-5 py-2 rounded-full text-sm hover:opacity-90">AI 基本面研报</button>
        </div>
      </div>
      <div v-if="!fStore.overview && !fStore.loading" class="text-center text-[#8fa5c6] py-20 text-sm">加载中...</div>
    </div>

    <!-- === 资金流 === -->
    <div v-show="tab==='fundflow'" class="space-y-4">
      <div v-if="ffStore.stockFlow" class="space-y-4">
        <div ref="flowRef" class="w-full" style="height:260px"></div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
          <h3 class="text-sm font-semibold text-white p-4 pb-2">近20日资金流</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-xs text-[#8fa5c6]">
              <thead><tr class="border-b border-[#1a314a]">
                <th class="px-3 py-2 text-left">日期</th><th class="px-3 py-2 text-right">主力净流入</th><th class="px-3 py-2 text-right">超大单</th><th class="px-3 py-2 text-right">大单</th><th class="px-3 py-2 text-right">中单</th><th class="px-3 py-2 text-right">小单</th>
              </tr></thead>
              <tbody>
                <tr v-for="(f,i) in ffStore.stockFlow.flows.slice().reverse().slice(0,15)" :key="i" class="border-b border-[#1a314a] hover:bg-[#132438]">
                  <td class="px-3 py-1.5 font-mono">{{ f.date }}</td>
                  <td class="px-3 py-1.5 text-right font-mono" :class="f.main_net>=0?'text-[#05b169]':'text-[#cf202f]'">{{ f.main_net.toFixed(0) }}</td>
                  <td class="px-3 py-1.5 text-right font-mono">{{ f.super_large_net.toFixed(0) }}</td>
                  <td class="px-3 py-1.5 text-right font-mono">{{ f.large_net.toFixed(0) }}</td>
                  <td class="px-3 py-1.5 text-right font-mono">{{ f.mid_net.toFixed(0) }}</td>
                  <td class="px-3 py-1.5 text-right font-mono">{{ f.small_net.toFixed(0) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div v-if="!ffStore.stockFlow && !ffStore.loading" class="text-center text-[#8fa5c6] py-20 text-sm">加载中...</div>
    </div>

    <!-- === 舆情 === -->
    <div v-show="tab==='sentiment'" class="space-y-4">
      <div v-if="sStore.news" class="space-y-4">
        <div v-if="sStore.sentiment" class="grid grid-cols-5 gap-3">
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">舆情总分</div>
            <div class="text-xl font-bold" :class="sStore.sentiment.overall>0.2?'text-[#05b169]':sStore.sentiment.overall<-0.2?'text-[#cf202f]':'text-[#8fa5c6]'">{{ sStore.sentiment.overall.toFixed(2) }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">利好</div><div class="text-lg font-bold text-[#05b169]">{{ sStore.sentiment.positive_count }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">利空</div><div class="text-lg font-bold text-[#cf202f]">{{ sStore.sentiment.negative_count }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3 text-center">
            <div class="text-xs text-[#8fa5c6]">中性</div><div class="text-lg font-bold text-[#8fa5c6]">{{ sStore.sentiment.neutral_count }}</div>
          </div>
          <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] p-3">
            <div class="text-xs text-[#8fa5c6] mb-2">关键议题</div>
            <div class="flex flex-wrap gap-1"><span v-for="t in sStore.sentiment.key_topics" :key="t" class="bg-[#132438] text-[#8fa5c6] px-2 py-0.5 rounded text-xs">{{ t }}</span></div>
          </div>
        </div>
        <div class="flex gap-2"><button @click="doSentiment" class="bg-[#0052ff] text-white px-4 py-1.5 rounded-full text-xs hover:opacity-90">AI 情感分析</button></div>
        <div class="bg-[#0f1a2e] rounded-lg border border-[#1a314a] overflow-hidden">
          <h3 class="text-sm font-semibold text-white p-4 pb-2">相关资讯</h3>
          <div class="divide-y divide-[#1a314a]">
            <div v-for="(n,i) in sStore.news.items" :key="i" class="px-4 py-2.5 hover:bg-[#132438]">
              <div class="text-sm text-[#c5d0e0]">{{ n.title }}</div>
              <div class="text-xs text-[#8fa5c6] mt-1">{{ n.source }} · {{ n.time }}</div>
            </div>
            <div v-if="!sStore.news.items.length" class="px-4 py-8 text-center text-[#8fa5c6] text-sm">暂无资讯</div>
          </div>
        </div>
      </div>
      <div v-if="!sStore.news && !sStore.loading" class="text-center text-[#8fa5c6] py-20 text-sm">加载中...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTechnicalStore } from "../stores/technical";
import { useFundamentalStore } from "../stores/fundamental";
import { useFundFlowStore } from "../stores/fundFlow";
import { useSentimentStore } from "../stores/sentiment";
import * as echarts from "echarts";

const route = useRoute(); const router = useRouter();
const tStore = useTechnicalStore();
const fStore = useFundamentalStore();
const depthData = ref<any>(null);
const ffStore = useFundFlowStore();
const sStore = useSentimentStore();

const code = ref("");
const tab = ref("technical");
const techPeriod = ref("daily");
const stockName = ref("");

const tabs = [
  { key: "technical", label: "技术面" },
  { key: "fundamental", label: "基本面" },
  { key: "fundflow", label: "资金流向" },
  { key: "sentiment", label: "舆情分析" },
];

const scoreMetrics = [
  { key:"trend",label:"趋势",color:"text-[#3b82f6]",val:(s:any)=>s.trend },
  { key:"momentum",label:"动量",color:"text-[#f59e0b]",val:(s:any)=>s.momentum },
  { key:"volatility",label:"波动",color:"text-[#8b5cf6]",val:(s:any)=>s.volatility },
  { key:"volume_score",label:"量能",color:"text-[#ec4899]",val:(s:any)=>s.volume_score },
  { key:"total",label:"综合",color:"text-[#0052ff]",val:(s:any)=>s.total },
];

const valList = [{key:"pe"},{key:"pb"},{key:"ps"},{key:"roe"}];
const finMetrics:any = ref([]);

function search() { const c = code.value.trim(); if (c) router.replace(`/analysis/${c}`); }

async function loadAll(c: string) {
  stockName.value = "";
  await Promise.all([
    tStore.fetchAll(c, techPeriod.value),
    fStore.fetchAll(c),
    ffStore.fetchStockFlow(c),
    sStore.fetchNews(c),
  ]);
  stockName.value = tStore.name || fStore.name || ffStore.name || sStore.name || c;

  // 渲染图表
  nextTick(() => { renderKline(); renderMacd(); renderRsi(); renderFin(); renderFlow(); });
}

// --- ECharts 渲染 ---
let klineChart:any=null,macdChart:any=null,rsiChart:any=null,finChart:any=null,flowChart:any=null;
const klineRef=ref(),macdRef=ref(),rsiRef=ref(),finRef=ref(),flowRef=ref();

function renderKline() {
  if (!klineRef.value || !tStore.indicators) return;
  if (!klineChart) klineChart = echarts.init(klineRef.value);
  const d=tStore.indicators;
  klineChart.setOption({
    tooltip:{trigger:"axis"},
    grid:{left:60,right:20,top:20,bottom:40},
    xAxis:{type:"category",data:d.dates||[],axisLabel:{color:"#8fa5c6"}},
    yAxis:{type:"value",axisLabel:{color:"#8fa5c6"}},
    series:[
      {name:"MA5",type:"line",data:d.ma5||[],showSymbol:false,lineStyle:{color:"#f59e0b",width:1}},
      {name:"MA10",type:"line",data:d.ma10||[],showSymbol:false,lineStyle:{color:"#3b82f6",width:1}},
      {name:"MA20",type:"line",data:d.ma20||[],showSymbol:false,lineStyle:{color:"#ec4899",width:1}},
      {name:"MA60",type:"line",data:d.ma60||[],showSymbol:false,lineStyle:{color:"#22c55e",width:1}},
      {name:"BOLL上",type:"line",data:d.boll_up||[],showSymbol:false,lineStyle:{color:"#8fa5c6",width:1,type:"dashed"}},
      {name:"BOLL下",type:"line",data:d.boll_dn||[],showSymbol:false,lineStyle:{color:"#8fa5c6",width:1,type:"dashed"}},
    ],
  });
}
function renderMacd() {
  if (!macdRef.value || !tStore.indicators) return;
  if (!macdChart) macdChart = echarts.init(macdRef.value);
  const d=tStore.indicators;
  macdChart.setOption({
    tooltip:{trigger:"axis"},grid:{left:50,right:20,top:20,bottom:30},
    xAxis:{type:"category",data:d.dates||[],axisLabel:{color:"#8fa5c6"}},
    yAxis:{type:"value",axisLabel:{color:"#8fa5c6"}},
    series:[
      {name:"DIF",type:"line",data:d.macd_dif||[],showSymbol:false,itemStyle:{color:"#f59e0b"}},
      {name:"DEA",type:"line",data:d.macd_dea||[],showSymbol:false,itemStyle:{color:"#3b82f6"}},
      {name:"BAR",type:"bar",data:(d.macd_bar||[]).map((v:number)=>v>=0?v:v),itemStyle:{color:(p:any)=>p.value>=0?"#ef4444":"#22c55e"}},
    ],
  });
}
function renderRsi() {
  if (!rsiRef.value || !tStore.indicators) return;
  if (!rsiChart) rsiChart = echarts.init(rsiRef.value);
  const d=tStore.indicators;
  rsiChart.setOption({
    tooltip:{trigger:"axis"},legend:{data:["RSI6","RSI12","RSI24"],textStyle:{color:"#8fa5c6"}},
    grid:{left:50,right:20,top:40,bottom:30},
    xAxis:{type:"category",data:d.dates||[],axisLabel:{color:"#8fa5c6"}},
    yAxis:{type:"value",max:100,min:0,axisLabel:{color:"#8fa5c6"}},
    series:[
      {name:"RSI6",type:"line",data:d.rsi6||[],showSymbol:false,itemStyle:{color:"#f59e0b"}},
      {name:"RSI12",type:"line",data:d.rsi12||[],showSymbol:false,itemStyle:{color:"#3b82f6"}},
      {name:"RSI24",type:"line",data:d.rsi24||[],showSymbol:false,itemStyle:{color:"#8b5cf6"}},
    ],
  });
}
function renderFin() {
  if (!finRef.value || !fStore.overview) return;
  if (!finChart) finChart = echarts.init(finRef.value);
  const data=fStore.overview.data||[];
  const dates=data.map((d:any)=>d.date).reverse();
  const rev=data.map((d:any)=>d.revenue).reverse();
  const prf=data.map((d:any)=>d.net_profit).reverse();
  finChart.setOption({
    tooltip:{trigger:"axis"},legend:{data:["营收(亿)","净利润(亿)"],textStyle:{color:"#8fa5c6"},top:0},
    grid:{left:60,right:20,top:40,bottom:40},
    xAxis:{type:"category",data:dates,axisLabel:{color:"#8fa5c6",rotate:30}},
    yAxis:{type:"value",axisLabel:{color:"#8fa5c6"}},
    series:[
      {name:"营收(亿)",type:"bar",data:rev,itemStyle:{color:"#3b82f6"}},
      {name:"净利润(亿)",type:"bar",data:prf,itemStyle:{color:"#05b169"}},
    ],
  });
  // 更新财务指标
  const last=data[data.length-1]||{};
  finMetrics.value = [
    {key:"revenue",label:"营收(亿)",val:last.revenue?.toFixed(1)||"-",color:"text-white"},
    {key:"net_profit",label:"净利润(亿)",val:last.net_profit?.toFixed(1)||"-",color:last.net_profit>0?"text-[#05b169]":"text-[#cf202f]"},
    {key:"roe",label:"ROE%",val:last.roe?.toFixed(1)||"-",color:"text-[#f59e0b]"},
  ];
}
function renderFlow() {
  if (!flowRef.value || !ffStore.stockFlow?.flows?.length) return;
  if (!flowChart) flowChart = echarts.init(flowRef.value);
  const flows=ffStore.stockFlow.flows;
  flowChart.setOption({
    tooltip:{trigger:"axis"},legend:{data:["主力净流入","超大单"],textStyle:{color:"#8fa5c6"},top:0},
    grid:{left:60,right:20,top:40,bottom:40},
    xAxis:{type:"category",data:flows.map((f:any)=>f.date),axisLabel:{color:"#8fa5c6",rotate:30}},
    yAxis:{type:"value",axisLabel:{color:"#8fa5c6"}},
    series:[
      {name:"主力净流入",type:"bar",data:flows.map((f:any)=>f.main_net),itemStyle:{color:(p:any)=>p.value>=0?"#ef4444":"#22c55e"}},
      {name:"超大单",type:"line",data:flows.map((f:any)=>f.super_large_net),showSymbol:false,itemStyle:{color:"#f59e0b"}},
    ],
  });
}

async function loadTechnical() { await tStore.fetchAll(code.value, techPeriod.value); }
async function loadDepth() { try { depthData.value = await api.market.depth(code.value); } catch(e){} }

async function doSentiment() {
  if (!sStore.news) return;
  await sStore.analyze(code.value, sStore.news.items.map((n:any)=>n.title));
}

// Tab 切换时确保数据加载
watch(tab, (t) => {
  if (!code.value) return;
  if (t==="technical" && !tStore.indicators) loadTechnical();
  if (t==="fundamental" && !fStore.overview) fStore.fetchAll(code.value);
  if (t==="fundflow" && !ffStore.stockFlow) ffStore.fetchStockFlow(code.value);
  if (t==="sentiment" && !sStore.news) sStore.fetchNews(code.value);
});

watch(() => route.params.code, (c) => {
  if (c) { code.value = c as string; loadAll(c as string); }
});

onMounted(() => {
  const c = route.params.code as string;
  if (c) { code.value = c; loadAll(c); }
});
</script>

