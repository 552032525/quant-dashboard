import { createRouter, createWebHistory } from "vue-router";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "market", component: () => import("../views/MarketView.vue") },
    { path: "/portfolio", name: "portfolio", component: () => import("../views/PortfolioView.vue") },
    { path: "/ai", name: "ai", component: () => import("../views/AIChatView.vue") },
  ],
});
export default router;
