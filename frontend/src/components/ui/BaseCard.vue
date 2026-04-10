<script setup>
/**
 * BaseCard - 统一风格的卡片组件
 * 提供一致的背景、边框、阴影和悬停效果
 */

import { computed } from 'vue'

const props = defineProps({
  // 卡片变体
  variant: {
    type: String,
    default: 'default', // default | elevated | bordered | ghost
  },
  // 是否可点击
  clickable: {
    type: Boolean,
    default: false
  },
  // 是否悬浮效果
  hoverable: {
    type: Boolean,
    default: false
  },
  // 是否有渐变背景
  gradient: {
    type: Boolean,
    default: false
  },
  // 渐变方向
  gradientDirection: {
    type: String,
    default: 'to-br', // to-br | to-r | to-b | to-l
  },
  // 内边距
  padding: {
    type: String,
    default: 'md', // none | sm | md | lg
  },
  // 尺寸
  size: {
    type: String,
    default: 'md', // sm | md | lg
  }
})

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-6'
}

const sizeClasses = {
  sm: 'rounded-lg',
  md: 'rounded-xl',
  lg: 'rounded-2xl'
}

const baseClasses = computed(() => [
  sizeClasses[props.size],
  paddingClasses[props.padding],
  'transition-all duration-200 ease-out'
])

const variantClasses = computed(() => {
  if (props.gradient) {
    return [
      'from-white dark:from-gray-800 to-transparent border border-gray-100 dark:border-gray-700/50',
      'backdrop-blur-sm'
    ]
  }
  
  switch (props.variant) {
    case 'elevated':
      return ['bg-white dark:bg-gray-800 shadow-md']
    case 'bordered':
      return ['bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700']
    case 'ghost':
      return ['bg-transparent hover:bg-gray-50 dark:hover:bg-gray-800/50']
    default:
      return [
        'bg-white dark:bg-gray-800',
        'shadow-sm',
        'border border-gray-100 dark:border-gray-700/50'
      ]
  }
})

const interactiveClasses = computed(() => {
  if (!props.clickable && !props.hoverable) return []
  return [
    'cursor-pointer',
    'hover:shadow-md hover:border-gray-200 dark:hover:border-gray-600',
    'active:scale-[0.99]'
  ]
})

const emit = defineEmits(['click'])

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<template>
  <div
    :class="[...baseClasses, ...variantClasses, ...interactiveClasses]"
    @click="handleClick"
  >
    <slot />
  </div>
</template>