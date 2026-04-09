<script setup>
import { ref, computed, watch, inject } from 'vue'
import FileDropZone from './FileDropZone.vue'
import FontTargetSelector from './shared/FontTargetSelector.vue'
import SplitTargetSelector from './shared/SplitTargetSelector.vue'
import MergeFileList from './shared/MergeFileList.vue'
import OutputLog from './shared/OutputLog.vue'

const toast = inject('toast')

const props = defineProps({
  activeTool: String
})

// --- State ---
const loading = ref(false)
const outputLog = ref('')
const selectedOperation = ref('')
const inputPaths = ref([])
const outputPath = ref('')
const fontPath = ref('')
const regexPattern = ref('')
const selectedMode = ref('')
const operationCompleted = ref(false)

// Font encrypt target selection
const fontTargets = ref({ font_families: [], xhtml_files: [] })
const selectedFontFamilies = ref([])
const selectedXhtmlFiles = ref([])
const showFontTargetSelector = ref(false)

// OPF viewer
const opfContent = ref('')

// Merge file list
const mergeFiles = ref([])

// Split state
const splitTargets = ref([])
const selectedSplitPoints = ref([])
const showSplitTargetSelector = ref(false)

// Image compress options
const jpegQuality = ref(85)
const webpQuality = ref(80)
const pngToJpg = ref(true)

// Ad clean patterns
const adPatterns = ref([
  { id: 1, pattern: '.*广告.*', replacement: '', enabled: true },
  { id: 2, pattern: '.*推广.*', replacement: '', enabled: true },
])
let adPatternIdCounter = 3

// Built-in presets: each entry = [label, [{pattern, replacement, enabled}]]
const adPresets = [
  {
    label: '通用广告词',
    desc: '广告/推广/赞助',
    items: [
      { pattern: '.*广告.*', replacement: '', enabled: true },
      { pattern: '.*推广.*', replacement: '', enabled: true },
      { pattern: '.*赞助.*', replacement: '', enabled: true },
    ]
  },
  {
    label: '网址链接',
    desc: 'http(s) www 链接',
    items: [
      { pattern: 'https?://[^\\s\\n]+', replacement: '', enabled: true },
      { pattern: 'www\\.[a-zA-Z0-9\\-]+\\.[a-zA-Z]+[^\\s\\n]*', replacement: '', enabled: true },
    ]
  },
  {
    label: '小说站引流',
    desc: '正版/全本/公众号',
    items: [
      { pattern: '.*正版免费阅读.*', replacement: '', enabled: true },
      { pattern: '.*全本下载.*', replacement: '', enabled: true },
      { pattern: '.*关注.*公众号.*', replacement: '', enabled: true },
      { pattern: '.*加入.*VIP.*', replacement: '', enabled: true },
      { pattern: '.*纵横中文网.*', replacement: '', enabled: true },
      { pattern: '.*起点中文网.*', replacement: '', enabled: true },
    ]
  },
  {
    label: '章末水话',
    desc: '本章完/求票/未完待续',
    items: [
      { pattern: '本章完.*', replacement: '', enabled: true },
      { pattern: '未完待续.*', replacement: '', enabled: true },
      { pattern: '.*求月票.*', replacement: '', enabled: true },
      { pattern: '.*求推荐.*票?.*', replacement: '', enabled: true },
      { pattern: '.*求收藏.*', replacement: '', enabled: true },
      { pattern: '.*打赏.*', replacement: '', enabled: true },
    ]
  },
  {
    label: '排版清理',
    desc: '多余空行/空格',
    items: [
      { pattern: '\\n{3,}', replacement: '\\n\\n', enabled: true },
      { pattern: ' {2,}', replacement: ' ', enabled: true },
    ]
  },
]

// Track applied presets: { label -> [addedPatternIds] }
const appliedPresets = ref({})

const applyAdPreset = (preset) => {
  if (preset.label in appliedPresets.value) {
    // Already applied — remove it
    const idsToRemove = appliedPresets.value[preset.label]
    adPatterns.value = adPatterns.value.filter(p => !idsToRemove.includes(p.id))
    const newMap = { ...appliedPresets.value }
    delete newMap[preset.label]
    appliedPresets.value = newMap
    return
  }
  // Apply: add all items from preset, record their ids
  const newIds = []
  preset.items.forEach(item => {
    adPatterns.value.push({ ...item, id: adPatternIdCounter++ })
    newIds.push(adPatternIdCounter - 1)
  })
  appliedPresets.value = { ...appliedPresets.value, [preset.label]: newIds }
}

const removeAllAdPatterns = () => {
  adPatterns.value = []
  adPatternIdCounter = 3
  appliedPresets.value = {}
}

