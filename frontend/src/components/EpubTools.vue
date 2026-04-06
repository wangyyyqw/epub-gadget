<script setup>
import { ref, computed, watch, nextTick, inject } from 'vue'
import FileDropZone from './FileDropZone.vue'
import FontTargetSelector from './shared/FontTargetSelector.vue'
import SplitTargetSelector from './shared/SplitTargetSelector.vue'
import MergeFileList from './shared/MergeFileList.vue'
import OutputLog from './shared/OutputLog.vue'

const toast = inject('toast')

const props = defineProps({
  activeTool: String
})

import { useFileManager } from '../composables/useFileManager'
import { useEpubProcess } from '../composables/useEpubProcess'

// --- State ---
const { inputPaths, outputPath, handleFileDrop: handleEpubDrop, selectFile, removeFile, clearFiles, selectOutputPath } = useFileManager(toast, ['.epub'])
const { loading, outputLog, appendLog, clearLog, runBackend } = useEpubProcess(toast)

const selectedOperation = ref('')
const fontPath = ref('')
const regexPattern = ref('')
const operationCompleted = ref(false)

// Font encrypt target selection state
const fontTargets = ref({ font_families: [], xhtml_files: [] })
const selectedFontFamilies = ref([])
const selectedXhtmlFiles = ref([])
const showFontTargetSelector = ref(false)

// OPF viewer state
const opfContent = ref('')

// Merge file list state
const mergeFiles = ref([])

// Split state
const splitTargets = ref([])
const selectedSplitPoints = ref([])
const showSplitTargetSelector = ref(false)

// Image compress options
const jpegQuality = ref(85)
const webpQuality = ref(80)
const pngToJpg = ref(true)

watch(() => props.activeTool, (newVal) => {
  if (newVal) {
    selectedOperation.value = newVal
    inputPaths.value = []; outputPath.value = ''; fontPath.value = ''; regexPattern.value = ''
    outputLog.value = ''; operationCompleted.value = false
    fontTargets.value = { font_families: [], xhtml_files: [] }
    selectedFontFamilies.value = []; selectedXhtmlFiles.value = []; showFontTargetSelector.value = false
    opfContent.value = ''; mergeFiles.value = []
    splitTargets.value = []; selectedSplitPoints.value = []; showSplitTargetSelector.value = false
    jpegQuality.value = 85; webpQuality.value = 80; pngToJpg.value = true
  }
}, { immediate: true })

