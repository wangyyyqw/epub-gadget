<script setup>
import { ref, nextTick, inject, computed } from 'vue'
import FileDropZone from './FileDropZone.vue'
import PatternSelector from './shared/PatternSelector.vue'
import ChapterPreview from './shared/ChapterPreview.vue'
import OutputLog from './shared/OutputLog.vue'
import { useUI } from '../composables/useUI'

const { inputBaseClass, inputReadonlyClass, buttonBaseClass, buttonPrimaryClass, buttonSecondaryClass, cardClass, sectionHeaderClass } = useUI()

const toast = inject('toast')

let previewDebounceTimer = null
const debounceGeneratePreview = (delay = 150) => {
  if (previewDebounceTimer) clearTimeout(previewDebounceTimer)
  previewDebounceTimer = setTimeout(generatePreview, delay)
}

// --- State ---
const txtPath = ref('')
const epubPath = ref('')
const title = ref('')
const author = ref('Unknown')
const coverPath = ref('')
const customRegex = ref('')
const removeEmptyLine = ref(false)
const fixIndent = ref(false)
const splitChapterTitle = ref(false)
const headerImagePath = ref('')

const loading = ref(false)
const scanning = ref(false)
const outputLog = ref('')
const scanResults = ref(null)
const activeTab = ref('basic')

const selectedPatterns = ref([])
const chapterPreview = ref([])
const previewLoading = ref(false)

const wordCountThreshold = ref(5000)
const enableWordCountCheck = ref(true)
const enableSequenceCheck = ref(true)

// Batch mode
const batchMode = ref(false)
const txtFiles = ref([])
const batchOutputDir = ref('')

// --- Computed ---
const hasSelectedPatterns = computed(() => selectedPatterns.value.length > 0)

const patternsString = computed(() => {
  return selectedPatterns.value
    .filter(p => p.enabled)
    .sort((a, b) => a.order - b.order)
    .map(p => `${p.pattern}:${p.level}:${p.split}`)
    .join(' ||| ')
})

const totalChapters = computed(() => {
  let count = 0
  const countNodes = (nodes) => {
    for (const node of nodes) {
      count++
      if (node.children && node.children.length > 0) countNodes(node.children)
    }
  }
  countNodes(chapterPreview.value)
  return count
})

const warningCount = computed(() => chapterPreview.value.filter(c => c.hasWarning).length)
const wordWarningCount = computed(() => chapterPreview.value.filter(c => c.hasWordWarning).length)
const sequenceWarningCount = computed(() => chapterPreview.value.filter(c => c.sequenceWarning).length)

// --- Helper Functions ---
const extractNumber = (title) => {
  const chineseNums = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '百': 100, '千': 1000, '万': 10000,
    '〇': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10, '佰': 100, '仟': 1000
  }
  const arabicMatch = title.match(/\d+/)
  if (arabicMatch) return parseInt(arabicMatch[0])
  const chineseMatch = title.match(/[零一二两三四五六七八九十百千万〇壹贰叁肆伍陆柒捌玖拾佰仟]+/)
  if (chineseMatch) {
    const str = chineseMatch[0]
    let result = 0, section = 0, temp = 0
    for (let i = 0; i < str.length; i++) {
      const val = chineseNums[str[i]]
      if (val === 10000) {
        if (temp === 0 && section === 0) section = 1
        section += temp; result += section * val; section = 0; temp = 0
      } else if (val >= 10) {
        if (temp === 0) temp = 1
        section += temp * val; temp = 0
      } else { temp = val }
    }
    result += section + temp
    return result || null
  }
  return null
}

const checkSequence = (chapters) => {
  let prevNum = null
  for (const chapter of chapters) {
    const num = extractNumber(chapter.title)
    if (num !== null) {
      if (prevNum !== null && num <= prevNum) {
        chapter.sequenceWarning = true
        chapter.sequenceDetail = `序号 ${num} <= 前一章 ${prevNum}`
      }
      prevNum = num
    }
  }
}

