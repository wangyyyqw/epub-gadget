<script setup>
import { ref, onMounted } from 'vue'

const recentFiles = ref([])
const visibleFeatures = ref([])
const visibleCards = ref([])

const openURL = async (url) => {
  try {
    await window.go.main.App.OpenURL(url)
  } catch (err) {
    console.error('Failed to open URL:', err)
  }
}

const features = [
  { icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', label: 'TXT → EPUB', desc: '将纯文本文件转换为标准 EPUB 电子书，支持自动章节识别和分层目录', color: 'indigo', gradient: 'from-indigo-500/10 to-indigo-600/5' },
  { icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z', label: '加密 / 解密', desc: '对 EPUB 进行 DRM 加密或解密处理，支持字体混淆加密', color: 'amber', gradient: 'from-amber-500/10 to-amber-600/5' },
  { icon: 'M4 6h16M4 10h16M4 14h16M4 18h16', label: 'EPUB 重构', desc: '解包并重新打包 EPUB，修复结构错误，清理冗余文件', color: 'emerald', gradient: 'from-emerald-500/10 to-emerald-600/5' },
  { icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z', label: '图片处理', desc: '压缩图片体积、转换 WebP 格式、下载远程网络图片到本地', color: 'rose', gradient: 'from-rose-500/10 to-rose-600/5' },
  { icon: 'M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129', label: '简繁转换', desc: '简体繁体中文双向转换，基于词组级别精确转换', color: 'violet', gradient: 'from-violet-500/10 to-violet-600/5' },
  { icon: 'M7 20l4-16m2 16l4-16M6 9h14M4 15h14', label: '注音 / 注释', desc: '为生僻字添加拼音注音，文本正则匹配生成脚注或弹窗注释', color: 'cyan', gradient: 'from-cyan-500/10 to-cyan-600/5' },
]

const colorConfig = {
  indigo: { icon: 'text-indigo-500 dark:text-indigo-400', from: 'from-indigo-500', to: 'to-indigo-600' },
  amber: { icon: 'text-amber-500 dark:text-amber-400', from: 'from-amber-500', to: 'to-amber-600' },
  emerald: { icon: 'text-emerald-500 dark:text-emerald-400', from: 'from-emerald-500', to: 'to-emerald-600' },
  rose: { icon: 'text-rose-500 dark:text-rose-400', from: 'from-rose-500', to: 'to-rose-600' },
  violet: { icon: 'text-violet-500 dark:text-violet-400', from: 'from-violet-500', to: 'to-violet-600' },
  cyan: { icon: 'text-cyan-500 dark:text-cyan-400', from: 'from-cyan-500', to: 'to-cyan-600' },
}

// 交错动画效果
onMounted(() => {
  // 功能卡片交错动画
  features.forEach((_, index) => {
    setTimeout(() => {
      visibleFeatures.value.push(index)
    }, 150 + index * 80)
  })
  
  // 底部卡片延迟动画
  setTimeout(() => {
    visibleCards.value = [0, 1]
  }, 500)
})
</script>

<template>
  <div class="h-full flex flex-col space-y-6">
    <!-- 标题区域 - 带渐变动画 -->
    <header class="text-center py-4 animate-fade-in">
      <h1 class="text-3xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent dark:from-indigo-400 dark:via-purple-400 dark:to-indigo-400 animate-shimmer bg-[length:200%_auto]">
        EPUB 工具箱
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">一站式 EPUB 电子书处理工具，从创建到优化全覆盖</p>
    </header>

    <!-- 快速开始卡片 - 带浮动动画 -->
    <div class="relative animate-fade-in-up" style="animation-delay: 100ms">
      <div class="absolute inset-0 bg-gradient-to-r from-indigo-500/20 via-violet-500/20 to-indigo-500/20 blur-3xl -z-10"></div>
      <div class="bg-gradient-to-br from-indigo-500 to-violet-600 rounded-2xl p-6 text-white shadow-xl shadow-indigo-500/20">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <h2 class="text-xl font-bold mb-2">快速开始</h2>
            <p class="text-indigo-100 text-sm leading-relaxed">选择左侧菜单中的工具开始处理你的 EPUB 文件<br>或从 TXT 创建新的电子书</p>
            <div class="flex gap-3 mt-4">
              <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-white/20 rounded-full text-xs font-medium backdrop-blur-sm">
                <span class="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                开发中
              </span>
            </div>
          </div>
          <div class="relative">
            <div class="absolute -inset-4 bg-white/10 rounded-full blur-xl animate-pulse-slow"></div>
            <svg class="h-20 w-20 text-white/90 relative animate-float" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能概览 - 带交错动画 -->
    <div>
      <h2 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">功能概览</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(f, index) in features" :key="f.label"
          class="group relative bg-gradient-to-br p-5 rounded-2xl border border-gray-100 dark:border-gray-700/50 backdrop-blur-sm transition-all duration-300 ease-out"
          :class="[f.gradient, visibleFeatures.includes(index) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4']"
          :style="{ transitionDelay: `${index * 50}ms` }"
        >
          <div class="absolute inset-0 bg-gradient-to-br from-white/80 to-transparent dark:from-gray-800/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl pointer-events-none"></div>

          <div class="relative flex items-start gap-4">
            <div :class="['p-3 rounded-xl bg-gradient-to-br shadow-lg transition-transform duration-300 group-hover:scale-110', `bg-gradient-to-br ${colorConfig[f.color].from} ${colorConfig[f.color].to}`]">
              <svg :class="['h-6 w-6 text-white']" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" :d="f.icon" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-800 dark:text-white text-sm mb-1.5 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{{ f.label }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-2">{{ f.desc }}</p>
            </div>
          </div>

          <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
            <svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部信息卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- 使用提示卡片 -->
      <div class="bg-gradient-to-br from-gray-50 to-white dark:from-gray-800/50 dark:to-gray-800/30 border border-gray-100 dark:border-gray-700/50 rounded-2xl p-5 backdrop-blur-sm transition-all duration-300"
        :class="visibleCards.includes(0) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
      >
        <div class="flex items-center gap-2 mb-4">
          <div class="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
            <svg class="h-5 w-5 text-indigo-500 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300">使用提示</h2>
        </div>
        <ul class="space-y-3">
          <li class="flex items-start gap-2.5 text-sm text-gray-600 dark:text-gray-400">
            <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-400 flex-shrink-0"></span>
            <span>处理前建议备份原始文件，部分操作会直接修改源文件</span>
          </li>
          <li class="flex items-start gap-2.5 text-sm text-gray-600 dark:text-gray-400">
            <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>
            <span>TXT 转 EPUB 支持自动检测编码、智能章节识别和多级目录</span>
          </li>
          <li class="flex items-start gap-2.5 text-sm text-gray-600 dark:text-gray-400">
            <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0"></span>
            <span>图片处理工具可大幅缩减 EPUB 文件体积，推荐转换为 WebP 格式</span>
          </li>
        </ul>
      </div>

      <!-- 致谢卡片 -->
      <div class="bg-gradient-to-br from-gray-50 to-white dark:from-gray-800/50 dark:to-gray-800/30 border border-gray-100 dark:border-gray-700/50 rounded-2xl p-5 backdrop-blur-sm transition-all duration-300"
        :class="visibleCards.includes(1) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
      >
        <div class="flex items-center gap-2 mb-4">
          <div class="p-2 bg-rose-100 dark:bg-rose-900/30 rounded-lg">
            <svg class="h-5 w-5 text-rose-500 dark:text-rose-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </div>
          <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300">致谢</h2>
        </div>
        <div class="flex flex-wrap gap-2">
          <a v-for="(contributor, i) in [
            { name: '遥遥心航', url: 'https://tieba.baidu.com/home/main?id=tb.1.7f262ae1.5_dXQ2Jp0F0MH9YJtgM2Ew' },
            { name: 'lgernier', url: 'https://github.com/lgernier' },
            { name: 'fontObfuscator', url: 'https://github.com/solarhell/fontObfuscator' },
            { name: 'epub_tool', url: 'https://github.com/cnwxi/epub_tool' }
          ]" :key="i"
            @click="openURL(contributor.url)"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600/50 rounded-full text-xs text-gray-600 dark:text-gray-300 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all duration-200 cursor-pointer group"
          >
            <span>{{ contributor.name }}</span>
            <svg class="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    </div>

    <footer class="text-center text-xs text-gray-400 dark:text-gray-500 pt-4 border-t border-gray-100 dark:border-gray-800">
      <p>EPUB 工具箱 · 开源免费 · MIT License</p>
    </footer>
  </div>
</template>

<style scoped>
/* 卡片交错动画 */
.card-stagger {
  opacity: 0;
  transform: translateY(10px);
  animation: fadeInUp 0.5s ease-out forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 标题渐变动画 */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-shimmer {
  background-size: 200% auto;
  animation: shimmer 3s linear infinite;
}

/* 浮动动画 */
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

/* 脉冲动画 */
@keyframes pulse-slow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.animate-pulse-slow {
  animation: pulse-slow 2s ease-in-out infinite;
}
</style>