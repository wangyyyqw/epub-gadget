import { ref } from 'vue'

export function useFileManager(toast, allowedExtensions = ['.epub']) {
  const inputPaths = ref([])
  const outputPath = ref('')

  const handleFileDrop = (pathsOrPath) => {
    if (!pathsOrPath) return
    const paths = Array.isArray(pathsOrPath) ? pathsOrPath : [pathsOrPath]
    const validPaths = paths.map(p => typeof p === 'string' ? p : p.path).filter(Boolean)
    const filteredPaths = validPaths.filter(p => {
      const pstr = p.toLowerCase()
      return allowedExtensions.some(ext => pstr.endsWith(ext))
    })
    
    if (filteredPaths.length === 0) {
      if (toast?.error) toast.error(`请选择支持的文件格式 (${allowedExtensions.join(', ')})`)
      return
    }
    
    const existing = new Set(inputPaths.value)
    const newPaths = filteredPaths.filter(p => !existing.has(p))
    
    if (newPaths.length > 0) {
      inputPaths.value = [...inputPaths.value, ...newPaths]
      if (toast?.success) toast.success(`已添加 ${newPaths.length} 个文件`)
    }
  }

  const selectFile = async () => {
    try {
      const paths = await window.go.main.App.SelectFiles({})
      if (paths && paths.length > 0) handleFileDrop(paths)
    } catch (err) {
      console.error(err)
    }
  }

  const removeFile = (index) => {
    inputPaths.value.splice(index, 1)
  }

  const clearFiles = () => {
    inputPaths.value = []
  }

  const selectOutputPath = async () => {
    try {
      const path = await window.go.main.App.SelectDirectory()
      if (path) {
        outputPath.value = path
        if (toast?.success) toast.success('已设置输出目录')
      }
    } catch (err) {
      console.error(err)
    }
  }

  return {
    inputPaths,
    outputPath,
    handleFileDrop,
    selectFile,
    removeFile,
    clearFiles,
    selectOutputPath
  }
}
