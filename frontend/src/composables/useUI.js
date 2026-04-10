/**
 * UI 样式常量 - 统一整个项目的视觉规范
 * 所有组件应使用此处定义的常量，确保视觉一致性
 */

export const useUI = () => {
  // ============ 颜色系统 ============
  const colors = {
    // 主色调 - Indigo
    primary: {
      50: 'bg-indigo-50',
      100: 'bg-indigo-100',
      500: 'bg-indigo-500',
      600: 'bg-indigo-600',
      700: 'bg-indigo-700',
      text: 'text-indigo-600 dark:text-indigo-400',
      textDark: 'text-indigo-700 dark:text-indigo-300',
      border: 'border-indigo-200 dark:border-indigo-800',
      hover: 'hover:bg-indigo-50 dark:hover:bg-indigo-900/20',
    },
    // 工具分组颜色
    group: {
      emerald: { bg: 'bg-emerald-500', light: 'text-emerald-500 dark:text-emerald-400', hover: 'hover:bg-emerald-50 dark:hover:bg-emerald-900/20' },
      blue: { bg: 'bg-blue-500', light: 'text-blue-500 dark:text-blue-400', hover: 'hover:bg-blue-50 dark:hover:bg-blue-900/20' },
      amber: { bg: 'bg-amber-500', light: 'text-amber-500 dark:text-amber-400', hover: 'hover:bg-amber-50 dark:hover:bg-amber-900/20' },
      rose: { bg: 'bg-rose-500', light: 'text-rose-500 dark:text-rose-400', hover: 'hover:bg-rose-50 dark:hover:bg-rose-900/20' },
      teal: { bg: 'bg-teal-500', light: 'text-teal-500 dark:text-teal-400', hover: 'hover:bg-teal-50 dark:hover:bg-teal-900/20' },
      cyan: { bg: 'bg-cyan-500', light: 'text-cyan-500 dark:text-cyan-400', hover: 'hover:bg-cyan-50 dark:hover:bg-cyan-900/20' },
      violet: { bg: 'bg-violet-500', light: 'text-violet-500 dark:text-violet-400', hover: 'hover:bg-violet-50 dark:hover:bg-violet-900/20' },
    },
    // 状态颜色
    status: {
      success: 'text-green-500 dark:text-green-400',
      warning: 'text-amber-500 dark:text-amber-400',
      error: 'text-red-500 dark:text-red-400',
      info: 'text-blue-500 dark:text-blue-400',
    }
  }

  // ============ 阴影系统 ============
  const shadows = {
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
    card: 'shadow-sm',
    cardHover: 'shadow-lg',
  }

  // ============ 圆角系统 ============
  const radii = {
    none: 'rounded-none',
    sm: 'rounded',
    md: 'rounded-lg',
    lg: 'rounded-xl',
    xl: 'rounded-2xl',
    full: 'rounded-full',
    card: 'rounded-xl',
    button: 'rounded-lg',
    input: 'rounded-lg',
  }

  // ============ 间距系统 ============
  const spacing = {
    section: 'space-y-6',
    card: 'p-5',
    input: 'p-2.5',
  }

  // ============ 输入框样式 ============
  const inputBaseClass = 'w-full rounded-lg border border-gray-200 dark:border-gray-600 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 bg-gray-50 dark:bg-gray-900/50 focus:bg-white dark:focus:bg-gray-800 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 dark:focus:ring-indigo-900/30 outline-none transition-all duration-200'
  const inputReadonlyClass = inputBaseClass + ' cursor-pointer'
  const inputDisabledClass = inputBaseClass + ' opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-800'

  // ============ 按钮样式 ============
  const buttonBaseClass = 'px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1'
  
  const buttons = {
    primary: buttonBaseClass + ' bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white shadow-sm hover:shadow active:scale-[0.98] focus:ring-indigo-500',
    secondary: buttonBaseClass + ' bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 focus:ring-gray-400',
    danger: buttonBaseClass + ' bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/50 focus:ring-red-400',
    ghost: buttonBaseClass + ' bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 focus:ring-gray-400',
    // 带颜色的按钮
    amber: buttonBaseClass + ' bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-800/30 focus:ring-amber-400',
  }

  // 禁用状态
  const buttonDisabledClass = 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed opacity-70'

  // ============ 卡片样式 ============
  const cardClass = 'bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-all duration-200'
  const cardHoverClass = 'hover:shadow-md hover:border-gray-200 dark:hover:border-gray-600'

  // ============ 分组标题样式 ============
  const sectionHeaderClass = 'text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider'

  // ============ 动画配置 ============
  const animations = {
    // 淡入上移动画
    fadeInUp: {
      duration: 'duration-300',
      easing: 'ease-out',
      keyframes: {
        from: 'opacity-0 translate-y-2',
        to: 'opacity-100 translate-y-0',
      }
    },
    // 缩放淡入
    scaleIn: {
      duration: 'duration-200',
      easing: 'ease-out',
    },
    // 悬停效果
    hover: {
      scale: 'hover:scale-105',
      lift: 'hover:-translate-y-0.5',
      glow: 'hover:shadow-lg',
    }
  }

  // ============ 过渡配置 ============
  const transitions = {
    default: 'transition-all duration-200',
    fast: 'transition-all duration-150',
    slow: 'transition-all duration-300',
    color: 'transition-colors duration-200',
    transform: 'transition-transform duration-200',
  }

  // ============ 表单标签样式 ============
  const labelClass = 'text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5 block'
  const labelRequiredClass = labelClass + ' after:content-["*"] after:text-red-400 after:ml-0.5'

  // ============ 占位符样式 ============
  const placeholderClass = 'placeholder:text-gray-400 dark:placeholder:text-gray-500'

  return {
    colors,
    shadows,
    radii,
    spacing,
    inputBaseClass,
    inputReadonlyClass,
    inputDisabledClass,
    buttonBaseClass,
    buttons,
    buttonDisabledClass,
    cardClass,
    cardHoverClass,
    sectionHeaderClass,
    animations,
    transitions,
    labelClass,
    labelRequiredClass,
    placeholderClass,
  }
}

// ============ 工具函数 ============

/**
 * 生成动态 class
 */
export const clsx = (...classes) => classes.filter(Boolean).join(' ')

/**
 * 生成条件类
 */
export const cn = (...args) => {
  const classes = []
  for (const arg of args) {
    if (typeof arg === 'string') {
      classes.push(arg)
    } else if (typeof arg === 'object' && arg !== null) {
      for (const [key, value] of Object.entries(arg)) {
        if (value) classes.push(key)
      }
    }
  }
  return classes.join(' ')
}
