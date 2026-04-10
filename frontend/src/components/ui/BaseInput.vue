<script setup>
/**
 * BaseInput - 统一风格的输入框组件
 * 支持文本、密码、邮箱等类型
 */

import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  monospace: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md', // sm | md | lg
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue', 'focus', 'blur'])

const sizeClasses = {
  sm: 'py-1.5 px-2.5 text-xs',
  md: 'py-2.5 px-3 text-sm',
  lg: 'py-3 px-4 text-base'
}

const inputClasses = computed(() => [
  'w-full rounded-lg border',
  'text-gray-700 dark:text-gray-200',
  'bg-gray-50 dark:bg-gray-900/50',
  'placeholder:text-gray-400 dark:placeholder:text-gray-500',
  'focus:bg-white dark:focus:bg-gray-800',
  'focus:border-indigo-400',
  'focus:ring-2 focus:ring-indigo-100 dark:focus:ring-indigo-900/30',
  'outline-none transition-all duration-200',
  'dark:border-gray-600',
  sizeClasses[props.size],
  {
    'border-gray-200': !props.error,
    'border-red-400 dark:border-red-500': props.error,
    'border-gray-300 dark:border-gray-500': props.disabled,
    'font-mono': props.monospace,
    'cursor-pointer': props.readonly && !props.disabled,
    'cursor-not-allowed opacity-50': props.disabled,
  }
])

const handleInput = (e) => {
  emit('update:modelValue', e.target.value)
}

const handleFocus = (e) => {
  emit('focus', e)
}

const handleBlur = (e) => {
  emit('blur', e)
}
</script>

<template>
  <div class="space-y-1.5">
    <!-- Label -->
    <label v-if="label" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
      {{ label }}
      <span v-if="required" class="text-red-400 ml-0.5">*</span>
    </label>

    <!-- Input -->
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :class="inputClasses"
      @input="handleInput"
      @focus="handleFocus"
      @blur="handleBlur"
    />

    <!-- Error Message -->
    <p v-if="error" class="text-xs text-red-500 dark:text-red-400">
      {{ error }}
    </p>

    <!-- Hint -->
    <p v-else-if="hint" class="text-xs text-gray-400 dark:text-gray-500">
      {{ hint }}
    </p>
  </div>
</template>