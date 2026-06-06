import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useMarketStore = defineStore("market", () => {
  const activeSymbol = ref("600519"); const klineData = ref<any[]>([]); const quote = ref<any>(null); const loading = ref(false); const error = ref("");
  async function fetchKline(code: string) {
    loading.value = true; error.value = "";
    try {
      klineData.value = await api.market.kline(code);
      quote.value = await api.market.realtime(code);
      activeSymbol.value = code;
    } catch (e: any) {
      error.value = e.message || "数据获取失败";
    } finally { loading.value = false; }
  }
  return { activeSymbol, klineData, quote, loading, error, fetchKline };
});
