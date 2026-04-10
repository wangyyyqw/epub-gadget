<script setup>
/**
 * BaseSelect - 统一风格的下拉选择组件
 */

import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择'
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
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const sizeClasses = {
  sm: 'py-1.5 px-2.5 text-xs',
  md: 'py-2.5 px-3 text-sm',
  lg: 'py-3 px-4 text-base'
}

const selectClasses = computed(() => [
  'w-full rounded-lg border',
  'text-gray-700 dark:text-gray-200',
  'bg-gray-50 dark:bg-gray-900/50',
  'focus:bg-white dark:focus:bg-gray-800',
  'focus:border-indigo-400',
  'focus:ring-2 focus:ring-indigo-100 dark:focus:ring-indigo-900/30',
  'outline-none transition-all duration-200',
  'dark:border-gray-600',
  'cursor-pointer',
  sizeClasses[props.size],
  {
    'border-gray-200': !props.error,
    'border-red-400 dark:border-red-500': props.error,
    'cursor-not-allowed opacity-50': props.disabled,
  }
])

const handleChange = (e) => {
  emit('update:modelValue', e.target.value)
  emit('change', e.target.value)
}
</script>

<template>
  <div class="space-y-1.5">
    <!-- Label -->
    <label v-if="label" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
      {{ label }}
      <span v-if="required" class="text-red-400 ml-0.5">*</span>
    </label>

    <!-- Select -->
    <select
      :value="modelValue"
      :disabled="disabled"
      :class="selectClasses"
      @change="handleChange"
    >
      <option value="" disabled>{{ placeholder }}</option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>

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