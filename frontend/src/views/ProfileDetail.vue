<template>
  <div class="max-w-2xl">
    <h1 class="text-xl font-bold mb-4">{{ isNew ? '新建配置' : '编辑配置' }}</h1>

    <!-- Path mapping hint -->
    <div v-if="mapping" class="text-xs text-gray-500 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
      <p><strong>📁 提示：</strong>请直接填入 NAS 上的完整文件夹路径。</p>
      <p class="mt-1">从 NAS 文件管理器复制完整路径粘贴到这里，例如：<code class="font-mono bg-blue-100 dark:bg-blue-800 px-1 rounded">{{ mapping.host_base }}/相机备份</code></p>
      <p class="mt-1 text-orange-500">⚠ 不要填容器内路径（如 /photos/xxx），填 NAS 实际路径即可</p>
    </div>

    <div class="card space-y-4">
      <div>
        <label class="label">配置名称</label>
        <input v-model="form.name" class="input" placeholder="例如：索尼 A7M4" />
      </div>

      <div>
        <label class="label">匹配方式</label>
        <select v-model="form.match_type" class="input">
          <option value="manual">仅手动同步</option>
          <option value="always">插卡即同步</option>
          <option value="label">按卷标匹配</option>
        </select>
      </div>
      <div v-if="form.match_type === 'label'">
        <label class="label">卷标名称</label>
        <input v-model="form.match_value" class="input" placeholder="如 SONY-A7M4" />
      </div>

      <div>
        <label class="label">同步模式</label>
        <select v-model="form.sync_mode" class="input">
          <option value="date">按日期归档 (YYYY/MM/DD)</option>
          <option value="original">保留原始目录结构</option>
          <option value="custom">自定义模板</option>
        </select>
      </div>
      <div v-if="form.sync_mode === 'custom'">
        <label class="label">自定义路径模板</label>
        <input v-model="form.custom_template" class="input" placeholder="{Y}/{m}/{d}/{filename}" />
        <p class="text-xs text-gray-500 mt-1">可用变量: {filename} {Y} {m} {d} {H} {M} {S} {model}</p>
      </div>

      <div>
        <label class="label">目标目录（NAS 路径）</label>
        <input v-model="form.destination" class="input font-mono text-sm" :placeholder="mapping ? mapping.host_base + '/相机名' : '/volume2/照片/相机名'" />
        <p class="text-xs text-orange-500 mt-1">⚠ 请粘贴 NAS 文件管理器中复制的完整路径</p>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="label">冲突策略</label>
          <select v-model="form.conflict_strategy" class="input">
            <option value="skip">跳过</option>
            <option value="overwrite">覆盖</option>
            <option value="rename">自动重命名</option>
            <option value="keep_both">保留两者</option>
          </select>
        </div>
        <div>
          <label class="label">复制模式</label>
          <select v-model="form.copy_mode" class="input">
            <option value="copy">复制（卡上保留）</option>
            <option value="move">剪切（卡上删除）</option>
          </select>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="form.auto_sync" class="rounded" />自动同步
        </label>
        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="form.checksum_verify" class="rounded" />校验完整性
        </label>
      </div>

      <div class="flex gap-2 pt-2">
        <button @click="save" class="btn-primary">{{ isNew ? '创建' : '保存' }}</button>
        <button v-if="!isNew" @click="remove" class="btn-danger">删除</button>
        <button @click="$router.back()" class="btn-secondary">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { profilesApi } from '../api/profiles'
import { settingsApi } from '../api/settings'

const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.path === '/profiles/new')
const mapping = ref(null)

const form = ref({
  name: '',
  match_type: 'manual',
  match_value: '',
  sync_mode: 'date',
  custom_template: '',
  destination: '/volume2/照片',
  conflict_strategy: 'skip',
  copy_mode: 'copy',
  auto_sync: false,
  checksum_verify: true,
})

onMounted(async () => {
  // Fetch path mapping info
  try {
    const res = await fetch('/api/v1/system/path-mapping')
    mapping.value = await res.json()
    // Set default destination based on mapping
    form.value.destination = mapping.value.host_base
  } catch (e) {}

  // If editing, load existing profile
  if (!isNew.value) {
    try {
      const d = await profilesApi.get(route.params.id)
      form.value = { ...d }
    } catch (e) {
      alert(e.message)
    }
  }
})

const save = async () => {
  try {
    if (isNew.value) {
      await profilesApi.create(form.value)
    } else {
      await profilesApi.update(route.params.id, form.value)
    }
    router.push('/profiles')
  } catch (e) {
    alert(e.message)
  }
}

const remove = async () => {
  if (!confirm('确定删除此配置？')) return
  try {
    await profilesApi.delete(route.params.id)
    router.push('/profiles')
  } catch (e) {
    alert(e.message)
  }
}
</script>
