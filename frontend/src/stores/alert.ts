import { defineStore } from "pinia"; import { ref } from "vue"; import { api } from "../api";
export const useAlertStore = defineStore("alert", () => {
  const alerts = ref<any[]>([]);
  const events = ref<any[]>([]);
  const loading = ref(false);
  async function fetchAlerts() {
    loading.value = true;
    try { alerts.value = await api.monitor.alerts(); }
    catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }
  async function create(rule: any) {
    await api.monitor.createAlert(rule);
    await fetchAlerts();
  }
  async function remove(id: number) {
    await api.monitor.deleteAlert(id);
    await fetchAlerts();
  }
  async function check() {
    loading.value = true;
    try { events.value = await api.monitor.checkAlerts(); }
    catch (e: any) { console.error(e); }
    finally { loading.value = false; }
  }
  async function toggle(id: number, enabled: boolean) {
    await api.monitor.createAlert({ id, enabled });
    await fetchAlerts();
  }
  return { alerts, events, loading, fetchAlerts, create, remove, check, toggle };
});
