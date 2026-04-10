<script setup>
/**
 * BaseButton - 统一风格的按钮组件
 * 支持多种变体和状态
 */

import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary', // primary | secondary | danger | ghost | amber
    validator: (v) => ['primary', 'secondary', 'danger', 'ghost', 'amber'].includes(v)
  },
  size: {
    type: String,
    default: 'md', // sm | md | lg
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  block: {
    type: Boolean,
    default: false
  },
  icon: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs gap-1.5',
  md: 'px-4 py-2.5 text-sm gap-2',
  lg: 'px-6 py-3 text-base gap-2.5'
}

const variantClasses = {
  primary: 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white shadow-sm hover:shadow focus:ring-indigo-500 dark:focus:ring-indigo-400',
  secondary: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 focus:ring-gray-400',
  danger: 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/50 focus:ring-red-400',
  ghost: 'bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 focus:ring-gray-400',
  amber: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-800/30 focus:ring-amber-400'
}

const buttonClasses = computed(() => [
  'inline-flex items-center justify-center font-medium rounded-lg',
  'transition-all duration-200 ease-out',
  'focus:outline-none focus:ring-2 focus:ring-offset-1',
  'active:scale-[0.98]',
  sizeClasses[props.size],
  variantClasses[props.variant],
  {
    'w-full': props.block,
    'opacity-50 cursor-not-allowed': props.disabled || props.loading,
    'px-2 py-2': props.icon && props.size === 'md',
    'px-1.5 py-1.5': props.icon && props.size === 'sm',
  }
])

const handleClick = (e) => {
  if (!props.disabled && !props.loading) {
    emit('click', e)
  }
}
</script>

<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <!-- Loading Spinner -->
    <svg
      v-if="loading"
      class="animate-spin"
      :class="{ 'h-3.5 w-3.5': size === 'sm', 'h-4 w-4': size === 'md', 'h-5 w-5': size === 'lg' }"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
    <slot />
  </button>
</template>