// --- Methods ---
const handleTxtDrop = async (fileOrPath) => {
  if (!fileOrPath) return
  const resolvedPath = typeof fileOrPath === 'string' ? fileOrPath : (fileOrPath.path || await window.go.main.App.SelectFile())
  if (resolvedPath) {
    if (!resolvedPath.toLowerCase().endsWith('.txt') && !resolvedPath.toLowerCase().includes('.txt')) {
      toast?.error?.('请选择 TXT 文本文件'); return
    }
    txtPath.value = resolvedPath
    const filename = resolvedPath.split(/[\\/]/).pop()
    const name = filename.replace(/\.[^/.]+$/, '')
    if (!title.value) title.value = name
    if (!epubPath.value) epubPath.value = resolvedPath.replace(/\.[^/.]+$/, '.epub')
    toast?.success?.(`已选择文件: ${filename}`)
  }
}

const selectTxtFile = async () => {
  try {
    const path = await window.go.main.App.SelectTxtFile()
    if (path) {
      txtPath.value = path
      const filename = path.split(/[\\/]/).pop()
      const name = filename.replace(/\.[^/.]+$/, '')
      if (!title.value) title.value = name
      if (!epubPath.value) epubPath.value = path.replace(/\.[^/.]+$/, '.epub')
      toast?.success?.(`已选择文件: ${filename}`)
    }
  } catch (err) { console.error(err); toast?.error?.('选择文件失败') }
}

const selectEpubSavePath = async () => {
  try {
    const defaultName = title.value ? title.value + '.epub' : 'output.epub'
    const path = await window.go.main.App.SaveFile(defaultName)
    if (path) { epubPath.value = path; toast?.success?.('已设置输出路径') }
  } catch (err) { console.error(err); toast?.error?.('设置输出路径失败') }
}

const selectCoverFile = async () => {
  try {
    const path = await window.go.main.App.SelectFile()
    if (path) { coverPath.value = path; toast?.success?.('已选择封面图片') }
  } catch (err) { console.error(err); toast?.error?.('选择封面图片失败') }
}

const selectHeaderImage = async () => {
  try {
    const path = await window.go.main.App.SelectFile()
    if (path) { headerImagePath.value = path; toast?.success?.('已选择章节头图') }
  } catch (err) { console.error(err); toast?.error?.('选择章节头图失败') }
}

const scanChapters = async () => {
  if (!txtPath.value) { toast?.warning?.('请先选择 TXT 文件'); return }
  scanning.value = true
  outputLog.value = '▶ 正在扫描章节结构...\n'
  scanResults.value = null; selectedPatterns.value = []; chapterPreview.value = []
  const nullPath = "/dev/null" // scan mode doesn't write output, use /dev/null
  const args = ['--plugin', 'txt2epub', '--txt-path', txtPath.value, '--epub-path', nullPath, '--title', 'scan', '--scan']
  try {
    const result = await window.go.main.App.RunBackend(args)
    if (result.stderr) outputLog.value += result.stderr + '\n'
    const data = JSON.parse(result.stdout)
    scanResults.value = data
    if (data.suggested_hierarchy && data.suggested_hierarchy.length > 0) {
      selectedPatterns.value = data.suggested_hierarchy.map((h, index) => ({
        ...h, enabled: true, order: index, split: h.split !== false
      }))
    }
    const patternCount = data.suggested_hierarchy?.length || 0
    outputLog.value += `✅ 扫描完成，找到 ${patternCount} 种章节模式\n`
    toast?.success?.(`扫描完成，找到 ${patternCount} 种章节模式`)
    await generatePreview()
  } catch (err) {
    outputLog.value += '❌ 扫描失败: ' + err + '\n'
    toast?.error?.('扫描失败: ' + err)
  } finally { scanning.value = false }
}

