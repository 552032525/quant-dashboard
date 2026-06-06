const BASE = "/api";
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || "请求失败"); }
  if (res.status === 204) return undefined as T;
  return res.json();
}
export const api = {
  market: {
    realtime: (code: string) => request<any>(`/market/realtime/${code}`),
    kline: (code: string, start?: string, end?: string, period = "daily") => {
      const params = new URLSearchParams({ period });
      if (start) params.set("start_date", start);
      if (end) params.set("end_date", end);
      return request<any[]>(`/market/kline/${code}?${params.toString()}`);
    },
    search: (keyword: string) => request<any[]>(`/market/search?keyword=${encodeURIComponent(keyword)}`),
  },
  portfolio: {
    list: () => request<any[]>("/portfolio"),
    create: (data: any) => request<any>("/portfolio", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: any) => request<any>(`/portfolio/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number) => request<void>(`/portfolio/${id}`, { method: "DELETE" }),
    summary: () => request<any>("/portfolio/summary"),
  },
  ai: {
    analyze: (code: string, days = 30) => request<any>("/ai/analyze", { method: "POST", body: JSON.stringify({ symbol_code: code, days }) }),
    chat: (message: string, code?: string) => request<any>("/ai/chat", { method: "POST", body: JSON.stringify({ message, symbol_code: code }) }),
  },
};
