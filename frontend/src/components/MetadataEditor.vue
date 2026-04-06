<script setup>
import { ref, watch, inject } from 'vue'
import FileDropZone from './FileDropZone.vue'
import OutputLog from './shared/OutputLog.vue'
import { useEpubProcess } from '../composables/useEpubProcess'

const toast = inject('toast')

const props = defineProps({
  activeTool: String
})

const { loading, outputLog, appendLog, clearLog, runBackend } = useEpubProcess(toast)

const inputPaths = ref([])
const outputPath = ref('')

const metadata = ref({
  title: '',
  author: '',
  language: 'zh-CN',
  publisher: '',
  description: '',
  identifier: '',
  rights: '',
})

const coverImage = ref(null)
const coverPreview = ref('')
const removeCover = ref(false)

const languages = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'zh-TW', label: '繁體中文' },
  { value: 'en-US', label: 'English' },
  { value: 'ja-JP', label: '日本語' },
  { value: 'ko-KR', label: '한국어' },
]

const resetState = () => {
  inputPaths.value = []
  outputPath.value = ''
  metadata.value = { title: '', author: '', language: 'zh-CN', publisher: '', description: '', identifier: '', rights: '' }
  coverImage.value = null
  coverPreview.value = ''
  removeCover.value = false
  clearLog()
}

watch(() => props.activeTool, resetState, { immediate: true })

const handleDrop = async (pathOrPaths) => {
  if (!pathOrPaths) return
  const paths = Array.isArray(pathOrPaths) ? pathOrPaths : [pathOrPaths]
  const epubPaths = paths.filter(p => typeof p === 'string' && p.toLowerCase().endsWith('.epub'))
  if (epubPaths.length === 0) { toast?.error('请选择正确的 EPUB 文件'); return }
  
  inputPaths.value = [epubPaths[0]]
  await loadMetadata(epubPaths[0])
  toast?.success('已选定文件准备编辑')
}

const handleFileSelectClick = async () => {
  try {
    const path = await window.go.main.App.SelectFile()
    if (path) {
      await handleDrop(path)
    }
  } catch (err) {
    console.error(err)
  }
}

const loadMetadata = async (epubPath) => {
  if (!epubPath) return
  try {
    const result = await window.go.main.App.RunBackend(['--plugin', 'metadata_edit', '--action', 'read', '--epub', epubPath])
    if (result && result.stdout) {
      // Find JSON string dynamically to avoid parsing errors from debug logs
      const output = result.stdout
      const jsonStart = output.indexOf('{')
      const jsonEnd = output.lastIndexOf('}')
      if (jsonStart >= 0 && jsonEnd >= jsonStart) {
        const jsonStr = output.slice(jsonStart, jsonEnd + 1)
        const data = JSON.parse(jsonStr)
        metadata.value = {
          title: data.title || '',
          author: data.author || '',
          language: data.language || 'zh-CN',
          publisher: data.publisher || '',
          description: data.description || '',
          identifier: data.identifier || '',
          rights: data.rights || '',
        }
        if (data.cover) {
          coverPreview.value = data.cover
        }
      }
    }
  } catch (e) {
    console.error('Failed to load metadata:', e)
  }
}

const handleCoverSelect = async () => {
  try {
    const path = await window.go.main.App.SelectFile()
    if (path) {
      coverImage.value = path
      coverPreview.value = `file://${path}`
      removeCover.value = false
    }
  } catch (e) {
    console.error('Failed to select cover:', e)
  }
}

const handleOutputSelect = async () => {
  try {
    const defaultFilename = inputPaths.value[0]?.split(/[\\/]/).pop()?.replace('.epub', '_metadata.epub') || 'output.epub'
    const path = await window.go.main.App.SaveFile(defaultFilename)
    if (path) {
      outputPath.value = path
    }
  } catch (e) {
    console.error('Failed to select output:', e)
  }
}

