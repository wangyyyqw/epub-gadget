/**
 * 动画和过渡效果 composable
 */

import { ref, onMounted, onUnmounted } from 'vue'

export const useAnimation = () => {
  // ============ 预定义动画类 ============
  const animations = {
    // 淡入
    fadeIn: 'animate-fade-in',
    // 淡入上移
    fadeInUp: 'animate-fade-in-up',
    // 缩放淡入
    scaleIn: 'animate-scale-in',
    // 滑入
    slideInLeft: 'animate-slide-in-left',
    slideInRight: 'animate-slide-in-right',
    // 脉冲
    pulse: 'animate-pulse',
    // 旋转
    spin: 'animate-spin',
    // 弹跳
    bounce: 'animate-bounce',
  }

  // ============ 过渡类 ============
  const transitions = {
    default: 'transition-all duration-200 ease-out',
    fast: 'transition-all duration-150 ease-out',
    slow: 'transition-all duration-300 ease-out',
    color: 'transition-colors duration-200',
    transform: 'transition-transform duration-200',
    opacity: 'transition-opacity duration-200',
  }

  // ============ 悬停效果 ============
  const hoverEffects = {
    scale: 'hover:scale-105',
    lift: 'hover:-translate-y-0.5',
    liftMore: 'hover:-translate-y-1',
    glow: 'hover:shadow-lg hover:shadow-indigo-500/10',
    brighten: 'hover:brightness-110',
  }

  return {
    animations,
    transitions,
    hoverEffects,
  }
}

/**
 * 交错动画 hook
 * 用于列表项的依次显示动画
 */
export const useStaggerAnimation = (itemCount, baseDelay = 100) => {
  const visibleItems = ref([])

  const animateItems = () => {
    visibleItems.value = []
    for (let i = 0; i < itemCount; i++) {
      setTimeout(() => {
        visibleItems.value.push(i)
      }, i * baseDelay)
    }
  }

  return {
    visibleItems,
    animateItems,
  }
}

/**
 * 打字机效果
 */
export const useTypewriter = (text, speed = 50) => {
  const displayedText = ref('')
  const isTyping = ref(false)
  let timeoutId = null

  const start = () => {
    isTyping.value = true
    displayedText.value = ''
    let index = 0

    const type = () => {
      if (index < text.length) {
        displayedText.value += text[index]
        index++
        timeoutId = setTimeout(type, speed)
      } else {
        isTyping.value = false
      }
    }

    type()
  }

  const stop = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    isTyping.value = false
  }

  const reset = () => {
    stop()
    displayedText.value = ''
  }

  onUnmounted(stop)

  return {
    displayedText,
    isTyping,
    start,
    stop,
    reset,
  }
}

/**
 * 滚动动画 hook
 * 元素进入视口时触发动画
 */
export const useIntersectionAnimation = (threshold = 0.1) => {
  const elementRef = ref(null)
  const isVisible = ref(false)

  onMounted(() => {
    if (!elementRef.value) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            isVisible.value = true
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold }
    )

    observer.observe(elementRef.value)

    onUnmounted(() => {
      observer.disconnect()
    })
  })

  return {
    elementRef,
    isVisible,
  }
}

/**
 * 动画类名工具函数
 */
export const cn = (...classes) => classes.filter(Boolean).join(' ')