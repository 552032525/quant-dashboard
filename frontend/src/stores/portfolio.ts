import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const usePortfolioStore = defineStore("portfolio", () => {
  const positions = ref<any[]>([]); const summary = ref<any>(null); const error = ref("");
  async function fetchAll() {
    error.value = "";
    try {
      positions.value = await api.portfolio.list();
      summary.value = await api.portfolio.summary();
    } catch (e: any) { error.value = e.message || "数据获取失败"; }
  }
  async function add(data: { symbol_code: string; quantity: number; cost_price: number }) {
    error.value = "";
    try { await api.portfolio.create(data); await fetchAll(); } catch (e: any) { error.value = e.message || "添加失败"; }
  }
  async function remove(id: number) {
    error.value = "";
    try { await api.portfolio.delete(id); await fetchAll(); } catch (e: any) { error.value = e.message || "删除失败"; }
  }
  return { positions, summary, error, fetchAll, add, remove };
});
