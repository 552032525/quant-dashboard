import { createRouter, createWebHistory } from "vue-router";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "market", component: () => import("../views/MarketOverview.vue") },
    { path: "/stock/:code", name: "stock-detail", component: () => import("../views/MarketView.vue") },
    { path: "/analysis/:code?", name: "analysis", component: () => import("../views/StockAnalysis.vue") },
    { path: "/portfolio", name: "portfolio", component: () => import("../views/PortfolioView.vue") },
    { path: "/stockpick", name: "stockpick", component: () => import("../views/StockPickView.vue") },
    { path: "/stats", name: "stats", component: () => import("../views/StatsView.vue") },
    { path: "/alerts", name: "alerts", component: () => import("../views/AlertView.vue") },
    { path: "/behavior", name: "behavior", component: () => import("../views/BehaviorView.vue") },
    { path: "/ai", name: "ai", component: () => import("../views/AIAssistant.vue") },
    // 旧路由重定向
    { path: "/fundamental/:code?", redirect: (to:any) => `/analysis/${to.params.code||''}` },
    { path: "/technical/:code?", redirect: (to:any) => `/analysis/${to.params.code||''}` },
    { path: "/fundflow/:code?", redirect: (to:any) => `/analysis/${to.params.code||''}` },
    { path: "/sentiment/:code?", redirect: (to:any) => `/analysis/${to.params.code||''}` },
    { path: "/risk", redirect: "/portfolio" },
    { path: "/review", redirect: "/ai" },
    { path: "/monitor", redirect: "/" },
  ],
});
export default router;

