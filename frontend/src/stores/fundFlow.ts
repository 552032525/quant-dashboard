import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useFundFlowStore = defineStore("fundFlow", () => {
  const code = ref("");
  const name = ref("");
  const loading = ref(false);
  const stockFlow = ref<any>(null);
  const northbound = ref<any>(null);
  const northboundDaily = ref<any>(null);
  const sectors = ref<any>(null);
  const market = ref<any>(null);
  const report = ref<any>(null);
  const tab = ref("stock");

  async function fetchStockFlow(c: string) {
    code.value = c;
    loading.value = true;
    try {
      stockFlow.value = await api.fundflow.stockFlow(c);
      name.value = stockFlow.value.name || c;
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchNorthbound() {
    loading.value = true;
    try {
      const [nb, nbDaily] = await Promise.all([
        api.fundflow.northbound(),
        api.fundflow.northboundDaily(),
      ]);
      northbound.value = nb;
      northboundDaily.value = nbDaily;
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchSectors() {
    loading.value = true;
    try {
      sectors.value = await api.fundflow.sectors();
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchMarket() {
    try {
      market.value = await api.fundflow.market();
    } catch (e: any) {
      console.error(e);
    }
  }

  async function fetchReport(c: string) {
    loading.value = true;
    try {
      report.value = await api.fundflow.report(c);
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  return {
    code, name, loading, tab,
    stockFlow, northbound, northboundDaily, sectors, market, report,
    fetchStockFlow, fetchNorthbound, fetchSectors, fetchMarket, fetchReport,
  };
});
