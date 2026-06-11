<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold">同步配置</h1>
      <button @click="$router.push('/profiles/new')" class="btn-primary">+ 新建配置</button>
    </div>
    
    <div v-if="items.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="p in items" :key="p.id">
        <div class="card">
          <!-- 点击卡本身进入编辑 -->
          <div class="cursor-pointer" @click="$router.push('/profiles/'+p.id)">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-medium">{{ p.name }}</h3>
              <span class="text-xs px-2 py-0.5 rounded-full"
                :class="p.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'">
                {{ p.enabled ? '已启用' : '已禁用' }}
              </span>
            </div>
            <div class="text-sm text-gray-500 space-y-1">
              <p>匹配方式: {{ { label: '按卷标', always: '自动', manual: '手动' }[p.match_type] || p.match_type }}</p>
              <p>目标: {{ p.destination }}</p>
              <p>归档: {{ { date: '按日期', original: '原结构', custom: '自定义' }[p.sync_mode] || p.sync_mode }}</p>
            </div>
          </div>
          <!-- 手动同步按钮 -->
          <div class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <button @click.stop="showSyncDialog(p)" class="btn-primary text-sm w-full">🔄 手动同步</button>
            
            <!-- 选择储存卡 -->
            <div v-if="syncProfileId === p.id" class="mt-2 space-y-2">
              <div v-if="cards.length" class="space-y-1">
                <label class="text-xs text-gray-500">选择要同步的储存卡：</label>
                <select v-model="selectedCardPath" class="input text-sm">
                  <option value="" disabled>请选择储存卡</option>
                  <option v-for="c in cards" :key="c.path" :value="c.path">
                    {{ c.label }} ({{ c.path }})
                  </option>
                </select>
              </div>
              <p v-else class="text-xs text-orange-500">没有检测到储存卡，请先插入 USB 读卡器</p>
              <div class="flex gap-2">
                <button @click="triggerSync(p)" class="btn-primary text-xs" 
                  :disabled="!selectedCardPath || syncing">开始同步</button>
                <button @click="syncProfileId = null" class="btn-secondary text-xs">取消</button>
              </div>
              <p v-if="syncMsg" class="text-xs" :class="syncOk ? 'text-green-600' : 'text-red-600'">{{ syncMsg }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <EmptyState v-else title="还没有同步配置" message="新建一个配置来开始自动同步照片"
      action="新建配置" @action="$router.push('/profiles/new')" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { profilesApi } from '../api/profiles'
import { cardsApi } from '../api/cards'
import { syncApi } from '../api/sync'
import EmptyState from '../components/EmptyState.vue'

const items = ref([])
const cards = ref([])
const syncProfileId = ref(null)
const selectedCardPath = ref('')
const syncing = ref(false)
const syncMsg = ref('')
const syncOk = ref(false)

onMounted(async () => {
  try {
    const d = await profilesApi.list({ page: 1, page_size: 100 })
    items.value = d.items
  } catch (e) {}
  try {
    cards.value = await cardsApi.list()
  } catch (e) {}
})

const showSyncDialog = profile => {
  syncProfileId.value = profile.id
  selectedCardPath.value = ''
  syncMsg.value = ''
  // Refresh cards list
  cardsApi.list().then(d => cards.value = d).catch(() => {})
}

const triggerSync = async profile => {
  if (!selectedCardPath.value || !syncProfileId.value) return
  syncing.value = true
  syncMsg.value = ''
  try {
    await syncApi.trigger(syncProfileId.value, selectedCardPath.value)
    syncMsg.value = '✅ 已加入同步队列！可到仪表盘查看进度'
    syncOk.value = true
  } catch (e) {
    syncMsg.value = '❌ 同步失败: ' + (e.message || e)
    syncOk.value = false
  } finally {
    syncing.value = false
  }
}
</script>
