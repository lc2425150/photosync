<template>
  <div>
    <h1 class="text-xl font-bold mb-4">储存卡浏览器</h1>
    
    <div v-if="cards.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="c in cards" :key="c.path" class="card">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-medium">{{ c.label }}</h3>
          <span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">已连接</span>
        </div>
        <p class="text-xs text-gray-500 font-mono mb-2">{{ c.path }}</p>
        <p class="text-sm text-gray-600">容量: {{ c.total_space ? (c.total_space/1073741824).toFixed(1)+'GB' : '未知' }}</p>
        <p v-if="c.matched_profile" class="text-sm text-blue-600">匹配配置: {{ c.matched_profile }}</p>
        
        <div class="flex gap-2 mt-3">
          <button @click="preview(c.path)" class="btn-secondary text-sm">预览文件</button>
          <!-- 手动同步按钮 -->
          <button @click="showSyncDialog(c)" class="btn-primary text-sm">手动同步</button>
        </div>
        
        <!-- 同步配置选择器 -->
        <div v-if="syncCard === c.path" class="mt-3 p-2 border rounded bg-gray-50 dark:bg-gray-700/50 space-y-2">
          <select v-model="selectedProfileId" class="input text-sm">
            <option value="" disabled>选择同步配置</option>
            <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <div class="flex gap-2">
            <button @click="startSync(c)" class="btn-primary text-xs" :disabled="!selectedProfileId || syncing">开始同步</button>
            <button @click="syncCard = null" class="btn-secondary text-xs">取消</button>
          </div>
          <p v-if="syncMsg" class="text-xs" :class="syncOk?'text-green-600':'text-red-600'">{{ syncMsg }}</p>
        </div>
      </div>
    </div>
    
    <EmptyState v-else title="未检测到储存卡" message="插入相机储存卡到 NAS 的 USB 接口后会自动显示" action="刷新" @action="load"/>
    
    <!-- 同步进度 -->
    <div v-if="progress.running" class="mt-6 card">
      <h3 class="font-medium mb-2">同步进度</h3>
      <SyncProgress :progress="progress" />
    </div>

    <div v-if="previewFiles.length" class="mt-6">
      <h2 class="font-medium mb-3">文件预览</h2>
      <div class="card">
        <div v-for="f in previewFiles" :key="f.path" class="flex justify-between text-sm p-1.5 even:bg-gray-50 rounded">
          <span>{{ f.name }}</span>
          <span class="text-gray-500"> {{ (f.size/1024).toFixed(0) }}KB</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { cardsApi } from '../api/cards'
import { profilesApi } from '../api/profiles'
import { syncApi } from '../api/sync'
import EmptyState from '../components/EmptyState.vue'
import SyncProgress from '../components/SyncProgress.vue'

const cards = ref([])
const previewFiles = ref([])
const profiles = ref([])

// Sync dialog state
const syncCard = ref(null)
const selectedProfileId = ref('')
const syncing = ref(false)
const syncMsg = ref('')
const syncOk = ref(false)
const progress = ref({ running: false })

const load = async () => {
  try {
    cards.value = await cardsApi.list()
  } catch (e) {}
  try {
    const d = await profilesApi.list({ page: 1, page_size: 100 })
    profiles.value = d.items
  } catch (e) {}
}
onMounted(load)

const preview = async path => {
  try {
    previewFiles.value = await cardsApi.preview(path, 'all')
  } catch (e) {
    alert(e.message)
  }
}

const showSyncDialog = card => {
  syncCard.value = card.path
  selectedProfileId.value = ''
  syncMsg.value = ''
}

const startSync = async card => {
  if (!selectedProfileId.value) return
  syncing.value = true
  syncMsg.value = ''
  try {
    await syncApi.trigger(selectedProfileId.value, card.path)
    syncMsg.value = '已加入同步队列！'
    syncOk.value = true
    syncCard.value = null
  } catch (e) {
    syncMsg.value = '同步失败: ' + (e.message || e)
    syncOk.value = false
  } finally {
    syncing.value = false
  }
}

// Poll sync status
let timer = null
onMounted(() => {
  timer = setInterval(async () => {
    try {
      progress.value = await syncApi.status()
    } catch (e) {}
  }, 2000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