const operationsMap = {
  encrypt: { label: '加密 EPUB', desc: '对 EPUB 文件进行 DRM 加密处理', category: 'encrypt' },
  decrypt: { label: '解密 EPUB', desc: '移除 EPUB 文件的 DRM 加密', category: 'encrypt' },
  encrypt_font: { label: '字体加密', desc: '对 EPUB 内嵌字体进行混淆加密', category: 'encrypt' },
  reformat_convert: { label: '重构 / 转换', desc: 'EPUB 重构与版本转换', category: 'format', hasMode: true, modes: [{ value: 'reformat', label: '规范重构' }, { value: '3.0', label: '转为 EPUB3' }, { value: '2.0', label: '转为 EPUB2' }] },
  convert_chinese: { label: '简繁转换', desc: '简繁中文双向转换', category: 'format', hasMode: true, modes: [{ value: 's2t', label: '简体 → 繁体' }, { value: 't2s', label: '繁体 → 简体' }] },
  font_subset: { label: '字体子集化', desc: '精简内嵌字体，保留用到的字符', category: 'format' },
  view_opf: { label: 'OPF 查看', desc: '查看 OPF 文件和内部结构', category: 'format' },
  split_merge_epub: { label: '拆分 / 合并', desc: '拆分或合并多个 EPUB', category: 'format', hasMode: true, modes: [{ value: 'split', label: '拆分 EPUB' }, { value: 'merge', label: '合并 EPUB' }] },
  img_compress: { label: '图片压缩', desc: '压缩 EPUB 中的图片体积', category: 'image', hasCompressOptions: true },
  convert_image_format: { label: '图片格式转换', desc: '图片与 WebP 格式互转', category: 'image', hasMode: true, modes: [{ value: 'img_to_webp', label: '图片 → WebP' }, { value: 'webp_to_img', label: 'WebP → 图片' }] },
  phonetic: { label: '生僻字注音', desc: '为生僻字添加拼音标注', category: 'annotate' },
  comment: { label: '正则匹配→弹窗', desc: '正则匹配文本转为弹窗注释', category: 'annotate', hasRegex: true },
  footnote_conv: { label: '脚注→弹窗', desc: '脚注转为阅微弹窗样式', category: 'annotate', hasRegex: true },
  download_images: { label: '下载网络图片', desc: '将网络图片下载到本地', category: 'other' },
  yuewei: { label: '阅微→多看', desc: '注释格式转换', category: 'other' },
  zhangyue: { label: '掌阅→多看', desc: '掌阅脚注转为多看格式', category: 'other' },
  ad_clean: { label: '广告净化', desc: '用正则匹配并替换广告文字', category: 'other', hasAdPatterns: true }
}

const currentToolInfo = computed(() => operationsMap[selectedOperation.value] || { label: '请选择工具', desc: '' })
const needsFontPath = computed(() => selectedOperation.value === 'encrypt_font')
const needsRegex = computed(() => operationsMap[selectedOperation.value]?.hasRegex)
const needsMode = computed(() => operationsMap[selectedOperation.value]?.hasMode)
const needsCompressOptions = computed(() => operationsMap[selectedOperation.value]?.hasCompressOptions)
const needsAdPatterns = computed(() => operationsMap[selectedOperation.value]?.hasAdPatterns)
const needsFileInput = computed(() => !(selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'merge'))

const resetState = () => {
  inputPaths.value = []
  outputPath.value = ''
  fontPath.value = ''
  regexPattern.value = ''
  outputLog.value = ''
  operationCompleted.value = false
  fontTargets.value = { font_families: [], xhtml_files: [] }
  selectedFontFamilies.value = []
  selectedXhtmlFiles.value = []
  showFontTargetSelector.value = false
  opfContent.value = ''
  mergeFiles.value = []
  splitTargets.value = []
  selectedSplitPoints.value = []
  showSplitTargetSelector.value = false
  jpegQuality.value = 85
  webpQuality.value = 80
  pngToJpg.value = true
  adPatterns.value = [
    { id: 1, pattern: '.*广告.*', replacement: '', enabled: true },
    { id: 2, pattern: '.*推广.*', replacement: '', enabled: true },
  ]
  adPatternIdCounter = 3
  appliedPresets.value = {}
}

watch(() => props.activeTool, (newVal) => {
  if (newVal) {
    selectedOperation.value = newVal
    resetState()
  }
}, { immediate: true })

watch(selectedOperation, (val) => {
  selectedMode.value = operationsMap[val]?.hasMode ? operationsMap[val].modes[0].value : ''
})

// --- Shared Style Classes ---
const inputBaseClass = 'w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-800 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:focus:ring-indigo-900/30 outline-none transition-all'
const inputReadonlyClass = inputBaseClass + ' cursor-pointer'
const buttonBaseClass = 'px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1'
const buttonPrimaryClass = buttonBaseClass + ' bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white shadow-sm hover:shadow active:scale-[0.98] focus:ring-indigo-500'
const buttonSecondaryClass = buttonBaseClass + ' bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 focus:ring-gray-400'

// --- Methods ---
const fileName = (p) => p.split(/[\\/]/).pop()