const operationsMap = {
  encrypt: { label: '加密 EPUB', desc: '对 EPUB 文件进行 DRM 加密处理', details: '使用文件名混淆等方式对 EPUB 内容进行保护。', category: 'encrypt' },
  decrypt: { label: '解密 EPUB', desc: '移除 EPUB 文件的 DRM 加密', details: '解密受保护的 EPUB 文件，还原为可自由阅读的格式。', category: 'encrypt' },
  encrypt_font: { label: '字体加密', desc: '对 EPUB 内嵌字体进行混淆加密', details: '按照 EPUB 规范对内嵌字体进行 Adobe 或 IDPF 方式的混淆处理，防止字体被直接提取使用。', category: 'encrypt' },
  reformat_convert: { label: '重构 / 转换', desc: 'EPUB重构与版本转换', details: '解包并重新构建EPUB结构规范，或者在 EPUB2.0 和 EPUB3.0 规范之间相互转换。', category: 'format', hasMode: true, modes: [{ value: 'reformat', label: '规范重构 (不改版本)' }, { value: '3.0', label: '转为 EPUB3' }, { value: '2.0', label: '转为 EPUB2' }] },
  convert_chinese: { label: '简繁转换', desc: '简体中文与繁体中文互转', details: '基于词组级别的精确转换，支持简转繁和繁转简双向转换。', category: 'format', hasMode: true, modes: [{ value: 's2t', label: '简体 → 繁体' }, { value: 't2s', label: '繁体 → 简体' }] },
  font_subset: { label: '字体子集化', desc: '精简 EPUB 内嵌字体，仅保留用到的字符', details: '分析 EPUB 内容中实际使用的字符，生成最小化的字体子集，可大幅缩减文件体积。', category: 'format' },
  view_opf: { label: 'OPF 查看', desc: '查看 EPUB 的 OPF 文件内容和内部结构', details: '从 EPUB 中提取 OPF 文件内容，以格式化 XML 形式展示，同时列出 EPUB 内部文件结构。', category: 'format' },
  split_merge_epub: { label: '拆分 / 合并', desc: '合并多个或按章拆分 EPUB', details: '将多个 EPUB 拖入列表合并为一个，或分析当前 EPUB 结构并指定拆分点生成多个拆分文件。', category: 'format', hasMode: true, modes: [{ value: 'split', label: '拆分 EPUB' }, { value: 'merge', label: '合并 EPUB' }] },
  img_compress: { label: '图片压缩', desc: '压缩 EPUB 中所有图片的体积', details: '支持 JPEG/PNG/WebP/BMP 全格式压缩。可调节 JPEG 和 WebP 的压缩质量，无透明度的 PNG 可转为 JPG 大幅减小体积，有透明度的 PNG 自动转为 PNG-8 二值透明。', category: 'image', hasCompressOptions: true },
  convert_image_format: { label: '图片格式转换', desc: '在图片和 WebP 格式之间互转', details: 'WebP 格式可大幅减小体积，传统图片格式兼容性更好。', category: 'image', hasMode: true, modes: [{ value: 'img_to_webp', label: '图片 → WebP' }, { value: 'webp_to_img', label: 'WebP → 图片' }] },
  phonetic: { label: '生僻字注音', desc: '为 EPUB 中的生僻字添加拼音注音', details: '自动识别生僻字并添加 Ruby 拼音标注，方便阅读生僻汉字。', category: 'annotate' },
  comment: { label: '正则匹配→弹窗', desc: '用正则表达式匹配文本并转为弹窗注释', details: '将匹配到的注释内容转换为多看/Kindle 支持的弹窗式注释，点击即可查看。', category: 'annotate', hasRegex: true },
  footnote_conv: { label: '脚注→弹窗', desc: '将已有的链接式脚注转为阅微弹窗样式', details: '将 EPUB 中已有的超链接脚注转换为阅微弹窗样式的注释，阅读更流畅。', category: 'annotate', hasRegex: true },
  download_images: { label: '下载网络图片', desc: '将 EPUB 中引用的网络图片下载到本地', details: '扫描 EPUB 中所有引用外部 URL 的图片，下载并嵌入到 EPUB 文件中，确保离线阅读正常。', category: 'other' },
  yuewei: { label: '阅微→多看', desc: '将阅微格式的注释转换为多看格式', details: '兼容阅微平台导出的 EPUB 注释格式，转换为多看阅读器支持的标准格式。', category: 'other' },
  zhangyue: { label: '掌阅→多看', desc: '将掌阅格式的脚注转换为多看格式', details: '将掌阅平台 EPUB 中散落在正文的 aside 脚注提取出来，转换为多看阅读器支持的标准弹窗注释格式。', category: 'other' }
}

const currentToolInfo = computed(() => operationsMap[selectedOperation.value] || { label: '未知功能', desc: '', details: '' })
const needsFontPath = computed(() => selectedOperation.value === 'encrypt_font')
const needsRegex = computed(() => operationsMap[selectedOperation.value]?.hasRegex)
const needsMode = computed(() => operationsMap[selectedOperation.value]?.hasMode)
const needsCompressOptions = computed(() => operationsMap[selectedOperation.value]?.hasCompressOptions)
const selectedMode = ref('')

watch(selectedOperation, (val) => {
  selectedMode.value = operationsMap[val]?.hasMode ? operationsMap[val].modes[0].value : ''
})

// --- Shared Style Classes ---
const inputBaseClass = 'w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-800 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:focus:ring-indigo-900/30 outline-none transition-all'
const inputReadonlyClass = inputBaseClass + ' cursor-pointer'
const buttonBaseClass = 'px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1'
const buttonSecondaryClass = buttonBaseClass + ' bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 focus:ring-gray-400'

