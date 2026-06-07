import { createRouter, createWebHistory } from "vue-router";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "market", component: () => import("../views/MarketOverview.vue") },
    { path: "/stock/:code", name: "stock-detail", component: () => import("../views/MarketView.vue") },
    { path: "/portfolio", name: "portfolio", component: () => import("../views/PortfolioView.vue") },
    { path: "/fundamental/:code?", name: "fundamental", component: () => import("../views/FundamentalView.vue") },
    { path: "/ai", name: "ai", component: () => import("../views/AIChatView.vue") },
  ],
});
export default router;
