import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useRiskStore = defineStore("risk", () => {
  const loading = ref(false);
  const stockRisk = ref<any>(null);
  const marketRisk = ref<any>(null);
  const portfolioRisks = ref<any[]>([]);

  async function checkStock(code: string) {
    loading.value = true;
    try { stockRisk.value = await api.risk.checkStock(code); }
    catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }

  async function fetchMarketRisk() {
    try { marketRisk.value = await api.risk.marketRisk(); }
    catch (e: any) {}
  }

  async function checkPortfolio(positions: any[]) {
    loading.value = true;
    try { portfolioRisks.value = await api.risk.checkPortfolio(positions); }
    catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }

  return { loading, stockRisk, marketRisk, portfolioRisks, checkStock, fetchMarketRisk, checkPortfolio };
});
