import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useTechnicalStore = defineStore("technical", () => {
  const code = ref("");
  const name = ref("");
  const loading = ref(false);
  const period = ref("daily");
  const indicators = ref<any>(null);
  const anomalies = ref<any>(null);
  const score = ref<any>(null);
  const report = ref<any>(null);

  async function fetchAll(c: string, p: string = "daily") {
    code.value = c;
    period.value = p;
    loading.value = true;
    try {
      const [ind, ano, sco] = await Promise.all([
        api.technical.indicators(c, p),
        api.technical.anomaly(c),
        api.technical.score(c),
      ]);
      indicators.value = ind;
      anomalies.value = ano;
      score.value = sco;
      name.value = sco.name || c;
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchReport(c: string) {
    loading.value = true;
    try {
      report.value = await api.technical.report(c);
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  return { code, name, loading, period, indicators, anomalies, score, report, fetchAll, fetchReport };
});
