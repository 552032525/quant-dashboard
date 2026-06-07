import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useStockPickStore = defineStore("stockPick", () => {
  const loading = ref(false);
  const candidates = ref<any[]>([]);
  const strategies = ref<any[]>([]);
  const backtestResult = ref<any>(null);
  const compareResult = ref<any>(null);
  const filters = ref({ pe_max: 100, pe_min: 0, pb_max: 20, pb_min: 0, roe_min: 0 });

  async function screen(f: any) {
    loading.value = true;
    try {
      const r = await api.stockpick.screen(f);
      candidates.value = r.candidates || [];
    } catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }

  async function loadStrategies() {
    try { strategies.value = await api.stockpick.strategies(); } catch (e: any) {}
  }

  async function runBacktest(params: any) {
    loading.value = true;
    try { backtestResult.value = await api.stockpick.backtest(params); }
    catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }

  async function runCompare(params: any) {
    loading.value = true;
    try { compareResult.value = await api.stockpick.compare(params); }
    catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }

  return { loading, candidates, strategies, backtestResult, compareResult, filters, screen, loadStrategies, runBacktest, runCompare };
});