const fileName = (p) => p.split(/[\\/]/).pop()

// File Management logic moved to useFileManager

const selectFontFile = async () => {
  try { const path = await window.go.main.App.SelectFile(); if (path) { fontPath.value = path; toast?.success?.('已选择字体文件') } }
  catch (err) { console.error(err) }
}

const scrollLogToBottom = async () => {
  await nextTick()
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
    if (targets.font_families.length === 0 && targets.xhtml_files.length === 0) {
      toast?.warning?.('该 EPUB 无可加密的字体族或 XHTML 文件')
      outputLog.value += '⚠ 未找到可加密的字体族或 XHTML 文件\n'; loading.value = false; return
    }
    if (targets.font_families.length === 0) { toast?.warning?.('该 EPUB 无可加密的字体族'); outputLog.value += '⚠ 未找到可加密的字体族\n' }
    if (targets.xhtml_files.length === 0) { toast?.warning?.('该 EPUB 无可加密的 XHTML 文件'); outputLog.value += '⚠ 未找到可加密的 XHTML 文件\n' }
    selectedFontFamilies.value = [...targets.font_families]
    selectedXhtmlFiles.value = [...targets.xhtml_files]
    showFontTargetSelector.value = true
    outputLog.value += `✅ 扫描完成: 发现 ${targets.font_families.length} 个字体族, ${targets.xhtml_files.length} 个 XHTML 文件\n`
    toast?.success?.('扫描完成，请选择要加密的目标')
  } catch (err) { outputLog.value += `❌ 扫描失败: ${String(err)}\n`; toast?.error?.('扫描字体加密目标失败，请重新选择文件') }
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
    if (targets.length === 0) { toast?.warning?.('该 EPUB 无可用的章节结构'); outputLog.value += '⚠ 未找到可用的章节结构\n'; loading.value = false; return }
    selectedSplitPoints.value = []; showSplitTargetSelector.value = true
    outputLog.value += `✅ 扫描完成: 发现 ${targets.length} 个章节条目\n`
    toast?.success?.('扫描完成，请选择拆分点')
  } catch (err) { outputLog.value += `❌ 扫描失败: ${String(err)}\n`; toast?.error?.('扫描拆分目标失败，请重新选择文件') }
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
const reorderMergeFiles = (fromIdx, toIdx) => {
  const list = [...mergeFiles.value]
  const dragged = list.splice(fromIdx, 1)[0]
  list.splice(toIdx, 0, dragged)
  mergeFiles.value = list
}

