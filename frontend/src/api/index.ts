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
    index: () => request<any[]>("/market/index"),
    heat: () => request<any>("/market/heat"),
    sectors: (type = "industry") => request<any[]>(`/market/sectors?type=${type}`),
    rankings: (type = "up", limit = 20) => request<any[]>(`/market/rankings?type=${type}&limit=${limit}`),
    intraday: (code: string) => request<any[]>(`/market/intraday/${code}`),
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
  fundamental: {
    overview: (code: string) => request<any>(`/fundamental/overview/${code}`),
    valuation: (code: string) => request<any>(`/fundamental/valuation/${code}`),
    risk: (code: string) => request<any>(`/fundamental/risk/${code}`),
    holders: (code: string) => request<any>(`/fundamental/holders/${code}`),
    report: (code: string) => request<any>("/fundamental/report", { method: "POST", body: JSON.stringify({ code }) }),
    chat: (code: string, message: string) => request<any>("/fundamental/chat", { method: "POST", body: JSON.stringify({ code, message }) }),
    compare: (codes: string[]) => request<any>("/fundamental/compare", { method: "POST", body: JSON.stringify({ codes: codes, indicators: ["revenue_growth", "roe", "pe", "debt_ratio"] }) }),
  },
  technical: {
    indicators: (code: string, period = "daily") => request<any>(`/technical/indicators/${code}?period=${period}`),
    anomaly: (code: string) => request<any>(`/technical/anomaly/${code}`),
    score: (code: string) => request<any>("/technical/score", { method: "POST", body: JSON.stringify({ code }) }),
    report: (code: string) => request<any>("/technical/report", { method: "POST", body: JSON.stringify({ code }) }),
  },
  fundflow: {
    stockFlow: (code: string) => request<any>(`/fundflow/stock/${code}`),
    northbound: () => request<any>("/fundflow/northbound"),
    northboundDaily: () => request<any>("/fundflow/northbound/daily"),
    sectors: () => request<any>("/fundflow/sectors"),
    market: () => request<any>("/fundflow/market"),
    report: (code: string) => request<any>("/fundflow/report", { method: "POST", body: JSON.stringify({ code }) }),
  },
  sentiment: {
    news: (code: string) => request<any>(`/sentiment/news/${code}`),
    marketNews: () => request<any>("/sentiment/market-news"),
    analyze: (code: string, texts?: string[]) => request<any>(`/sentiment/analyze/${code}`, { method: "POST", body: JSON.stringify({ texts }) }),
    summary: (code: string, content?: string) => request<any>("/sentiment/summary", { method: "POST", body: JSON.stringify({ code, content }) }),
  },
  stockpick: {
    screen: (filters: any) => request<any>("/stockpick/screen", { method: "POST", body: JSON.stringify(filters) }),
    backtest: (params: any) => request<any>("/stockpick/backtest", { method: "POST", body: JSON.stringify(params) }),
    strategies: () => request<any[]>("/stockpick/strategies"),
  },
  risk: {
    checkStock: (code: string) => request<any>(`/risk/stock/${code}`),
    marketRisk: () => request<any>("/risk/market"),
    checkPortfolio: (positions: any[]) => request<any[]>("/risk/portfolio", { method: "POST", body: JSON.stringify({ positions }) }),
  },
  rebalance: {
    advice: (positions: any[]) => request<any>("/rebalance/advice", { method: "POST", body: JSON.stringify({ positions }) }),
  },
  review: {
    daily: () => request<any>("/review/daily", { method: "POST" }),
    stock: (code: string) => request<any>(`/review/stock/${code}`, { method: "POST" }),
    weekly: () => request<any>("/review/weekly", { method: "POST" }),
  },
  monitor: {
    watchlist: () => request<any[]>("/monitor/watchlist"),
    addWatch: (code: string) => request<any>(`/monitor/watchlist/${code}`, { method: "POST" }),
    removeWatch: (code: string) => request<any>(`/monitor/watchlist/${code}`, { method: "DELETE" }),
    alerts: () => request<any[]>("/monitor/alerts"),
    createAlert: (rule: any) => request<any>("/monitor/alerts", { method: "POST", body: JSON.stringify(rule) }),
    deleteAlert: (id: number) => request<any>(`/monitor/alerts/${id}`, { method: "DELETE" }),
    checkAlerts: () => request<any[]>("/monitor/check"),
    summary: () => request<any>("/monitor/summary"),
  },
};
