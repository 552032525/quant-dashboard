import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const usePortfolioStore = defineStore("portfolio", () => {
  const positions = ref<any[]>([]); const summary = ref<any>(null);
  async function fetchAll() { positions.value=await api.portfolio.list(); summary.value=await api.portfolio.summary(); }
  async function add(data:{symbol_code:string;quantity:number;cost_price:number}) { await api.portfolio.create(data); await fetchAll(); }
  async function remove(id:number) { await api.portfolio.delete(id); await fetchAll(); }
  return { positions, summary, fetchAll, add, remove };
});
