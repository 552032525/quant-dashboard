import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useMarketStore = defineStore("market", () => {
  const activeSymbol = ref("600519");
  const period = ref("daily");
  const klineData = ref<any[]>([]);
  const quote = ref<any>(null);
  const loading = ref(false);
  const error = ref("");
  const indexQuotes = ref<any[]>([]);
  const indexError = ref("");
  const heat = ref<any>(null);
  const heatError = ref("");
  const sectors = ref<any[]>([]);
  const sectorsError = ref("");
  const rankings = ref<any[]>([]);
  const rankingsError = ref("");
  const intradayData = ref<any[]>([]);

  async function fetchKline(code: string, p?: string) {
    loading.value = true; error.value = "";
    const per = p || period.value;
    try {
      const [k, q] = await Promise.all([
        api.market.kline(code, undefined, undefined, per),
        api.market.realtime(code),
      ]);
      klineData.value = k; quote.value = q; activeSymbol.value = code; period.value = per;
    } catch (e: any) {
      error.value = e.message || "数据获取失败";
    } finally { loading.value = false; }
  }

  async function fetchIndex() {
    indexError.value = "";
    try { indexQuotes.value = await api.market.index(); } catch (e: any) { indexError.value = e.message || "指数数据获取失败"; }
  }
  async function fetchHeat() {
    heatError.value = "";
    try { heat.value = await api.market.heat(); } catch (e: any) { heatError.value = e.message || "市场热度获取失败"; }
  }
  async function fetchSectors(type = "industry") {
    sectorsError.value = "";
    try { sectors.value = await api.market.sectors(type); } catch (e: any) { sectorsError.value = e.message || "板块数据获取失败"; }
  }
  async function fetchRankings(type = "up") {
    rankingsError.value = "";
    try { rankings.value = await api.market.rankings(type); } catch (e: any) { rankingsError.value = e.message || "排行数据获取失败"; }
  }
  async function fetchIntraday(code: string) {
    try { intradayData.value = await api.market.intraday(code); } catch (e: any) { console.warn("分时数据获取失败:", e.message); }
  }

  return { activeSymbol, period, klineData, quote, loading, error,
    indexQuotes, indexError, heat, heatError, sectors, sectorsError, rankings, rankingsError, intradayData,
    fetchKline, fetchIndex, fetchHeat, fetchSectors, fetchRankings, fetchIntraday };
});
