import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useReviewStore = defineStore("review", () => {
  const loading = ref(false);
  const daily = ref<any>(null);
  const stock = ref<any>(null);
  const weekly = ref<any>(null);

  async function genDaily() { loading.value = true; try { daily.value = await api.review.daily(); } catch(e:any){} finally{loading.value=false;} }
  async function genStock(code: string) { loading.value = true; try { stock.value = await api.review.stock(code); } catch(e:any){} finally{loading.value=false;} }
  async function genWeekly() { loading.value = true; try { weekly.value = await api.review.weekly(); } catch(e:any){} finally{loading.value=false;} }

  return { loading, daily, stock, weekly, genDaily, genStock, genWeekly };
});

export const useMonitorStore = defineStore("monitor", () => {
  const loading = ref(false);
  const watchlist = ref<any[]>([]);
  const alerts = ref<any[]>([]);
  const alertEvents = ref<any[]>([]);
  const summary = ref<any>(null);

  async function fetchWatchlist() { try { watchlist.value = await api.monitor.watchlist(); } catch(e:any){} }
  async function addWatch(code: string) { await api.monitor.addWatch(code); await fetchWatchlist(); }
  async function removeWatch(code: string) { await api.monitor.removeWatch(code); await fetchWatchlist(); }
  async function fetchAlerts() { try { alerts.value = await api.monitor.alerts(); } catch(e:any){} }
  async function createAlert(rule: any) { await api.monitor.createAlert(rule); await fetchAlerts(); }
  async function deleteAlert(id: number) { await api.monitor.deleteAlert(id); await fetchAlerts(); }
  async function checkAlerts() { try { alertEvents.value = await api.monitor.checkAlerts(); } catch(e:any){} }
  async function fetchSummary() { try { summary.value = await api.monitor.summary(); } catch(e:any){} }

  return { loading, watchlist, alerts, alertEvents, summary, fetchWatchlist, addWatch, removeWatch, fetchAlerts, createAlert, deleteAlert, checkAlerts, fetchSummary };
});