const generatePreview = async () => {
  if (!txtPath.value) { chapterPreview.value = []; return }
  if (!patternsString.value && selectedPatterns.value.filter(p => p.enabled).length === 0) {
    chapterPreview.value = []; return
  }
  previewLoading.value = true
  try {
    const chapters = []
    if (scanResults.value && scanResults.value.patterns) {
      const enabledPatterns = selectedPatterns.value.filter(p => p.enabled).sort((a, b) => a.order - b.order)
      for (const pattern of enabledPatterns) {
        const matched = scanResults.value.patterns.find(p => p.pattern === pattern.pattern)
        if (matched && matched.chapter_details) {
          const level = pattern.level
          const levelLabels = ['h1', 'h2', 'h3', 'h4']
          for (const detail of matched.chapter_details) {
            const wordCount = detail.word_count || 0
            const hasWordWarning = enableWordCountCheck.value && wordCount > wordCountThreshold.value
            chapters.push({
              title: detail.title, level, levelLabel: levelLabels[level] || 'h2',
              wordCount, hasWordWarning, sequenceWarning: false, sequenceDetail: '',
              hasWarning: hasWordWarning, children: []
            })
          }
        }
      }
      if (enableSequenceCheck.value) {
        checkSequence(chapters)
        chapters.forEach(c => { if (c.sequenceWarning) c.hasWarning = true })
      }
    }
    chapterPreview.value = chapters
  } catch (err) { console.error('Preview error:', err); chapterPreview.value = [] }
  finally { previewLoading.value = false }
}

const togglePattern = (pattern) => { pattern.enabled = !pattern.enabled; debounceGeneratePreview() }
const movePatternUp = (index) => {
  if (index <= 0) return
  const temp = selectedPatterns.value[index].order
  selectedPatterns.value[index].order = selectedPatterns.value[index - 1].order
  selectedPatterns.value[index - 1].order = temp
  selectedPatterns.value.sort((a, b) => a.order - b.order); debounceGeneratePreview()
}
const movePatternDown = (index) => {
  if (index >= selectedPatterns.value.length - 1) return
  const temp = selectedPatterns.value[index].order
  selectedPatterns.value[index].order = selectedPatterns.value[index + 1].order
  selectedPatterns.value[index + 1].order = temp
  selectedPatterns.value.sort((a, b) => a.order - b.order); debounceGeneratePreview()
}
const selectAllPatterns = () => { selectedPatterns.value.forEach(p => p.enabled = true); debounceGeneratePreview() }
const deselectAllPatterns = () => { selectedPatterns.value.forEach(p => p.enabled = false); debounceGeneratePreview() }

// Batch mode helpers
const fileName = (p) => p.split(/[\\/]/).pop()

const handleBatchFileDrop = (pathsOrPath) => {
  if (!pathsOrPath) return
  const paths = Array.isArray(pathsOrPath) ? pathsOrPath : [pathsOrPath]
  const validPaths = paths.map(p => typeof p === 'string' ? p : p.path).filter(p => p.toLowerCase().endsWith('.txt'))
  if (validPaths.length === 0) { toast?.error?.('请选择 TXT 文件'); return }
  const existing = new Set(txtFiles.value)
  const newPaths = validPaths.filter(p => !existing.has(p))
  if (newPaths.length > 0) { txtFiles.value = [...txtFiles.value, ...newPaths]; toast?.success?.(`已添加 ${newPaths.length} 个文件`) }
}

const selectBatchFiles = async () => {
  try {
    const paths = await window.go.main.App.SelectFiles({ filters: [{ name: 'TXT 文件', extensions: ['txt'] }] })
    if (paths && paths.length > 0) handleBatchFileDrop(paths)
  } catch (err) { console.error(err) }
}

const removeBatchFile = (index) => { txtFiles.value.splice(index, 1) }
const clearBatchFiles = () => { txtFiles.value = [] }

