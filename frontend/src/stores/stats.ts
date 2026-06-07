import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useStatsStore = defineStore("stats", () => {
  const dailyStats = ref<any[]>([]);
  const latest = ref<any>(null);
  const loading = ref(false);
  const error = ref("");

  async function fetchDaily(start?: string, end?: string) {
    loading.value = true; error.value = "";
    try {
      dailyStats.value = await api.stats.daily(start, end);
      // API 返回降序，反转为正序
      dailyStats.value.reverse();
    } catch (e: any) {
      error.value = e.message || "数据获取失败";
    } finally { loading.value = false; }
  }

  async function fetchLatest() {
    try { latest.value = await api.stats.latest(); }
    catch (e: any) { /* 404 正常，首次使用 */ }
  }

  async function createSnapshot() {
    error.value = "";
    try {
      await api.stats.snapshot();
      await Promise.all([fetchLatest(), fetchDaily()]);
    } catch (e: any) {
      error.value = e.response?.status === 409 ? "今日已有快照" : (e.message || "快照失败");
      throw e;
    }
  }

  return { dailyStats, latest, loading, error, fetchDaily, fetchLatest, createSnapshot };
});
