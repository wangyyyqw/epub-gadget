<script setup>
import { ref } from 'vue'

const props = defineProps({
  currentView: String,
  currentTheme: String
})

const emit = defineEmits(['change-view', 'toggle-theme'])

const expandedGroups = ref({ encrypt: true, format: true, image: true, annotate: true, other: true })
const toggleGroup = (key) => { expandedGroups.value[key] = !expandedGroups.value[key] }

const mainItems = [
  { id: 'dashboard', label: '仪表盘', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
]

const toolGroups = [
  {
    key: 'encrypt', label: '加密 / 解密', color: 'amber',
    items: [
      { id: 'tool:encrypt', label: '加密 EPUB', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
      { id: 'tool:decrypt', label: '解密 EPUB', icon: 'M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z' },
      { id: 'tool:encrypt_font', label: '字体加密', icon: 'M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' },
    ]
  },
  {
    key: 'format', label: '格式 / 转换', color: 'indigo',
    items: [
      { id: 'tool:metadata_edit', label: '元数据编辑', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
      { id: 'txt2epub', label: 'TXT → EPUB', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
      { id: 'tool:reformat_convert', label: '重构 / 转换', icon: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
      { id: 'tool:convert_chinese', label: '简繁转换', icon: 'M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129' },
      { id: 'tool:font_subset', label: '字体子集化', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
      { id: 'tool:view_opf', label: 'OPF 查看', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
      { id: 'tool:split_merge_epub', label: '拆分 / 合并', icon: 'M17 14v6m-3-3h6M6 10h2a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v2a2 2 0 002 2zm10 0h2a2 2 0 002-2V6a2 2 0 00-2-2h-2a2 2 0 00-2 2v2a2 2 0 002 2zM6 20h2a2 2 0 002-2v-2a2 2 0 00-2-2H6a2 2 0 00-2 2v2a2 2 0 002 2z' },
    ]
  },
  {
    key: 'image', label: '图片处理', color: 'rose',
    items: [
      { id: 'tool:img_compress', label: '图片压缩', icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
      { id: 'tool:convert_image_format', label: '图片格式转换', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
      { id: 'tool:download_images', label: '下载网络图', icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4' },
    ]
  },
  {
    key: 'annotate', label: '注释 / 注音', color: 'cyan',
    items: [
      { id: 'tool:phonetic', label: '生僻字注音', icon: 'M7 20l4-16m2 16l4-16M6 9h14M4 15h14' },
      { id: 'tool:comment', label: '正则匹配→弹窗', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z' },
      { id: 'tool:footnote_conv', label: '脚注→弹窗', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
    ]
  },
  {
    key: 'other', label: '其它', color: 'violet',
    items: [
      { id: 'tool:yuewei', label: '阅微→多看', icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4' },
      { id: 'tool:zhangyue', label: '掌阅→多看', icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4' },
    ]
  },
]

const colorMap = {
  amber: { bg: 'bg-amber-500', light: 'text-amber-500 dark:text-amber-400', hover: 'hover:bg-amber-50 dark:hover:bg-amber-900/20 dark:hover:text-amber-300' },
  indigo: { bg: 'bg-indigo-500', light: 'text-indigo-500 dark:text-indigo-400', hover: 'hover:bg-indigo-50 dark:hover:bg-indigo-900/20 dark:hover:text-indigo-300' },
  rose: { bg: 'bg-rose-500', light: 'text-rose-500 dark:text-rose-400', hover: 'hover:bg-rose-50 dark:hover:bg-rose-900/20 dark:hover:text-rose-300' },
  cyan: { bg: 'bg-cyan-500', light: 'text-cyan-500 dark:text-cyan-400', hover: 'hover:bg-cyan-50 dark:hover:bg-cyan-900/20 dark:hover:text-cyan-300' },
  violet: { bg: 'bg-violet-500', light: 'text-violet-500 dark:text-violet-400', hover: 'hover:bg-violet-50 dark:hover:bg-violet-900/20 dark:hover:text-violet-300' },
  emerald: { bg: 'bg-emerald-500', light: 'text-emerald-500 dark:text-emerald-400', hover: 'hover:bg-emerald-50 dark:hover:bg-emerald-900/20 dark:hover:text-emerald-300' },
}

const isActive = (id) => props.currentView === id
</script>

<template>
  <aside class="w-56 bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl flex flex-col h-full border-r border-gray-200/50 dark:border-gray-700/50 select-none transition-all duration-300">
    <div class="h-10 drag-region flex-shrink-0"></div>

    <div class="px-4 pb-4 flex-shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <div>
          <h1 class="text-sm font-bold text-gray-800 dark:text-white tracking-tight">EPUB 工具箱</h1>
          <p class="text-[9px] text-gray-400 dark:text-gray-500 font-medium">v1.0.3</p>
        </div>
      </div>
    </div>

    <nav class="flex-1 overflow-y-auto px-2 pb-4 space-y-1 no-scrollbar">
      <button
        v-for="item in mainItems" :key="item.id"
        @click="$emit('change-view', item.id)"
        :class="[
          'w-full flex items-center gap-2.5 px-3 py-2 text-[12px] font-medium rounded-xl transition-all duration-200',
          isActive(item.id)
            ? 'bg-gradient-to-r from-indigo-500/10 to-violet-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-200/50 dark:border-indigo-800/50'
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-white'
        ]"
      >
        <svg class="h-4 w-4" :class="isActive(item.id) ? 'text-indigo-500 dark:text-indigo-400' : 'text-gray-400 dark:text-gray-500'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
        </svg>
        {{ item.label }}
      </button>

      <div v-for="group in toolGroups" :key="group.key" class="pt-3">
        <button
          @click="toggleGroup(group.key)"
          class="w-full flex items-center justify-between px-2 py-1.5 group"
        >
          <div class="flex items-center gap-1.5">
            <span :class="['w-1.5 h-1.5 rounded-full bg-gradient-to-r', colorMap[group.color].bg, 'to-transparent opacity-60 group-hover:opacity-100 transition-opacity']"></span>
            <span class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider group-hover:text-gray-600 dark:group-hover:text-gray-400 transition-colors">{{ group.label }}</span>
          </div>
          <svg
            class="h-3.5 w-3.5 text-gray-400 dark:text-gray-500 transition-all duration-300"
            :class="{ 'rotate-90': expandedGroups[group.key] }"
            fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <transition name="slide">
          <ul v-show="expandedGroups[group.key]" class="mt-1 ml-1 space-y-0.5">
            <li v-for="item in group.items" :key="item.id">
              <button
                @click="$emit('change-view', item.id)"
                :class="[
                  'w-full flex items-center gap-2.5 px-3 py-1.5 text-[12px] font-medium rounded-lg transition-all duration-200',
                  isActive(item.id)
                    ? 'bg-gradient-to-r from-indigo-500/10 to-violet-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-200/50 dark:border-indigo-800/50'
                    : `text-gray-500 dark:text-gray-400 ${colorMap[group.color].hover} hover:border-gray-200 dark:hover:border-gray-700/50 border border-transparent`
                ]"
              >
                <svg class="h-4 w-4 flex-shrink-0" :class="isActive(item.id) ? 'text-indigo-500 dark:text-indigo-400' : colorMap[group.color].light" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
                </svg>
                {{ item.label }}
              </button>
            </li>
          </ul>
        </transition>
      </div>
    </nav>

    <div class="p-3 border-t border-gray-200/50 dark:border-gray-700/50">
      <button
        @click="$emit('toggle-theme')"
        class="w-full flex items-center justify-center gap-2 px-3 py-2 text-[11px] font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50 rounded-xl transition-all duration-200 group"
      >
        <div class="relative">
          <svg v-if="currentTheme === 'light'" class="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else-if="currentTheme === 'dark'" class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
          <svg v-else class="w-4 h-4 text-gray-400 group-hover:text-indigo-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <span>{{ currentTheme === 'auto' ? '跟随系统' : (currentTheme === 'light' ? '亮色模式' : '深色模式') }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.drag-region {
  --wails-draggable: drag;
}
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>