const handleFileDrop = (pathsOrPath) => {
  if (!pathsOrPath) return
  const paths = Array.isArray(pathsOrPath) ? pathsOrPath : [pathsOrPath]
  const validPaths = paths.map(p => typeof p === 'string' ? p : p.path).filter(Boolean)
  const filteredPaths = validPaths.filter(p => p.toLowerCase().endsWith('.epub'))
  if (filteredPaths.length === 0) { toast?.error?.('请选择 EPUB 文件'); return }
  const existing = new Set(inputPaths.value)
  const newPaths = filteredPaths.filter(p => !existing.has(p))
  if (newPaths.length > 0) { inputPaths.value = [...inputPaths.value, ...newPaths]; toast?.success?.(`已添加 ${newPaths.length} 个文件`) }
}

const selectFile = async () => {
  try {
    const paths = await window.go.main.App.SelectFiles()
    if (paths && paths.length > 0) handleFileDrop(paths)
  } catch (err) { console.error(err) }
}

const removeFile = (index) => { inputPaths.value.splice(index, 1) }
const clearFiles = () => { inputPaths.value = [] }

const selectOutputPath = async () => {
  try {
    const path = await window.go.main.App.SelectDirectory()
    if (path) { outputPath.value = path; toast?.success?.('已设置输出目录') }
  } catch (err) { console.error(err) }
}

const selectFontFile = async () => {
  try {
    const path = await window.go.main.App.SelectFile()
    if (path) { fontPath.value = path; toast?.success?.('已选择字体文件') }
  } catch (err) { console.error(err) }
}

const appendLog = (text) => { outputLog.value += text + '\n' }

const runBackend = async (args, onSuccess, onFail) => {
  loading.value = true
  let unlistener = null
  if (window.runtime && window.runtime.EventsOn) {
    unlistener = window.runtime.EventsOn('backend_log', (data) => {
      if (data && data.text !== undefined) appendLog(data.text)
    })
  }
  try {
    const result = await window.go.main.App.RunBackend(args)
    if (!unlistener) {
      if (result.stderr) appendLog(result.stderr)
      if (result.stdout) appendLog(result.stdout)
    }
    if (onSuccess) onSuccess(result)
  } catch (err) {
    const errStr = String(err)
    if (errStr.includes('ZHANGYUE_DRM') || errStr.includes('zhangyue_drm')) {
      appendLog('检测到掌阅 DRM 加密，不支持解密')
      toast?.warning?.('检测到掌阅 DRM 加密，不支持解密')
    } else {
      appendLog('执行失败: ' + errStr)
    }
    if (onFail) onFail(errStr)
  } finally {
    loading.value = false
    if (unlistener) unlistener()
  }
}

const scanFontTargets = async () => {
  if (inputPaths.value.length === 0) { toast?.warning?.('请先选择输入文件'); return }
  loading.value = true
  const filePath = inputPaths.value[0]
  outputLog.value = `▶ 扫描字体加密目标: ${fileName(filePath)}\n${'─'.repeat(40)}\n`
  const args = ['--plugin', 'epub_tool', '--operation', 'list_font_targets', '--input-path', filePath]
  try {
    const result = await window.go.main.App.RunBackend(args)
    if (result.stderr) outputLog.value += result.stderr + '\n'
    const targets = JSON.parse(result.stdout)
    fontTargets.value = targets
    selectedFontFamilies.value = [...targets.font_families]
    selectedXhtmlFiles.value = [...targets.xhtml_files]
    showFontTargetSelector.value = true
    outputLog.value += `✅ 扫描完成: ${targets.font_families.length} 个字体族, ${targets.xhtml_files.length} 个 XHTML 文件\n`
    toast?.success?.('扫描完成，请选择要加密的目标')
  } catch (err) { outputLog.value += `❌ 扫描失败: ${String(err)}\n`; toast?.error?.('扫描失败') }
  loading.value = false
}

const toggleAllFontFamilies = () => { selectedFontFamilies.value = [...fontTargets.value.font_families] }
const invertFontFamilies = () => { const c = new Set(selectedFontFamilies.value); selectedFontFamilies.value = fontTargets.value.font_families.filter(f => !c.has(f)) }
const toggleAllXhtmlFiles = () => { selectedXhtmlFiles.value = [...fontTargets.value.xhtml_files] }
const invertXhtmlFiles = () => { const c = new Set(selectedXhtmlFiles.value); selectedXhtmlFiles.value = fontTargets.value.xhtml_files.filter(f => !c.has(f)) }
const cancelFontTargetSelection = () => { showFontTargetSelector.value = false }