const runTool = async () => {
  if (selectedOperation.value !== 'split_merge_epub' || selectedMode.value !== 'merge') {
    if (inputPaths.value.length === 0 || !selectedOperation.value) { toast?.warning?.('请先选择输入文件'); return }
  }
  
  if (selectedOperation.value === 'encrypt_font' && !showFontTargetSelector.value) { await scanFontTargets(); return }
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'split' && !showSplitTargetSelector.value) { await scanSplitTargets(); return }

  // view_opf
  if (selectedOperation.value === 'view_opf') {
    loading.value = true; opfContent.value = ''
    const filePath = inputPaths.value[0]; const name = fileName(filePath)
    outputLog.value = `▶ OPF 查看: ${name}\n${'─'.repeat(40)}\n`
    const args = ['--plugin', 'epub_tool', '--operation', 'view_opf', '--input-path', filePath]
    try {
      await runBackend(args, (result) => {
        if (result.stdout) {
          const opfMatch = result.stdout.match(/=== OPF Content ===([\s\S]*?)(?==== File List ===|$)/)
          if (opfMatch) opfContent.value = opfMatch[1].trim()
        }
        appendLog(`\n✅ OPF 查看完成\n`)
        toast?.success?.('OPF 查看完成')
      })
    } catch (err) { toast?.error?.('OPF 查看失败') }
    operationCompleted.value = true; return
  }

  // split_merge_epub: merge
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'merge') {
    if (mergeFiles.value.length < 2) { toast?.warning?.('请至少添加 2 个 EPUB 文件'); return }
    loading.value = true
    outputLog.value = `▶ 合并 EPUB（共 ${mergeFiles.value.length} 个文件）\n${'─'.repeat(40)}\n`
    mergeFiles.value.forEach((p, i) => { outputLog.value += `  ${i + 1}. ${fileName(p)}\n` })
    outputLog.value += `${'─'.repeat(40)}\n`
    const args = ['--plugin', 'epub_tool', '--operation', 'merge', '--input-paths', ...mergeFiles.value]
    if (outputPath.value) args.push('--output-path', outputPath.value)
    try {
      await runBackend(args, () => {
        appendLog(`\n✅ 合并完成\n`); toast?.success?.('EPUB 合并完成')
      })
    } catch (err) { toast?.error?.('EPUB 合并失败') }
    operationCompleted.value = true; return
  }

  // split_merge_epub: split
  if (selectedOperation.value === 'split_merge_epub' && selectedMode.value === 'split' && showSplitTargetSelector.value) {
    if (selectedSplitPoints.value.length === 0) { toast?.warning?.('请至少选择一个拆分点'); return }
    loading.value = true
    const filePath = inputPaths.value[0]; const name = fileName(filePath)
    const sortedPoints = [...selectedSplitPoints.value].sort((a, b) => a - b)
    const splitPointsStr = sortedPoints.join(',')
    outputLog.value = `▶ 拆分 EPUB: ${name}\n${'─'.repeat(40)}\n  拆分点: ${splitPointsStr}\n${'─'.repeat(40)}\n`
    const args = ['--plugin', 'epub_tool', '--operation', 'split', '--input-path', filePath, '--split-points', splitPointsStr]
    if (outputPath.value) args.push('--output-path', outputPath.value)
    try {
      await runBackend(args, () => {
        appendLog(`\n✅ 拆分完成\n`); toast?.success?.('EPUB 拆分完成')
      })
    } catch (err) { toast?.error?.('EPUB 拆分失败') }
    operationCompleted.value = true
    showSplitTargetSelector.value = false; splitTargets.value = []; selectedSplitPoints.value = []; return
  }

  // Batch execution
  loading.value = true
  const total = inputPaths.value.length; let successCount = 0; let failCount = 0
  outputLog.value = `▶ 批量执行: ${currentToolInfo.value.label}（共 ${total} 个文件）\n${'─'.repeat(40)}\n`
  toast?.info?.(`开始批量执行 ${total} 个文件...`, 2000)
  for (let i = 0; i < total; i++) {
    const filePath = inputPaths.value[i]; const name = fileName(filePath)
    outputLog.value += `\n[${i + 1}/${total}] ${name}\n`
    const args = ['--plugin', 'epub_tool', '--operation', selectedOperation.value, '--input-path', filePath]
    if (fontPath.value && needsFontPath.value) args.push('--font-path', fontPath.value)
    if (outputPath.value) args.push('--output-path', outputPath.value)
    if (regexPattern.value && needsRegex.value) args.push('--regex-pattern', regexPattern.value)
    if (selectedOperation.value === 'encrypt_font' && showFontTargetSelector.value) {
      if (selectedFontFamilies.value.length > 0) args.push('--target-font-families', ...selectedFontFamilies.value)
      if (selectedXhtmlFiles.value.length > 0) args.push('--target-xhtml-files', ...selectedXhtmlFiles.value)
    }
    
    if (selectedOperation.value === 'reformat_convert') {
      if (selectedMode.value === 'reformat') {
        args[opIndex + 1] = 'reformat'
      } else {
        args[opIndex + 1] = 'convert_version'
        args.push('--target-version', selectedMode.value)
      }
    } else if (['convert_chinese', 'convert_image_format'].includes(selectedOperation.value)) {
      if (opIndex > -1) args[opIndex + 1] = selectedMode.value
    }
    if (selectedOperation.value === 'img_compress') {
      args.push('--jpeg-quality', String(jpegQuality.value), '--webp-quality', String(webpQuality.value), '--png-to-jpg', pngToJpg.value ? 'true' : 'false')
    }
    try {
      await runBackend(args, () => {
        appendLog(`  ✅ 完成\n`); successCount++
      }, () => {
        failCount++
      })
    } catch (err) {
      failCount++
    }
  }
  appendLog(`\n${'─'.repeat(40)}\n📊 执行结果: 成功 ${successCount}，失败 ${failCount}，共 ${total} 个文件\n`)
  operationCompleted.value = true
  if (selectedOperation.value === 'encrypt_font') {
    showFontTargetSelector.value = false; fontTargets.value = { font_families: [], xhtml_files: [] }
    selectedFontFamilies.value = []; selectedXhtmlFiles.value = []
  }
  if (failCount === 0) toast?.success?.(`全部完成（${successCount} 个文件）`)
  else toast?.warning?.(`完成: ${successCount} 成功, ${failCount} 失败`)
}

