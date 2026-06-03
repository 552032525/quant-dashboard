import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useMarketStore = defineStore("market", () => {
  const activeSymbol = ref("600519"); const klineData = ref<any[]>([]); const quote = ref<any>(null); const loading = ref(false);
  async function fetchKline(code: string) { loading.value=true; try{klineData.value=await api.market.kline(code);quote.value=await api.market.realtime(code);activeSymbol.value=code;}finally{loading.value=false;} }
  return { activeSymbol, klineData, quote, loading, fetchKline };
});
