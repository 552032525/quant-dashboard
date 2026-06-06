import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useMarketStore = defineStore("market", () => {
  const activeSymbol = ref("600519");
  const period = ref("daily");
  const klineData = ref<any[]>([]);
  const quote = ref<any>(null);
  const loading = ref(false);
  const error = ref("");
  const indexQuotes = ref<any[]>([]);
  const heat = ref<any>(null);
  const sectors = ref<any[]>([]);
  const rankings = ref<any[]>([]);
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
    try { indexQuotes.value = await api.market.index(); } catch {}
  }
  async function fetchHeat() {
    try { heat.value = await api.market.heat(); } catch {}
  }
  async function fetchSectors(type = "industry") {
    try { sectors.value = await api.market.sectors(type); } catch {}
  }
  async function fetchRankings(type = "up") {
    try { rankings.value = await api.market.rankings(type); } catch {}
  }
  async function fetchIntraday(code: string) {
    try { intradayData.value = await api.market.intraday(code); } catch {}
  }

  return { activeSymbol, period, klineData, quote, loading, error, indexQuotes, heat, sectors, rankings, intradayData, fetchKline, fetchIndex, fetchHeat, fetchSectors, fetchRankings, fetchIntraday };
});