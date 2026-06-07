import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from '../api';

export const useBehaviorStore = defineStore('behavior', () => {
  const data = ref<any>(null);
  const loading = ref(false);
  const error = ref('');

  async function fetch(code?: string) {
    loading.value = true;
    error.value = '';
    try {
      data.value = await api.behavior.analysis(code);
    } catch (e: any) {
      error.value = e.message || '获取失败';
    } finally {
      loading.value = false;
    }
  }

  return { data, loading, error, fetch };
});