const scanSplitTargets = async () => {
  if (inputPaths.value.length === 0) { toast?.warning?.('请先选择输入文件'); return }
  loading.value = true
  const filePath = inputPaths.value[0]
  outputLog.value = `▶ 扫描拆分目标: ${fileName(filePath)}\n${'─'.repeat(40)}\n`
  const args = ['--plugin', 'epub_tool', '--operation', 'list_split_targets', '--input-path', filePath]
  try {
    const result = await window.go.main.App.RunBackend(args)
    if (result.stderr) outputLog.value += result.stderr + '\n'
    const targets = JSON.parse(result.stdout)
    splitTargets.value = targets
    selectedSplitPoints.value = []; showSplitTargetSelector.value = true
    outputLog.value += `✅ 扫描完成: ${targets.length} 个章节\n`
    toast?.success?.('扫描完成，请选择拆分点')
  } catch (err) { outputLog.value += `❌ 扫描失败: ${String(err)}\n`; toast?.error?.('扫描失败') }
  loading.value = false
}

const toggleAllSplitPoints = () => { selectedSplitPoints.value = splitTargets.value.map((_, i) => i) }
const invertSplitPoints = () => { const c = new Set(selectedSplitPoints.value); selectedSplitPoints.value = splitTargets.value.map((_, i) => i).filter(i => !c.has(i)) }
const cancelSplitTargetSelection = () => { showSplitTargetSelector.value = false }

const handleMergeFileDrop = (pathsOrPath) => {
  if (!pathsOrPath) return
  const paths = Array.isArray(pathsOrPath) ? pathsOrPath : [pathsOrPath]
  const epubPaths = paths.filter(p => typeof p === 'string' && p.toLowerCase().endsWith('.epub'))
  if (epubPaths.length === 0) { toast?.error?.('请选择 EPUB 文件'); return }
  const existing = new Set(mergeFiles.value)
  const newPaths = epubPaths.filter(p => !existing.has(p))
  if (newPaths.length > 0) { mergeFiles.value = [...mergeFiles.value, ...newPaths]; toast?.success?.(`已添加 ${newPaths.length} 个文件`) }
}

const selectMergeFiles = async () => {
  try { const paths = await window.go.main.App.SelectFiles(); if (paths && paths.length > 0) handleMergeFileDrop(paths) }
  catch (err) { console.error(err) }
}

const removeMergeFile = (index) => { mergeFiles.value.splice(index, 1) }
const clearMergeFiles = () => { mergeFiles.value = [] }

// Ad pattern management
const addAdPattern = () => {
  adPatterns.value.push({ id: adPatternIdCounter++, pattern: '', replacement: '', enabled: true })
}

const removeAdPattern = (id) => {
  adPatterns.value = adPatterns.value.filter(p => p.id !== id)
}

const toggleAdPattern = (pattern) => { pattern.enabled = !pattern.enabled }

const updateAdPattern = (pattern, field, value) => {
  pattern[field] = value
}

const moveAdPatternUp = (index) => {
  if (index <= 0) return
  const list = adPatterns.value
  ;[list[index - 1], list[index]] = [list[index], list[index - 1]]
}

const moveAdPatternDown = (index) => {
  if (index >= adPatterns.value.length - 1) return
  const list = adPatterns.value
  ;[list[index], list[index + 1]] = [list[index + 1], list[index]]
}

const selectAllAdPatterns = () => { adPatterns.value.forEach(p => p.enabled = true) }
const deselectAllAdPatterns = () => { adPatterns.value.forEach(p => p.enabled = false) }

