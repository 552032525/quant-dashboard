<template>
  <div class="flex h-screen">
    <nav class="hidden md:flex w-14 bg-[#132438] flex-col items-center py-4 gap-4 border-r border-[#1a314a] overflow-y-auto">
      <router-link to="/" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="行情">📈</router-link>
      <router-link to="/analysis" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="个股分析">🔍</router-link>
      <router-link to="/portfolio" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="持仓风控">💼</router-link>
      <router-link to="/alerts" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="预警管理">🔔</router-link>
      <router-link to="/ai" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="AI助手">🤖</router-link>
      <router-link to="/stockpick" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="智能选股">🎯</router-link>
      <router-link to="/stats" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="收益统计">📊</router-link>
      <router-link to="/behavior" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="交易分析">📋</router-link>
    </nav>
    <!-- 移动端底部导航 -->
      <nav class="flex md:hidden fixed bottom-0 left-0 right-0 bg-[#132438]/95 backdrop-blur border-t border-[#1a314a] z-50 justify-around py-2">
      <router-link to="/" class="flex flex-col items-center text-xs gap-0.5 text-[#8fa5c6]">📈<span>行情</span></router-link>
      <router-link to="/analysis" class="flex flex-col items-center text-xs gap-0.5 text-[#8fa5c6]">🔍<span>分析</span></router-link>
      <router-link to="/portfolio" class="flex flex-col items-center text-xs gap-0.5 text-[#8fa5c6]">💼<span>持仓</span></router-link>
      <router-link to="/ai" class="flex flex-col items-center text-xs gap-0.5 text-[#8fa5c6]">🤖<span>AI</span></router-link>
      <router-link to="/alerts" class="flex flex-col items-center text-xs gap-0.5 text-[#8fa5c6]">🔔<span>预警</span></router-link>
    </nav>

    <!-- 移动端底部留白 -->
    <div class="md:hidden h-14"></div>

    <main class="flex-1 overflow-auto"><router-view /></main>
  </div>
</template>

