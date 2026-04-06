import { ref } from 'vue'

export function useEpubProcess(toast) {
  const loading = ref(false)
  const outputLog = ref('')
  
  // Appends text to log, scrolling the view is left to components or standard UI ref
  const appendLog = (text) => {
    outputLog.value += text + '\n'
  }

  const clearLog = () => {
    outputLog.value = ''
  }

  // The wrapper automatically handles standard spinning and event streams
  const runBackend = async (args, onSuccess, onFail) => {
    loading.value = true
    
    // Register event listener if supported
    let eventName = 'backend_log'
    let unlistener = null
    if (window.runtime && window.runtime.EventsOn) {
      // Wails EventsOn returns a cancellation function 
      unlistener = window.runtime.EventsOn(eventName, (data) => {
        if (data && data.text !== undefined) {
          appendLog(data.text)
        }
      })
    }

    try {
      const result = await window.go.main.App.RunBackend(args)
      
      // If we didn't have stream, we must append the whole block at the end fallback
      if (!unlistener) {
        if (result.stderr) appendLog(result.stderr)
        if (result.stdout) appendLog(result.stdout)
      }
      
      if (onSuccess) onSuccess(result)
    } catch (err) {
      const errStr = String(err)
      
      // Handling standardized ZHANGYUE_DRM flag inside error mapping
      if (errStr.includes('ZHANGYUE_DRM') || errStr.includes('zhangyue_drm')) {
        appendLog(`⚠️ 检测到掌阅(ZhangYue)DRM加密书籍，因版权保护原因不支持解密处理`)
        if (toast?.warning) toast.warning('检测到掌阅DRM加密，不支持解密')
      } else {
        appendLog(`❌ 执行失败: ${errStr}`)
      }
      if (onFail) onFail(errStr)
    } finally {
      loading.value = false
      if (unlistener) {
        window.runtime.EventsOff(eventName)
      }
    }
  }

  return {
    loading,
    outputLog,
    appendLog,
    clearLog,
    runBackend
  }
}
