<template>
  <div class="card">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-medium">同步进度</h3>
      <button v-if="running" @click="$emit('cancel')" class="text-xs px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
        停止同步
      </button>
    </div>
    <div v-if="running">
      <div class="flex justify-between text-sm mb-1">
        <span>{{ current }}/{{ total }} 个文件</span>
        <span>{{ speed }} MB/s</span>
      </div>
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div class="bg-blue-600 h-3 rounded-full transition-all duration-300" :style="{width:percent+'%'}"></div>
      </div>
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>{{ currentFile||'准备中...' }}</span>
        <span v-if="eta">剩余 {{ eta }}</span>
      </div>
    </div>
    <div v-else class="text-sm text-gray-500">当前没有同步任务</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  running: Boolean,
  current: Number,
  total: Number,
  speed: [Number, String],
  currentFile: String,
  eta: String,
})

defineEmits(['cancel'])

const percent = computed(() => props.total > 0 ? Math.round(props.current / props.total * 100) : 0)
</script>