const runTool = async () => {
  if (selectedOperation.value === 'encrypt_font' && !showFontTargetSelector.value) { await scanFontTargets(); return }
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'split' && !showSplitTargetSelector.value) { await scanSplitTargets(); return }

  // view_opf
  if (selectedOperation.value === 'view_opf') {
    loading.value = true; opfContent.value = ''
    const filePath = inputPaths.value[0]
    outputLog.value = `▶ OPF 查看: ${fileName(filePath)}\n${'─'.repeat(40)}\n`
    const args = ['--plugin', 'epub_tool', '--operation', 'view_opf', '--input-path', filePath]
    try {
      await runBackend(args, (result) => {
        if (result.stdout) {
          const opfMatch = result.stdout.match(/=== OPF Content ===([\s\S]*?)(?==== File List ===|$)/)
          if (opfMatch) opfContent.value = opfMatch[1].trim()
        }
        appendLog('✅ OPF 查看完成')
        toast?.success?.('OPF 查看完成')
      })
    } catch (err) { toast?.error?.('OPF 查看失败') }
    operationCompleted.value = true; return
  }

  // merge
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'merge') {
    if (mergeFiles.value.length < 2) { toast?.warning?.('请至少添加 2 个 EPUB 文件'); return }
    loading.value = true
    outputLog.value = `▶ 合并 EPUB（共 ${mergeFiles.value.length} 个文件）\n${'─'.repeat(40)}\n`
    mergeFiles.value.forEach((p, i) => { outputLog.value += `  ${i + 1}. ${fileName(p)}\n` })
    outputLog.value += `${'─'.repeat(40)}\n`
    const args = ['--plugin', 'epub_tool', '--operation', 'merge', '--input-paths', ...mergeFiles.value]
    if (outputPath.value) args.push('--output-path', outputPath.value)
    try {
      await runBackend(args, () => { appendLog('✅ 合并完成'); toast?.success?.('EPUB 合并完成') })
    } catch (err) { toast?.error?.('EPUB 合并失败') }
    operationCompleted.value = true; return
  }

  // split
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'split' && showSplitTargetSelector.value) {
    if (selectedSplitPoints.value.length === 0) { toast?.warning?.('请至少选择一个拆分点'); return }
    loading.value = true
    const filePath = inputPaths.value[0]
    const sortedPoints = [...selectedSplitPoints.value].sort((a, b) => a - b)
    outputLog.value = `▶ 拆分 EPUB: ${fileName(filePath)}\n${'─'.repeat(40)}\n  拆分点: ${sortedPoints.join(',')}\n${'─'.repeat(40)}\n`
    const args = ['--plugin', 'epub_tool', '--operation', 'split', '--input-path', filePath, '--split-points', sortedPoints.join(',')]
    if (outputPath.value) args.push('--output-path', outputPath.value)
    try {
      await runBackend(args, () => { appendLog('✅ 拆分完成'); toast?.success?.('EPUB 拆分完成') })
    } catch (err) { toast?.error?.('EPUB 拆分失败') }
    operationCompleted.value = true
    showSplitTargetSelector.value = false; splitTargets.value = []; selectedSplitPoints.value = []; return
  }

  // Batch execution
  loading.value = true
  const total = inputPaths.value.length; let successCount = 0; let failCount = 0
  outputLog.value = `▶ 批量执行: ${currentToolInfo.value.label}（共 ${total} 个文件）\n${'─'.repeat(40)}\n`
  toast?.info?.(`开始处理 ${total} 个文件...`, 2000)
  for (let i = 0; i < total; i++) {
    const filePath = inputPaths.value[i]; const name = fileName(filePath)
    outputLog.value += `\n[${i + 1}/${total}] ${name}\n`
    let backendOperation = selectedOperation.value
    if (selectedOperation.value === 'reformat_convert') {
      backendOperation = selectedMode.value === 'reformat' ? 'reformat' : 'convert_version'
    } else if (selectedOperation.value === 'convert_chinese') {
      backendOperation = selectedMode.value
    } else if (selectedOperation.value === 'convert_image_format') {
      backendOperation = selectedMode.value
    }
    const args = ['--plugin', 'epub_tool', '--operation', backendOperation, '--input-path', filePath]
    if (fontPath.value && needsFontPath.value) args.push('--font-path', fontPath.value)
    if (outputPath.value) args.push('--output-path', outputPath.value)
    if (regexPattern.value && needsRegex.value) args.push('--regex-pattern', regexPattern.value)
    if (selectedOperation.value === 'encrypt_font' && showFontTargetSelector.value) {
      if (selectedFontFamilies.value.length > 0) args.push('--target-font-families', ...selectedFontFamilies.value)
      if (selectedXhtmlFiles.value.length > 0) args.push('--target-xhtml-files', ...selectedXhtmlFiles.value)
    }
    if (selectedOperation.value === 'reformat_convert' && selectedMode.value !== 'reformat') {
      args.push('--target-version', selectedMode.value)
    }
    if (selectedOperation.value === 'img_compress') {
      args.push('--jpeg-quality', String(jpegQuality.value), '--webp-quality', String(webpQuality.value), '--png-to-jpg', pngToJpg.value ? 'true' : 'false')
    }
    if (selectedOperation.value === 'ad_clean') {
      const enabledPatterns = adPatterns.value.filter(p => p.enabled && p.pattern.trim())
      if (enabledPatterns.length === 0) {
        toast?.warning?.('请至少添加一条启用的正则表达式')
        loading.value = false
        return
      }
      const patternsStr = enabledPatterns.map(p => `${p.pattern}|||${p.replacement}`).join('|||PATTERNS|||')
      args.push('--ad-patterns', patternsStr)
    }
    try {
      await runBackend(args, () => { appendLog('  ✅ 完成'); successCount++ }, () => { failCount++ })
    } catch (err) { failCount++ }
  }
  appendLog(`\n${'─'.repeat(40)}\n📊 结果: 成功 ${successCount}，失败 ${failCount}\n`)
  operationCompleted.value = true
  if (selectedOperation.value === 'encrypt_font') {
    showFontTargetSelector.value = false; fontTargets.value = { font_families: [], xhtml_files: [] }
    selectedFontFamilies.value = []; selectedXhtmlFiles.value = []
  }
  if (failCount === 0) toast?.success?.(`全部完成（${successCount} 个文件）`)
  else toast?.warning?.(`完成: ${successCount} 成功, ${failCount} 失败`)
}

const openLogFile = async () => {
  try { await window.go.main.App.OpenLogFile() } catch (err) { toast?.error?.('打开日志文件失败') }
}

