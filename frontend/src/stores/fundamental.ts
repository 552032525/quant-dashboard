import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useFundamentalStore = defineStore("fundamental", () => {
  const code = ref("");
  const name = ref("");
  const loading = ref(false);
  const overview = ref<any>(null);
  const valuation = ref<any>(null);
  const risk = ref<any>(null);
  const holders = ref<any>(null);
  const report = ref<any>(null);
  const compareResult = ref<any>(null);

  async function fetchAll(c: string) {
    code.value = c;
    loading.value = true;
    try {
      const [ov, val, rsk, hld] = await Promise.all([
        api.fundamental.overview(c),
        api.fundamental.valuation(c),
        api.fundamental.risk(c),
        api.fundamental.holders(c),
      ]);
      overview.value = ov;
      valuation.value = val;
      risk.value = rsk;
      holders.value = hld;
      name.value = val.name || ov.name || c;
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchReport(c: string) {
    loading.value = true;
    try {
      report.value = await api.fundamental.report(c);
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function chat(c: string, msg: string): Promise<string> {
    try {
      const resp = await api.fundamental.chat(c, msg);
      return resp.content || "";
    } catch (e: any) {
      return `错误: ${e.message}`;
    }
  }

  async function compare(codes: string[]) {
    loading.value = true;
    try {
      compareResult.value = await api.fundamental.compare(codes);
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  return { code, name, loading, overview, valuation, risk, holders, report, compareResult, fetchAll, fetchReport, chat, compare };
});
