import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api";

export const useSentimentStore = defineStore("sentiment", () => {
  const code = ref("");
  const name = ref("");
  const loading = ref(false);
  const news = ref<any>(null);
  const marketNews = ref<any>(null);
  const sentiment = ref<any>(null);
  const summary = ref<any>(null);
  const tab = ref("news");

  async function fetchNews(c: string) {
    code.value = c;
    loading.value = true;
    try {
      news.value = await api.sentiment.news(c);
      name.value = news.value?.name || c;
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchMarketNews() {
    loading.value = true;
    try {
      marketNews.value = await api.sentiment.marketNews();
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function analyze(c: string, texts?: string[]) {
    loading.value = true;
    try {
      sentiment.value = await api.sentiment.analyze(c, texts);
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  async function summarize(c: string, content?: string) {
    loading.value = true;
    try {
      summary.value = await api.sentiment.summary(c, content);
    } catch (e: any) {
      console.error(e);
    } finally {
      loading.value = false;
    }
  }

  return {
    code, name, loading, tab,
    news, marketNews, sentiment, summary,
    fetchNews, fetchMarketNews, analyze, summarize,
  };
});
