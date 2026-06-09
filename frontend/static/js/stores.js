const { defineStore } = Pinia;
const { ref, computed } = Vue;

// System Store
window.useSystemStore = defineStore('system', () => {
  const health = ref({ status: 'loading', db: { connected: false }, worker: { alive: false } });
  const isInitialized = ref(false);
  async function checkHealth() {
    try {
      health.value = await api.get('/system/health');
      if (health.value.db?.connected) isInitialized.value = true;
    } catch (e) { health.value = { status: 'error', db: { connected: false }, worker: { alive: false } }; }
  }
  return { health, isInitialized, checkHealth };
});

// Sync Store
window.useSyncStore = defineStore('sync', () => {
  const status = ref({ running: false, current: 0, total: 0, speed_mbps: null, eta_seconds: null });
  const queue = ref([]);
  async function fetchStatus() {
    try { status.value = await api.get('/sync/status'); } catch (e) {}
  }
  async function fetchQueue() {
    try { queue.value = await api.get('/sync/queue'); } catch (e) {}
  }
  return { status, queue, fetchStatus, fetchQueue };
});

// Profiles Store
window.useProfilesStore = defineStore('profiles', () => {
  const list = ref([]);
  const total = ref(0);
  const loading = ref(false);
  async function fetchList(params = {}) {
    loading.value = true;
    try {
      const r = await api.get(`/profiles?${new URLSearchParams(params)}`);
      list.value = r.items; total.value = r.total;
    } catch (e) { console.error('Fetch profiles error:', e); }
    finally { loading.value = false; }
  }
  async function getProfile(id) { return api.get(`/profiles/${id}`); }
  async function createProfile(data) { return api.post('/profiles', data); }
  async function updateProfile(id, data) { return api.put(`/profiles/${id}`, data); }
  async function deleteProfile(id) { return api.delete(`/profiles/${id}`); }
  async function exportProfile(id) { return api.get(`/profiles/${id}/export`); }
  async function importProfile(data) { return api.post('/profiles/import', data); }
  return { list, total, loading, fetchList, getProfile, createProfile, updateProfile, deleteProfile, exportProfile, importProfile };
});

// Settings Store
window.useSettingsStore = defineStore('settings', () => {
  const settings = ref({});
  async function fetch() {
    try { settings.value = await api.get('/settings'); } catch (e) {}
  }
  async function update(data) { return api.put('/settings', data); }
  return { settings, fetch, update };
});
