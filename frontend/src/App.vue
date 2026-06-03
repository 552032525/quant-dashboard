<template>
  <div class="flex h-screen">
    <nav class="w-14 bg-[#132438] flex flex-col items-center py-4 gap-5 border-r border-[#1a314a]">
      <router-link to="/" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="行情">📈</router-link>
      <router-link to="/portfolio" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="持仓">💼</router-link>
      <router-link to="/ai" class="w-9 h-9 flex items-center justify-center rounded-lg text-base hover:bg-[#1a314a] transition-colors" title="AI">🤖</router-link>
    </nav>
    <main class="flex-1 overflow-auto"><router-view /></main>
  </div>
</template>