const applyMetadata = async () => {
  if (!inputPaths.value[0]) {
    toast?.error('请先选择 EPUB 文件')
    return
  }
  if (!outputPath.value) {
    toast?.error('请选择输出路径')
    return
  }

  loading.value = true
  outputLog.value = ''

  const args = [
    '--plugin', 'metadata_edit',
    '--action', 'write',
    '--epub', inputPaths.value[0],
    '--output', outputPath.value,
    '--metadata', JSON.stringify(metadata.value)
  ]

  if (coverImage.value) {
    args.push('--cover', coverImage.value)
  }
  if (removeCover.value) {
    args.push('--remove-cover')
  }

  try {
    await runBackend(args, (result) => {
      appendLog('\n✅ 元数据修改成功')
      toast?.success('元数据修改成功')
    }, () => {
      toast?.error('修改失败')
    })
  } catch (e) {
    toast?.error('处理出错')
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-1">元数据编辑</h2>
      <p class="text-sm text-gray-500 dark:text-gray-400">编辑 EPUB 书籍的标题、作者、出版社等信息</p>
    </div>

    <!-- File Selection -->
    <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
      <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">文件设置</h2>
      <div>
        <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
          输入文件 <span class="text-red-400">*</span>
        </label>
        <div class="space-y-2">
          <FileDropZone accept=".epub" :multiple="false" @drop="handleDrop" @click="handleFileSelectClick">
            <div class="flex flex-col items-center justify-center py-6 px-4 text-center">
              <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-2">
                <svg class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300">拖拽 EPUB 文件到此处</p>
              <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">或点击选择文件</p>
            </div>
          </FileDropZone>
          <div v-if="inputPaths.length > 0" class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg group">
            <span class="text-xs text-gray-600 dark:text-gray-400 truncate flex-1 mr-2" :title="inputPaths[0]">{{ inputPaths[0].split(/[\\/]/).pop() }}</span>
            <button @click="resetState" class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <template v-if="inputPaths.length > 0">
      <!-- Output Path -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <label class="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider">输出路径</label>
        <div class="flex gap-2">
          <input :value="outputPath" readonly @click="handleOutputSelect"
            placeholder="点击选择输出文件夹及名称"
            class="flex-1 rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 cursor-pointer focus:bg-white dark:focus:bg-gray-800 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 outline-none transition-all" />
          <button @click="handleOutputSelect"
            class="px-4 py-2.5 text-sm font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            选择保存位置
          </button>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <svg class="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          基本信息
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">书名</label>
            <input v-model="metadata.title" type="text" placeholder="请输入书名"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">作者</label>
            <input v-model="metadata.author" type="text" placeholder="请输入作者"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">语言</label>
            <select v-model="metadata.language"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all">
              <option v-for="lang in languages" :key="lang.value" :value="lang.value">{{ lang.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">出版社</label>
            <input v-model="metadata.publisher" type="text" placeholder="请输入出版社"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all" />
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">简介</label>
          <textarea v-model="metadata.description" rows="3" placeholder="请输入书籍简介"
            class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all resize-none"></textarea>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">ISBN / 标识符</label>
            <input v-model="metadata.identifier" type="text" placeholder="请输入标识符（可选）"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">版权信息</label>
            <input v-model="metadata.rights" type="text" placeholder="请输入版权信息（可选）"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:border-indigo-400 outline-none transition-all" />
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2 mb-4">
          <svg class="w-4 h-4 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          封面图片
        </h3>

        <div class="flex items-start gap-4">
          <div class="flex-shrink-0">
            <div v-if="coverPreview" class="w-24 h-32 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 shadow-md">
              <img :src="coverPreview" alt="封面预览" class="w-full h-full object-cover" />
            </div>
            <div v-else class="w-24 h-32 rounded-lg bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 flex items-center justify-center">
              <svg class="w-8 h-8 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>

          <div class="flex-1 space-y-3">
            <div class="flex gap-2">
              <button @click="handleCoverSelect"
                class="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 transition-colors">
                {{ coverPreview ? '更换封面' : '添加封面' }}
              </button>
              <button v-if="coverPreview" @click="removeCover = true; coverPreview = ''; coverImage = null"
                class="px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                移除封面
              </button>
            </div>
            <p class="text-xs text-gray-400 dark:text-gray-500">支持 JPG、PNG、WebP 等格式，建议尺寸 600×800 像素</p>
          </div>
        </div>
      </div>

      <!-- Action Button -->
      <div class="flex items-center justify-between pt-2">
        <button v-if="outputLog" @click="clearLog" class="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">清除日志</button>
        <div v-else></div>
        <button @click="applyMetadata" :disabled="loading || !outputPath"
          :class="['inline-flex items-center px-6 py-2.5 text-sm font-medium rounded-lg shadow-sm text-white transition-all duration-200',
            loading || !outputPath ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 hover:shadow-md active:scale-[0.98]']">
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ loading ? '处理中...' : '应用修改' }}
        </button>
      </div>

      <OutputLog v-if="outputLog" :log="outputLog" />
    </template>
  </div>
</template>