const selectBatchOutputDir = async () => {
  try {
    const path = await window.go.main.App.SelectDirectory()
    if (path) { batchOutputDir.value = path; toast?.success?.('已设置输出目录') }
  } catch (err) { console.error(err) }
}

const _inferTitleFromTxt = (txtPath) => {
  return fileName(txtPath).replace(/\.txt$/i, '').trim()
}

const _inferAuthorFromTxt = (txtPath) => {
  return 'Unknown'
}

const runBatchConversion = async () => {
  if (txtFiles.value.length === 0) { toast?.warning?.('请先添加 TXT 文件'); return }
  loading.value = true
  const total = txtFiles.value.length
  let successCount = 0, failCount = 0
  outputLog.value = `▶ 批量转换: 共 ${total} 个 TXT 文件\n${'─'.repeat(40)}\n`
  toast?.info?.(`开始批量转换 ${total} 个文件...`, 2000)
  for (let i = 0; i < total; i++) {
    const txtPath = txtFiles.value[i]
    const name = fileName(txtPath)
    outputLog.value += `\n[${i + 1}/${total}] ${name}\n`
    const inferredTitle = _inferTitleFromTxt(txtPath)
    const inferredAuthor = _inferAuthorFromTxt(txtPath)
    const baseName = inferredTitle.replace(/[\\/:*?"<>|]/g, '_')
    const epubPath = batchOutputDir.value
      ? `${batchOutputDir.value}/${baseName}.epub`
      : txtPath.replace(/\.txt$/i, '.epub')
    const args = ['--plugin', 'txt2epub', '--txt-path', txtPath, '--epub-path', epubPath, '--title', inferredTitle, '--author', inferredAuthor]
    if (customRegex.value) args.push('--custom-regex', customRegex.value)
    if (patternsString.value) args.push('--patterns', patternsString.value)
    if (removeEmptyLine.value) args.push('--remove-empty-line')
    if (fixIndent.value) args.push('--fix-indent')
    if (splitChapterTitle.value) args.push('--split-title')
    if (headerImagePath.value) args.push('--header-image', headerImagePath.value)
    try {
      await window.go.main.App.RunBackend(args)
      outputLog.value += '  ✅ 完成\n'
      successCount++
    } catch (err) {
      outputLog.value += `  ❌ 失败: ${String(err)}\n`
      failCount++
    }
  }
  outputLog.value += `\n${'─'.repeat(40)}\n📊 结果: 成功 ${successCount}，失败 ${failCount}\n`
  operationCompleted.value = true
  if (failCount === 0) toast?.success?.(`批量转换完成（${successCount} 个文件）`)
  else toast?.warning?.(`完成: ${successCount} 成功, ${failCount} 失败`)
  loading.value = false
}

const operationCompleted = ref(false)

const runConversion = async () => {
  if (!txtPath.value || !epubPath.value || !title.value) {
    const missing = []
    if (!txtPath.value) missing.push('TXT 文件')
    if (!epubPath.value) missing.push('EPUB 路径')
    if (!title.value) missing.push('书名')
    toast?.warning?.(`请填写: ${missing.join('、')}`); return
  }
  loading.value = true
  outputLog.value = '▶ 开始转换...\n'
  toast?.info?.('开始转换...', 2000)
  const args = ['--plugin', 'txt2epub', '--txt-path', txtPath.value, '--epub-path', epubPath.value, '--title', title.value, '--author', author.value]
  if (coverPath.value) args.push('--cover-path', coverPath.value)
  if (customRegex.value) args.push('--custom-regex', customRegex.value)
  if (patternsString.value) args.push('--patterns', patternsString.value)
  if (removeEmptyLine.value) args.push('--remove-empty-line')
  if (fixIndent.value) args.push('--fix-indent')
  if (splitChapterTitle.value) args.push('--split-title')
  if (headerImagePath.value) args.push('--header-image', headerImagePath.value)
  try {
    const result = await window.go.main.App.RunBackend(args)
    if (result.stderr) outputLog.value += result.stderr + '\n'
    if (result.stdout) outputLog.value += result.stdout + '\n'
    outputLog.value += '✅ 转换完成！'
    toast?.success?.('转换完成！')
  } catch (err) {
    const errStr = String(err)
    outputLog.value += '❌ 错误: ' + errStr + '\n'
    if (errStr.includes('PermissionError') || errStr.includes('Operation not permitted')) {
      outputLog.value += '提示: 没有写入权限，请尝试:\n  1. 选择其他输出目录（如 Documents 文件夹）\n  2. 在 macOS 系统设置中授予应用访问 Desktop 的权限\n  3. 将输出路径改为 TXT 文件所在目录\n'
      toast?.error?.('没有写入权限，请选择其他输出目录')
    } else if (errStr.includes('exit status 2')) {
      outputLog.value += '提示: 后端程序执行失败，请检查:\n  1. TXT 文件是否存在且可读\n  2. 输出目录是否有写入权限\n  3. Python 环境是否正确配置\n'
      toast?.error?.('转换失败，请查看日志详情')
    } else {
      toast?.error?.('转换失败，请查看日志详情')
    }
  } finally { loading.value = false }
}

const copyLog = async () => {
  try { await navigator.clipboard.writeText(outputLog.value); toast?.success?.('已复制日志到剪贴板') }
  catch { toast?.error?.('复制失败') }
}
const clearLog = () => { outputLog.value = ''; scanResults.value = null; selectedPatterns.value = []; chapterPreview.value = [] }

const tabs = [
  { key: 'basic', label: '基本设置' },
  { key: 'preview', label: '目录预览' },
  { key: 'advanced', label: '高级选项' },
]
</script>

<template>
  <div class="h-full flex flex-col space-y-6">
    <header class="pb-2">
      <div class="flex items-center gap-3">
        <div class="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h1 class="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
            TXT → EPUB
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">将纯文本文件转换为标准 EPUB 电子书</p>
        </div>
      </div>
    </header>

    <!-- Batch Mode Toggle -->
    <div class="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
      <div>
        <p class="text-sm font-medium text-gray-700 dark:text-gray-300">批量模式</p>
        <p class="text-xs text-gray-400 mt-0.5">一次转换多个 TXT 文件，书名自动从文件名推断</p>
      </div>
      <button @click="batchMode = !batchMode"
        :class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200', batchMode ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600']">
        <span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 shadow-sm', batchMode ? 'translate-x-6' : 'translate-x-1']" />
      </button>
    </div>

    <div class="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
        :class="['px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-150',
          activeTab === tab.key
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
            : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200']"
      >{{ tab.label }}</button>
    </div>

    <div class="flex-1 overflow-y-auto space-y-5">

      <!-- Basic Tab -->
      <template v-if="activeTab === 'basic'">
        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
          <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">文件路径</h2>
          <!-- Batch Mode File List -->
          <div v-if="batchMode">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              TXT 文件 <span class="text-red-400">*</span>
              <span v-if="txtFiles.length > 0" class="ml-2 text-xs text-indigo-500 font-normal">已选 {{ txtFiles.length }} 个文件</span>
            </label>
            <div class="space-y-2">
              <FileDropZone accept=".txt,text/plain" :multiple="true" @drop="handleBatchFileDrop" @error="(msg) => toast?.error?.(msg)" @click="selectBatchFiles" :disabled="false">
                <div class="flex flex-col items-center justify-center py-6 px-4 text-center">
                  <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-2">
                    <svg class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p class="text-sm font-medium text-gray-700 dark:text-gray-300">拖拽多个 TXT 文件到此处</p>
                  <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">书名将从文件名自动推断</p>
                </div>
              </FileDropZone>
              <div v-if="txtFiles.length > 0" class="space-y-1">
                <div v-for="(p, idx) in txtFiles" :key="p" class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg group">
                  <div class="flex items-center min-w-0 flex-1 mr-2">
                    <span class="text-xs text-gray-400 mr-2 flex-shrink-0">{{ idx + 1 }}.</span>
                    <span class="text-xs text-gray-600 dark:text-gray-400 truncate" :title="p">{{ fileName(p) }}</span>
                  </div>
                  <button @click="removeBatchFile(idx)" class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <button @click="clearBatchFiles" class="text-xs text-gray-400 hover:text-red-500 transition-colors mt-1">清空全部</button>
              </div>
            </div>
            <div class="mt-4">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">输出目录 <span class="text-gray-400 font-normal">（可选）</span></label>
              <div class="flex space-x-2">
                <input v-model="batchOutputDir" type="text" :class="inputReadonlyClass" placeholder="默认为源文件同目录" readonly @click="selectBatchOutputDir">
                <button @click="selectBatchOutputDir" :class="buttonSecondaryClass">浏览</button>
              </div>
            </div>
          </div>
          <!-- Single File Mode -->
          <div v-else>
            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                TXT 文件 <span class="text-red-400">*</span>
              </label>
              <div class="space-y-2">
                <FileDropZone accept=".txt,text/plain" @drop="handleTxtDrop" @error="(msg) => toast?.error?.(msg)" @click="selectTxtFile" :disabled="false">
                  <div class="flex flex-col items-center justify-center py-6 px-4 text-center">
                    <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-2">
                      <svg class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <p class="text-sm font-medium text-gray-700 dark:text-gray-300">拖拽 TXT 文件到此处</p>
                    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">或点击选择文件</p>
                  </div>
                </FileDropZone>
                <div v-if="txtPath" class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg group">
                  <span class="text-xs text-gray-600 dark:text-gray-400 truncate flex-1 mr-2" :title="txtPath">{{ txtPath.split(/[\\/]/).pop() }}</span>
                  <button @click="txtPath = ''" class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <div class="mt-4">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">EPUB 输出路径</label>
              <div class="flex space-x-2">
                <input v-model="epubPath" type="text" :class="inputReadonlyClass" placeholder="输出路径（自动生成）" readonly @click="selectEpubSavePath">
                <button @click="selectEpubSavePath" :class="buttonSecondaryClass">浏览</button>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
          <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">元数据</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">书名 <span class="text-red-400">*</span></label>
              <input v-model="title" type="text" :class="inputBaseClass" placeholder="输入书名">
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">作者</label>
              <input v-model="author" type="text" :class="inputBaseClass" placeholder="Unknown">
            </div>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">封面图片 <span class="text-gray-400 font-normal">（可选）</span></label>
            <div class="flex space-x-2">
              <input v-model="coverPath" type="text" :class="inputReadonlyClass" placeholder="选择封面图片" readonly @click="selectCoverFile">
              <button @click="selectCoverFile" :class="buttonSecondaryClass">浏览</button>
            </div>
          </div>
        </div>

        <!-- Chapter Scan Section -->
        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">章节识别</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">自动扫描并选择章节模式</p>
            </div>
            <button @click="scanChapters" :disabled="scanning || !txtPath"
              :class="['inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                scanning || !txtPath
                  ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-400 cursor-not-allowed'
                  : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-800/30']"
            >
              <svg v-if="scanning" class="animate-spin -ml-0.5 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {{ scanning ? '扫描中...' : '扫描章节' }}
            </button>
          </div>
          <div v-if="!txtPath" class="text-sm text-amber-600 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-300 rounded-lg p-3">
            请先选择 TXT 文件
          </div>
          <PatternSelector
            :patterns="selectedPatterns"
            @toggle="togglePattern"
            @moveUp="movePatternUp"
            @moveDown="movePatternDown"
            @selectAll="selectAllPatterns"
            @deselectAll="deselectAllPatterns"
            @updateLevel="generatePreview"
            @updateSplit="generatePreview"
          />
        </div>
      </template>

      <!-- Preview Tab -->
      <template v-if="activeTab === 'preview' && !batchMode">
        <ChapterPreview
          :chapters="chapterPreview"
          :totalChapters="totalChapters"
          :warningCount="warningCount"
          :wordWarningCount="wordWarningCount"
          :sequenceWarningCount="sequenceWarningCount"
          :previewLoading="previewLoading"
          :hasPatterns="!!patternsString"
          v-model:enableWordCountCheck="enableWordCountCheck"
          v-model:enableSequenceCheck="enableSequenceCheck"
          v-model:wordCountThreshold="wordCountThreshold"
          @refresh="generatePreview"
        />
      </template>

      <!-- Advanced Tab -->
      <template v-if="activeTab === 'advanced'">
        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-5">
          <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">文本清理</h2>
          <div class="flex flex-wrap gap-6">
            <label class="flex items-center space-x-2.5 cursor-pointer group">
              <input v-model="removeEmptyLine" type="checkbox" class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 dark:text-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 cursor-pointer">
              <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">移除多余空行</span>
            </label>
            <label class="flex items-center space-x-2.5 cursor-pointer group">
              <input v-model="fixIndent" type="checkbox" class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 dark:text-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 cursor-pointer">
              <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">修复段落缩进</span>
            </label>
            <label class="flex items-center space-x-2.5 cursor-pointer group">
              <input v-model="splitChapterTitle" type="checkbox" class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 dark:text-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 bg-white dark:bg-gray-700 cursor-pointer">
              <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">拆分章节标题 (序号/标题换行)</span>
            </label>
          </div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
          <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">样式增强</h2>
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">章节头图 <span class="text-gray-400 font-normal">（可选）</span></label>
            <div class="flex space-x-2">
              <input v-model="headerImagePath" type="text" :class="inputReadonlyClass" placeholder="选择图片（显示在每章开头）" readonly @click="selectHeaderImage">
              <button @click="selectHeaderImage" :class="buttonSecondaryClass">浏览</button>
            </div>
            <p class="text-xs text-gray-400 mt-2">将在每个章节标题前插入该图片，自动应用居中和多看样式。</p>
          </div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
          <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">手动模式</h2>
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">自定义正则 <span class="text-gray-400 font-normal">（单层模式，优先级高于自动扫描）</span></label>
            <input v-model="customRegex" type="text" :class="inputBaseClass + ' font-mono'" placeholder="例如: ^第[0-9]+章">
            <p class="text-xs text-gray-400 mt-2">留空则使用上方扫描结果或内置默认规则。</p>
          </div>
        </div>
      </template>

      <!-- Action Button -->
      <div class="flex items-center justify-between pt-2">
        <button v-if="outputLog" @click="clearLog" class="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">清除日志</button>
        <div v-else></div>
        <button v-if="batchMode" @click="runBatchConversion" :disabled="loading || txtFiles.length === 0"
          :class="['inline-flex items-center px-6 py-2.5 text-sm font-medium rounded-lg shadow-sm text-white transition-all duration-200',
            loading || txtFiles.length === 0
              ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 hover:shadow-md active:scale-[0.98]']"
        >
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ loading ? '转换中...' : `批量转换（${txtFiles.length} 个）` }}
        </button>
        <button v-else @click="runConversion" :disabled="loading || !txtPath || !epubPath || !title"
          :class="['inline-flex items-center px-6 py-2.5 text-sm font-medium rounded-lg shadow-sm text-white transition-all duration-200',
            loading || !txtPath || !epubPath || !title
              ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 hover:shadow-md active:scale-[0.98]']"
        >
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ loading ? '转换中...' : '开始转换' }}
        </button>
      </div>

      <OutputLog :log="outputLog" @copy="copyLog" />
    </div>
  </div>
</template>