const openLogFile = async () => {
  try { await window.go.main.App.OpenLogFile() } catch (err) { toast?.error?.('打开日志文件失败: ' + String(err)) }
}
const copyLog = async () => {
  try { await navigator.clipboard.writeText(outputLog.value); toast?.success?.('已复制日志到剪贴板') } catch { toast?.error?.('复制失败') }
}
const copyOpfContent = async () => {
  try { await navigator.clipboard.writeText(opfContent.value); toast?.success?.('已复制 OPF 内容到剪贴板') } catch { toast?.error?.('复制失败') }
}
</script>

<template>
  <div class="h-full flex flex-col space-y-6">
    <header>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ currentToolInfo.label }}</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ currentToolInfo.desc }}</p>
    </header>

    <div class="flex-1 overflow-y-auto space-y-5">

      <!-- Info Card -->
      <div v-if="currentToolInfo.details" class="bg-blue-50/80 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/30 rounded-xl p-4">
        <div class="flex items-start">
          <svg class="w-4 h-4 text-blue-400 dark:text-blue-300 mt-0.5 mr-2.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-sm text-blue-700 dark:text-blue-200 leading-relaxed">{{ currentToolInfo.details }}</p>
        </div>
      </div>

      <!-- File Selection -->
      <div v-show="!(selectedOperation === 'split_merge_epub' && selectedMode === 'merge')" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">文件设置</h2>
        <div>
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
            输入文件 <span class="text-red-400">*</span>
            <span v-if="inputPaths.length > 0" class="ml-2 text-xs text-indigo-500 font-normal">已选 {{ inputPaths.length }} 个文件</span>
          </label>
          <div class="space-y-2">
            <FileDropZone accept=".epub,application/epub+zip" :multiple="true" @drop="handleEpubDrop" @click="selectFile" :disabled="false">
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
              <button @click="clearFiles" class="text-xs text-gray-400 hover:text-red-500 transition-colors mt-1">清空全部文件</button>
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

      <!-- Font Path -->
      <div v-if="needsFontPath" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4 animate-slide-in">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">加密选项</h2>
        <div>
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">字体文件 <span class="text-gray-400 font-normal">（可选）</span></label>
          <div class="flex space-x-2">
            <input v-model="fontPath" type="text" :class="inputReadonlyClass" placeholder="选择字体文件用于混淆加密" readonly @click="selectFontFile">
            <button @click="selectFontFile" :class="buttonSecondaryClass">浏览</button>
          </div>
        </div>
      </div>

      <!-- Mode Selection -->
      <div v-if="needsMode" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4 animate-slide-in">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">转换模式</h2>
        <div class="flex space-x-3">
          <label v-for="mode in currentToolInfo.modes" :key="mode.value"
            :class="['flex-1 flex items-center justify-center px-4 py-2.5 rounded-lg border-2 cursor-pointer transition-all duration-150 text-sm font-medium',
              selectedMode === mode.value
                ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500']"
          >
            <input type="radio" v-model="selectedMode" :value="mode.value" class="sr-only">
            <span>{{ mode.label }}</span>
          </label>
        </div>
      </div>

      <!-- Regex Pattern -->
      <div v-if="needsRegex" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-4 animate-slide-in">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">正则选项</h2>
        <div>
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">正则表达式</label>
          <input v-model="regexPattern" type="text" :class="inputBaseClass + ' font-mono'"
            :placeholder="selectedOperation === 'footnote_conv' ? '默认: \\[(\\d+)\\] 或 #.+' : '默认: \\[(.*?)\\]'">
          <p class="text-xs text-gray-400 mt-2">留空将使用默认正则表达式。</p>
        </div>
      </div>

      <!-- Image Compress Options -->
      <div v-if="needsCompressOptions" class="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-5 animate-slide-in">
        <h2 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">压缩选项</h2>
        <div class="space-y-4">
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">JPEG 质量</label>
              <span class="text-sm font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded">{{ jpegQuality }}</span>
            </div>
            <input type="range" v-model.number="jpegQuality" min="10" max="100" step="5"
              class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600">
            <div class="flex justify-between text-xs text-gray-400 mt-1"><span>10 (最小)</span><span>100 (最高)</span></div>
          </div>
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">WebP 质量</label>
              <span class="text-sm font-mono text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded">{{ webpQuality }}</span>
            </div>
            <input type="range" v-model.number="webpQuality" min="10" max="100" step="5"
              class="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600">
            <div class="flex justify-between text-xs text-gray-400 mt-1"><span>10 (最小)</span><span>100 (最高)</span></div>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">PNG 转 JPG</label>
              <p class="text-xs text-gray-400 mt-0.5">无透明度的 PNG 转为 JPG 可大幅减小体积</p>
            </div>
            <button @click="pngToJpg = !pngToJpg"
              :class="['relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200',
                pngToJpg ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600']">
              <span :class="['inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 shadow-sm',
                pngToJpg ? 'translate-x-6' : 'translate-x-1']" />
            </button>
          </div>
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

      <!-- Merge EPUB File List -->
      <MergeFileList v-if="selectedOperation === 'split_merge_epub' && selectedMode === 'merge'"
        :files="mergeFiles"
        @drop="handleMergeFileDrop"
        @select="selectMergeFiles"
        @remove="removeMergeFile"
        @clear="clearMergeFiles"
        @reorder="reorderMergeFiles"
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

      <!-- Action Button -->
      <div class="flex items-center justify-between pt-2">
        <button v-if="outputLog" @click="clearLog" class="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">清除日志</button>
        <div v-else></div>
        <button @click="runTool"
          :disabled="loading || (selectedOperation === 'split_merge_epub' && selectedMode === 'merge' ? mergeFiles.length < 2 : selectedOperation === 'split_merge_epub' && selectedMode === 'split' && showSplitTargetSelector ? selectedSplitPoints.length === 0 : inputPaths.length === 0)"
          :class="['inline-flex items-center px-6 py-2.5 text-sm font-medium rounded-lg shadow-sm text-white transition-all duration-200',
            loading || (selectedOperation === 'split_merge_epub' && selectedMode === 'merge' ? mergeFiles.length < 2 : selectedOperation === 'split_merge_epub' && selectedMode === 'split' && showSplitTargetSelector ? selectedSplitPoints.length === 0 : inputPaths.length === 0)
              ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 hover:shadow-md active:scale-[0.98]']"
        >
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {{ loading ? '执行中...' : selectedOperation === 'split_merge_epub' && selectedMode === 'merge' ? `合并执行（${mergeFiles.length} 个文件）` : selectedOperation === 'split_merge_epub' && selectedMode === 'split' ? (showSplitTargetSelector ? `确认拆分（${selectedSplitPoints.length} 个拆分点）` : '扫描章节结构') : inputPaths.length > 1 ? `批量执行（${inputPaths.length} 个文件）` : '开始执行' }}
        </button>
      </div>

      <OutputLog :log="outputLog" :showOpenLog="operationCompleted" :opfContent="opfContent"
        @copy="copyLog" @copyOpf="copyOpfContent" @openLog="openLogFile" />
    </div>
  </div>
</template>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.25s ease-out;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