const copyLog = async () => {
  try { await navigator.clipboard.writeText(outputLog.value); toast?.success?.('已复制日志') } catch { toast?.error?.('复制失败') }
}

const copyOpfContent = async () => {
  try { await navigator.clipboard.writeText(opfContent.value); toast?.success?.('已复制 OPF 内容') } catch { toast?.error?.('复制失败') }
}

const clearLog = () => { outputLog.value = ''; operationCompleted.value = false }

const isActionDisabled = computed(() => {
  if (loading.value) return true
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'merge') {
    return mergeFiles.value.length < 2
  }
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'split') {
    return showSplitTargetSelector.value ? selectedSplitPoints.value.length === 0 : inputPaths.value.length === 0
  }
  return inputPaths.value.length === 0
})

const actionButtonText = computed(() => {
  if (loading.value) return '执行中...'
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'merge') {
    return mergeFiles.value.length > 0 ? `合并执行（${mergeFiles.value.length} 个）` : '合并执行'
  }
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'split') {
    return showSplitTargetSelector.value ? `确认拆分（${selectedSplitPoints.value.length} 个点）` : '扫描章节'
  }
  return inputPaths.value.length > 1 ? `批量执行（${inputPaths.value.length} 个）` : '开始执行'
})
</script>

<template>
  <div class="min-h-0 w-full flex flex-col space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ currentToolInfo.label }}</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ currentToolInfo.desc }}</p>
    </header>

    <div class="flex-1 min-h-0 overflow-y-auto space-y-5">

      <!-- Merge Mode -->
      <template v-if="selectedOperation === 'split_merge_epub' && selectedMode === 'merge'">
        <MergeFileList
          :files="mergeFiles"
          @drop="handleMergeFileDrop"
          @select="selectMergeFiles"
          @remove="removeMergeFile"
          @clear="clearMergeFiles"
        />
      </template>

      <!-- Normal File Selection + All Options (no tab switch) -->
      <template v-else>
        <div class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
          <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">文件路径</h2>
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
              输入文件 <span class="text-red-400">*</span>
              <span v-if="inputPaths.length > 0" class="ml-2 text-xs text-indigo-500 font-normal">已选 {{ inputPaths.length }} 个文件</span>
            </label>
            <div class="space-y-2">
              <FileDropZone accept=".epub,application/epub+zip" :multiple="true" @drop="handleFileDrop" @click="selectFile" :disabled="false">
                <div class="flex flex-col items-center justify-center py-6 px-4 text-center">
                  <div class="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mb-2">
                    <svg class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <p class="text-sm font-medium text-gray-700 dark:text-gray-300">拖拽 EPUB 文件到此处（支持多选）</p>
                  <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">或点击选择文件</p>
                </div>
              </FileDropZone>
              <div v-if="inputPaths.length > 0" class="space-y-1">
                <div v-for="(p, idx) in inputPaths" :key="p" class="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-900/50 rounded-lg group">
                  <div class="flex items-center min-w-0 flex-1 mr-2">
                    <span class="text-xs text-gray-400 mr-2 flex-shrink-0">{{ idx + 1 }}.</span>
                    <span class="text-xs text-gray-600 dark:text-gray-400 truncate" :title="p">{{ fileName(p) }}</span>
                  </div>
                  <button @click="removeFile(idx)" class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <button @click="clearFiles" class="text-xs text-gray-400 hover:text-red-500 transition-colors mt-1">清空全部</button>
              </div>
            </div>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">输出目录 <span class="text-gray-400 font-normal">（可选）</span></label>
            <div class="flex space-x-2">
              <input v-model="outputPath" type="text" :class="inputReadonlyClass" placeholder="默认为源文件同目录" readonly @click="selectOutputPath">
              <button @click="selectOutputPath" :class="buttonSecondaryClass">浏览</button>
            </div>
          </div>
        </div>
      </template>

      <!-- Mode Selection (reformat/convert, convert_chinese, split/merge, image format) -->
      <div v-if="needsMode" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">转换模式</h2>
        <div class="flex space-x-3">
          <label v-for="mode in currentToolInfo.modes" :key="mode.value"
            :class="[
              'flex-1 flex items-center justify-center px-4 py-2.5 rounded-lg border-2 cursor-pointer transition-all duration-150 text-sm font-medium',
              selectedMode === mode.value
                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
            ]"
          >
            <input type="radio" v-model="selectedMode" :value="mode.value" class="sr-only">
            <span>{{ mode.label }}</span>
          </label>
        </div>
      </div>

      <!-- Font Path -->
      <div v-if="needsFontPath" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">加密选项</h2>
        <div>
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">字体文件 <span class="text-gray-400 font-normal">（可选）</span></label>
          <div class="flex space-x-2">
            <input v-model="fontPath" type="text" :class="inputReadonlyClass" placeholder="选择字体文件用于混淆加密" readonly @click="selectFontFile">
            <button @click="selectFontFile" :class="buttonSecondaryClass">浏览</button>
          </div>
        </div>
      </div>

      <!-- Regex Pattern -->
      <div v-if="needsRegex" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">正则选项</h2>
        <div>
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">正则表达式</label>
          <input v-model="regexPattern" type="text" :class="inputBaseClass + ' font-mono'"
            :placeholder="selectedOperation === 'footnote_conv' ? '默认: \\[(\\d+)\\] 或 #.+' : '默认: \\[(.*?)\\]'">
          <p class="text-xs text-gray-400 mt-2">留空将使用默认正则表达式。</p>
        </div>
      </div>

      <!-- Image Compress Options -->
      <div v-if="needsCompressOptions" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-5">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">压缩选项</h2>
        <div class="space-y-4">
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">JPEG 质量</label>
              <span class="text-sm font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded">{{ jpegQuality }}</span>
            </div>
            <input type="range" v-model.number="jpegQuality" min="10" max="100" step="5"
              class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600">
            <div class="flex justify-between text-xs text-gray-400 mt-1"><span>10</span><span>100</span></div>
          </div>
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">WebP 质量</label>
              <span class="text-sm font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded">{{ webpQuality }}</span>
            </div>
            <input type="range" v-model.number="webpQuality" min="10" max="100" step="5"
              class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600">
            <div class="flex justify-between text-xs text-gray-400 mt-1"><span>10</span><span>100</span></div>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">PNG 转 JPG</label>
              <p class="text-xs text-gray-400 mt-0.5">无透明度的 PNG 转为 JPG 可减小体积</p>
            </div>
            <button @click="pngToJpg = !pngToJpg"
              :class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200', pngToJpg ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600']">
              <span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 shadow-sm', pngToJpg ? 'translate-x-6' : 'translate-x-1']" />
            </button>
          </div>
        </div>
      </div>

      <!-- Ad Pattern Editor -->
      <div v-if="needsAdPatterns" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">广告净化规则</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1.5 leading-relaxed">按顺序执行；仅启用的规则会参与匹配。替换留空表示删除匹配内容。</p>
          </div>
          <div class="flex shrink-0 gap-2">
            <button
              type="button"
              @click="selectAllAdPatterns"
              class="px-3 py-2 text-xs font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-400 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            >全选</button>
            <button
              type="button"
              @click="deselectAllAdPatterns"
              class="px-3 py-2 text-xs font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-400 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
            >取消全选</button>
          </div>
        </div>

        <!-- Presets -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400 dark:text-gray-500">快捷预设（点击添加）</span>
            <button v-if="adPatterns.length > 2" @click="removeAllAdPatterns" class="text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors">清空全部</button>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="preset in adPresets"
              :key="preset.label"
              @click="applyAdPreset(preset)"
              :disabled="false"
              :class="['inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border transition-all duration-150 focus:outline-none focus:ring-0 focus-visible:ring-2 focus-visible:ring-indigo-500/50 focus-visible:ring-offset-0', (preset.label in appliedPresets) ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 cursor-pointer' : 'border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20']"
            >
              <svg v-if="preset.label in appliedPresets" class="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
              {{ preset.label }}
            </button>
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500">每个预设包含多条规则，点击即批量添加；可在下方自行增删调整</p>
        </div>

        <ul class="space-y-3 max-h-[min(22rem,55vh)] overflow-y-auto pr-1 -mr-0.5 [scrollbar-gutter:stable]">
          <li
            v-for="(p, idx) in adPatterns"
            :key="p.id"
            class="rounded-xl border border-gray-200/90 dark:border-gray-600 bg-gray-50/90 dark:bg-gray-900/35 p-3 sm:p-4 transition-shadow hover:shadow-sm dark:hover:border-gray-500/80"
          >
            <div class="flex items-center gap-3 mb-3">
              <label class="flex items-center gap-2.5 min-w-0 cursor-pointer select-none">
                <input
                  v-model="p.enabled"
                  type="checkbox"
                  class="h-4 w-4 shrink-0 rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-0 dark:focus:ring-offset-gray-900 cursor-pointer"
                >
                <span
                  class="inline-flex h-7 min-w-[1.75rem] items-center justify-center rounded-md bg-white dark:bg-gray-800 px-2 text-xs font-mono font-medium text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600"
                >{{ idx + 1 }}</span>
                <span class="text-xs text-gray-500 dark:text-gray-400 truncate sm:max-w-[8rem]">{{ p.enabled ? '已启用' : '已跳过' }}</span>
              </label>
              <div class="flex-1 min-w-0" />
              <div
                class="inline-flex shrink-0 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-sm"
                role="group"
                aria-label="规则操作"
              >
                <button
                  type="button"
                  title="上移"
                  :disabled="idx === 0"
                  @click="moveAdPatternUp(idx)"
                  class="p-2 text-gray-500 hover:bg-gray-50 hover:text-gray-800 dark:hover:bg-gray-700/80 dark:hover:text-gray-200 disabled:opacity-25 disabled:pointer-events-none transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg>
                </button>
                <span class="w-px self-stretch bg-gray-200 dark:bg-gray-600" aria-hidden="true" />
                <button
                  type="button"
                  title="下移"
                  :disabled="idx === adPatterns.length - 1"
                  @click="moveAdPatternDown(idx)"
                  class="p-2 text-gray-500 hover:bg-gray-50 hover:text-gray-800 dark:hover:bg-gray-700/80 dark:hover:text-gray-200 disabled:opacity-25 disabled:pointer-events-none transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
                </button>
                <span class="w-px self-stretch bg-gray-200 dark:bg-gray-600" aria-hidden="true" />
                <button
                  type="button"
                  title="删除此规则"
                  @click="removeAdPattern(p.id)"
                  class="p-2 text-gray-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 dark:hover:text-red-400 transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>

            <div class="grid gap-3 sm:grid-cols-[1fr_minmax(0,auto)_minmax(0,1fr)] sm:items-end sm:gap-3">
              <div class="min-w-0 space-y-1.5">
                <label :for="`ad-pattern-${p.id}`" class="text-xs font-medium text-gray-500 dark:text-gray-400">正则</label>
                <input
                  :id="`ad-pattern-${p.id}`"
                  v-model="p.pattern"
                  type="text"
                  :class="inputBaseClass + ' w-full font-mono text-xs py-2'"
                  placeholder="例如 .*广告.*"
                  autocomplete="off"
                  spellcheck="false"
                >
              </div>
              <div class="hidden sm:flex items-end justify-center pb-2 text-gray-400 dark:text-gray-500" aria-hidden="true">
                <span class="text-lg leading-none font-light">→</span>
              </div>
              <div class="min-w-0 space-y-1.5 sm:col-span-1">
                <label :for="`ad-repl-${p.id}`" class="text-xs font-medium text-gray-500 dark:text-gray-400">替换为</label>
                <input
                  :id="`ad-repl-${p.id}`"
                  v-model="p.replacement"
                  type="text"
                  :class="inputBaseClass + ' w-full font-mono text-xs py-2'"
                  placeholder="留空则删除匹配内容"
                  autocomplete="off"
                  spellcheck="false"
                >
              </div>
            </div>
          </li>
        </ul>

        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between pt-1 border-t border-gray-100 dark:border-gray-700/80">
          <button
            type="button"
            @click="addAdPattern"
            class="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-400 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
            <span>添加规则</span>
          </button>
          <p class="text-xs text-gray-400 dark:text-gray-500 sm:text-right sm:max-w-md leading-relaxed">规则自上而下依次应用；建议把更具体的正则放在前面。</p>
        </div>
      </div>

      <!-- Font Encrypt Target Selector -->
      <FontTargetSelector v-if="showFontTargetSelector"
        :fontFamilies="fontTargets.font_families"
        :xhtmlFiles="fontTargets.xhtml_files"
        v-model:selectedFontFamilies="selectedFontFamilies"
        v-model:selectedXhtmlFiles="selectedXhtmlFiles"
        @toggleAllFonts="toggleAllFontFamilies"
        @invertFonts="invertFontFamilies"
        @toggleAllXhtml="toggleAllXhtmlFiles"
        @invertXhtml="invertXhtmlFiles"
        @cancel="cancelFontTargetSelection"
        @confirm="runTool"
      />

      <!-- Split EPUB Target Selector -->
      <SplitTargetSelector v-if="selectedOperation === 'split_merge_epub' && selectedMode === 'split' && showSplitTargetSelector"
        :targets="splitTargets"
        v-model:selectedPoints="selectedSplitPoints"
        @toggleAll="toggleAllSplitPoints"
        @invert="invertSplitPoints"
        @cancel="cancelSplitTargetSelection"
        @confirm="runTool"
      />

      <OutputLog
        :log="outputLog"
        :showOpenLog="operationCompleted"
        :opfContent="opfContent"
        @copy="copyLog"
        @copyOpf="copyOpfContent"
        @openLog="openLogFile"
        @clear="clearLog"
      />

      <!-- Action Bar -->
      <div class="flex items-center gap-2 sm:gap-3">
        <!-- Left status -->
        <div v-if="loading" class="flex items-center gap-1.5 text-xs text-indigo-500">
          <svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>执行中…</span>
        </div>
        <div v-else-if="outputLog" class="flex items-center gap-1.5 text-xs text-green-500 dark:text-green-400">
          <span class="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span>完成</span>
        </div>
        <div v-else class="flex-1 min-w-0" />
        <!-- Run button -->
        <button @click="runTool" :disabled="isActionDisabled"
          :class="['inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-150 active:scale-[0.97]', isActionDisabled ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white shadow-sm hover:shadow']"
        >
          <svg v-if="loading" class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ actionButtonText }}
        </button>
      </div>
    </div>
  </div>
</template>
