const { ref, reactive, computed, watch, onMounted, onUnmounted, defineComponent } = Vue;
const { useRouter, useRoute } = VueRouter;

// ----- Shared Components -----
const ThemeToggle = { template: '<span/>' };

const Pagination = {
  props: ['page', 'totalPages'],
  emits: ['page-change'],
  template: `<div class="pagination" v-if="totalPages>1">
    <button class="btn btn-sm" :disabled="page<=1" @click="$emit('page-change',page-1)">上一页</button>
    <span class="text-sm text-secondary">{{page}} / {{totalPages}}</span>
    <button class="btn btn-sm" :disabled="page>=totalPages" @click="$emit('page-change',page+1)">下一页</button>
  </div>`
};

const EmptyState = {
  props: ['icon', 'title', 'description'],
  template: `<div class="empty-state"><div class="icon">{{icon||"📭"}}</div>
    <h3 style="margin-bottom:8px;font-weight:600">{{title||"暂无数据"}}</h3>
    <p>{{description||""}}</p></div>`
};

// ----- Dashboard -----
const Dashboard = {
  components: { EmptyState },
  setup() {
    const router = useRouter();
    const syncStore = useSyncStore();
    const settingsStore = useSettingsStore();
    const stats = ref({ total_synced: 0, total_photos: 0, active_profiles: 0, storage_used: 0 });
    const recentActivity = ref([]);
    const loading = ref(true);

    onMounted(async () => {
      try {
        const r = await api.get('/system/stats');
        stats.value = r;
        const h = await api.get('/history?page_size=5');
        recentActivity.value = h.items || [];
      } catch (e) {}
      loading.value = false;
      await syncStore.fetchStatus();
    });

    const formatSize = (b) => {
      if (!b) return '0 B';
      const u = ['B','KB','MB','GB']; let i = 0;
      while (b >= 1024 && i < u.length-1) { b /= 1024; i++; }
      return `${b.toFixed(1)} ${u[i]}`;
    };

    return { stats, recentActivity, loading, router, syncStore, formatSize };
  },
  template: `<div>
    <h2 class="font-bold text-lg mb-4">仪表盘</h2>
    <div v-if="loading"><div class="spinner"></div></div>
    <template v-else>
      <div class="grid-3 mb-4">
        <div class="card stat-card"><div class="stat-value">{{stats.total_synced}}</div><div class="stat-label">已同步文件</div></div>
        <div class="card stat-card"><div class="stat-value">{{stats.active_profiles}}</div><div class="stat-label">活跃配置</div></div>
        <div class="card stat-card"><div class="stat-value">{{formatSize(stats.storage_used)}}</div><div class="stat-label">存储占用</div></div>
      </div>
      <div class="grid-2">
        <div class="card"><h3 style="margin-bottom:12px;font-weight:600">同步状态</h3>
          <div class="flex items-center gap-3" style="margin-bottom:12px">
            <span class="badge" :class="syncStore.status.running?'badge-green':'badge-yellow'">{{syncStore.status.running?'运行中':'空闲'}}</span>
            <span class="text-sm text-secondary">进度: {{syncStore.status.current}}/{{syncStore.status.total}}</span>
            <span class="text-sm text-secondary" v-if="syncStore.status.speed_mbps">{{syncStore.status.speed_mbps}} MB/s</span>
          </div>
          <div class="progress-bar" v-if="syncStore.status.total>0">
            <div class="progress-fill" :style="{width:(syncStore.status.current/syncStore.status.total*100)+'%'}"></div>
          </div>
        </div>
        <div class="card"><h3 style="margin-bottom:12px;font-weight:600">最近同步</h3>
          <div v-if="recentActivity.length===0"><EmptyState title="暂无同步记录" description="开始使用后这里会显示最近的同步活动"/></div>
          <div v-for="item in recentActivity" :key="item.id" class="flex items-center justify-between" style="padding:8px 0;border-bottom:1px solid var(--border)">
            <div><div class="text-sm font-medium">{{item.file_name||'未知文件'}}</div>
              <div class="text-xs text-muted">{{item.created_at}}</div></div>
            <span class="badge" :class="item.status==='success'?'badge-green':item.status==='failed'?'badge-red':'badge-yellow'">{{item.status==='success'?'成功':item.status==='failed'?'失败':'进行中'}}</span>
          </div>
        </div>
      </div>
      <div style="margin-top:12px">
        <button class="btn btn-primary" @click="router.push('/profiles/new')">+ 新建同步配置</button>
      </div>
    </template>
  </div>`
};

// ----- Profiles -----
const Profiles = {
  components: { Pagination, EmptyState },
  setup() {
    const store = useProfilesStore();
    const router = useRouter();
    const page = ref(1);
    const deleting = ref(null);

    const fetchData = () => store.fetchList({ page: page.value, page_size: 20 });
    onMounted(fetchData);

    const confirmDelete = async (id) => {
      if (!confirm('确定删除此同步配置？')) return;
      deleting.value = id;
      try { await store.deleteProfile(id); await fetchData(); } catch (e) { alert('删除失败: ' + e.message); }
      finally { deleting.value = null; }
    };

    const syncModeLabel = (m) => ({ mirror: '镜像', incremental: '增量', smart: '智能' })[m] || m;
    const matchTypeLabel = (m) => ({ card_label: '卡标签', device_name: '设备名', path_pattern: '路径模式', all: '全部' })[m] || m;

    return { store, router, page, deleting, confirmDelete, syncModeLabel, matchTypeLabel, fetchData };
  },
  template: `<div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-bold text-lg">同步配置</h2>
      <button class="btn btn-primary" @click="router.push('/profiles/new')">+ 新建</button>
    </div>
    <div v-if="store.loading" class="text-center text-secondary">加载中...</div>
    <div v-else-if="store.list.length===0"><EmptyState icon="⚙️" title="暂无同步配置" description="点击上方按钮创建第一个同步配置"/></div>
    <div v-else>
      <table><thead><tr><th>名称</th><th>匹配方式</th><th>目标路径</th><th>同步模式</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="p in store.list" :key="p.id">
            <td class="font-medium">{{p.name}}</td>
            <td class="text-sm text-secondary">{{matchTypeLabel(p.match_type)}}: {{p.match_value}}</td>
            <td class="text-sm text-secondary" style="max-width:200px;overflow:hidden;text-overflow:ellipsis">{{p.destination}}</td>
            <td><span class="badge" :class="p.sync_mode==='mirror'?'badge-blue':p.sync_mode==='incremental'?'badge-green':'badge-yellow'">{{syncModeLabel(p.sync_mode)}}</span></td>
            <td><span class="badge" :class="p.enabled?'badge-green':'badge-red'">{{p.enabled?'启用':'禁用'}}</span></td>
            <td><div class="flex gap-2"><button class="btn btn-sm" @click="router.push('/profiles/'+p.id)">编辑</button>
              <button class="btn btn-sm btn-danger" :disabled="deleting===p.id" @click="confirmDelete(p.id)">{{deleting===p.id?'删除中...':'删除'}}</button></div></td>
          </tr>
        </tbody>
      </table>
      <Pagination :page="page" :total-pages="Math.ceil(store.total/20)" @page-change="p=>{page=p;fetchData()}"/>
    </div>
  </div>`
};

// ----- Profile Detail (Create/Edit) -----
const ProfileDetail = {
  setup() {
    const router = useRouter();
    const route = useRoute();
    const store = useProfilesStore();
    const isEdit = computed(() => !!route.params.id);
    const loading = ref(true);
    const saving = ref(false);
    const form = reactive({
      name: '', match_type: 'card_label', match_value: '', destination: '',
      sync_mode: 'incremental', auto_sync: true, enabled: true,
      poll_interval: 5, conflict_strategy: 'skip', copy_mode: 'copy',
      file_filters: '*.jpg,*.jpeg,*.png,*.heic,*.dng,*.arw,*.cr2,*.nef',
      auto_eject: false, checksum_verify: false, custom_template: ''
    });

    onMounted(async () => {
      if (isEdit.value) {
        try {
          const p = await store.getProfile(parseInt(route.params.id));
          Object.assign(form, p);
        } catch (e) { alert('加载失败'); router.push('/profiles'); }
      }
      loading.value = false;
    });

    const save = async () => {
      saving.value = true;
      try {
        const data = { ...form };
        if (isEdit.value) await store.updateProfile(parseInt(route.params.id), data);
        else await store.createProfile(data);
        router.push('/profiles');
      } catch (e) { alert('保存失败: ' + e.message); }
      finally { saving.value = false; }
    };

    return { router, isEdit, loading, saving, form, save };
  },
  template: `<div>
    <div class="flex items-center gap-3 mb-4">
      <button class="btn btn-ghost" @click="router.push('/profiles')">← 返回</button>
      <h2 class="font-bold text-lg">{{isEdit?'编辑同步配置':'新建同步配置'}}</h2>
    </div>
    <div class="card" v-if="!loading">
      <div class="form-row">
        <div class="form-group"><label>配置名称</label><input v-model="form.name" placeholder="例如: 我的相机"></div>
        <div class="form-group"><label>目标路径</label><input v-model="form.destination" placeholder="/volume2/照片/相机"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>匹配方式</label>
          <select v-model="form.match_type">
            <option value="card_label">储存卡标签</option>
            <option value="device_name">设备名称</option>
            <option value="path_pattern">路径模式</option>
            <option value="all">全部设备</option>
          </select></div>
        <div class="form-group"><label>匹配值</label><input v-model="form.match_value" placeholder="根据匹配方式填写"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>同步模式</label>
          <select v-model="form.sync_mode">
            <option value="incremental">增量同步</option>
            <option value="mirror">镜像同步</option>
            <option value="smart">智能同步</option>
          </select></div>
        <div class="form-group"><label>冲突策略</label>
          <select v-model="form.conflict_strategy">
            <option value="skip">跳过</option>
            <option value="overwrite">覆盖</option>
            <option value="rename">重命名</option>
          </select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>复制模式</label>
          <select v-model="form.copy_mode">
            <option value="copy">复制</option>
            <option value="move">移动（剪切）</option>
            <option value="link">硬链接</option>
          </select></div>
        <div class="form-group"><label>轮询间隔（秒）</label><input type="number" v-model.number="form.poll_interval" min="1"></div>
      </div>
      <div class="form-group"><label>文件筛选（逗号分隔）</label><input v-model="form.file_filters" placeholder="*.jpg,*.png"></div>
      <div class="form-group"><label>目标路径模板</label><input v-model="form.custom_template" placeholder="可选: {{date}}/{{camera}}/{{filename}}"></div>
      <div class="flex gap-4" style="margin-bottom:14px;flex-wrap:wrap">
        <label class="flex items-center gap-2"><span class="text-sm">自动同步</span>
          <label class="toggle"><input type="checkbox" v-model="form.auto_sync"><span class="toggle-slider"></span></label></label>
        <label class="flex items-center gap-2"><span class="text-sm">插入后弹出</span>
          <label class="toggle"><input type="checkbox" v-model="form.auto_eject"><span class="toggle-slider"></span></label></label>
        <label class="flex items-center gap-2"><span class="text-sm">校验和验证</span>
          <label class="toggle"><input type="checkbox" v-model="form.checksum_verify"><span class="toggle-slider"></span></label></label>
      </div>
      <div class="flex gap-3">
        <button class="btn btn-primary" @click="save" :disabled="saving">{{saving?'保存中...':'保存'}}</button>
        <button class="btn" @click="router.push('/profiles')">取消</button>
      </div>
    </div>
  </div>`
};

// ----- History -----
const History = {
  components: { Pagination, EmptyState },
  setup() {
    const items = ref([]);
    const total = ref(0);
    const page = ref(1);
    const loading = ref(true);
    const router = useRouter();
    const filter = ref('');

    const fetchData = async () => {
      loading.value = true;
      try {
        const params = { page: page.value, page_size: 30 };
        if (filter.value) params.status = filter.value;
        const r = await api.get(`/history?${new URLSearchParams(params)}`);
        items.value = r.items; total.value = r.total;
      } catch (e) {}
      loading.value = false;
    };
    onMounted(fetchData);

    return { items, total, page, loading, router, filter, fetchData };
  },
  template: `<div>
    <h2 class="font-bold text-lg mb-4">同步记录</h2>
    <div class="flex gap-3 mb-4">
      <select v-model="filter" @change="fetchData" style="width:auto">
        <option value="">全部</option>
        <option value="success">成功</option>
        <option value="failed">失败</option>
        <option value="skipped">跳过</option>
      </select>
    </div>
    <div v-if="loading" class="text-center text-secondary">加载中...</div>
    <div v-else-if="items.length===0"><EmptyState title="暂无同步记录"/></div>
    <div v-else>
      <table><thead><tr><th>文件</th><th>来源</th><th>状态</th><th>大小</th><th>时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" style="cursor:pointer" @click="router.push('/history/'+item.id)">
            <td class="font-medium" style="max-width:200px;overflow:hidden;text-overflow:ellipsis">{{item.file_name||'-'}}</td>
            <td class="text-sm text-secondary" style="max-width:150px;overflow:hidden;text-overflow:ellipsis">{{item.source_path||'-'}}</td>
            <td><span class="badge" :class="item.status==='success'?'badge-green':item.status==='failed'?'badge-red':'badge-yellow'">{{item.status}}</span></td>
            <td class="text-sm text-secondary">{{item.file_size?((item.file_size/1024).toFixed(1)+' KB'):'-'}}</td>
            <td class="text-sm text-secondary">{{item.created_at||'-'}}</td>
            <td><button class="btn btn-sm" @click.stop="router.push('/history/'+item.id)">详情</button></td>
          </tr>
        </tbody>
      </table>
      <Pagination :page="page" :total-pages="Math.ceil(total/30)" @page-change="p=>{page=p;fetchData()}"/>
    </div>
  </div>`
};

// ----- History Detail -----
const HistoryDetail = {
  setup() {
    const router = useRouter();
    const route = useRoute();
    const item = ref(null);
    const loading = ref(true);
    onMounted(async () => {
      try { item.value = await api.get(`/history/${route.params.id}`); } catch (e) {}
      loading.value = false;
    });
    return { router, item, loading };
  },
  template: `<div>
    <div class="flex items-center gap-3 mb-4"><button class="btn btn-ghost" @click="router.push('/history')">← 返回</button>
      <h2 class="font-bold text-lg">同步详情</h2></div>
    <div v-if="loading" class="text-center text-secondary">加载中...</div>
    <div class="card" v-else-if="item">
      <table><tbody>
        <tr><th style="width:120px">文件</th><td>{{item.file_name||'-'}}</td></tr>
        <tr><th>来源路径</th><td>{{item.source_path||'-'}}</td></tr>
        <tr><th>目标路径</th><td>{{item.destination_path||'-'}}</td></tr>
        <tr><th>状态</th><td><span class="badge" :class="item.status==='success'?'badge-green':item.status==='failed'?'badge-red':'badge-yellow'">{{item.status}}</span></td></tr>
        <tr><th>文件大小</th><td>{{item.file_size?((item.file_size/1024).toFixed(1)+' KB'):'-'}}</td></tr>
        <tr><th>创建时间</th><td>{{item.created_at||'-'}}</td></tr>
        <tr><th>消息</th><td class="text-sm">{{item.message||'-'}}</td></tr>
        <tr v-if="item.error_info"><th>错误信息</th><td class="text-sm" style="color:var(--danger)">{{item.error_info}}</td></tr>
      </tbody></table>
    </div>
  </div>`
};

// ----- Settings -----
const Settings = {
  setup() {
    const router = useRouter();
    const store = useSettingsStore();
    const form = reactive({ poll_interval: 5, auto_sync: true, log_level: 'INFO', theme: 'auto', max_history_days: 30 });
    const saving = ref(false);

    onMounted(async () => {
      await store.fetch();
      Object.assign(form, store.settings);
    });

    const save = async () => {
      saving.value = true;
      try { await store.update(form); alert('设置已保存'); } catch (e) { alert('保存失败'); }
      finally { saving.value = false; }
    };

    return { form, saving, save, router };
  },
  template: `<div>
    <h2 class="font-bold text-lg mb-4">系统设置</h2>
    <div class="card" style="max-width:600px">
      <div class="form-group"><label>轮询间隔（秒）</label><input type="number" v-model.number="form.poll_interval" min="1"></div>
      <div class="form-group"><label>日志级别</label>
        <select v-model="form.log_level">
          <option value="DEBUG">DEBUG</option><option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option><option value="ERROR">ERROR</option>
        </select></div>
      <div class="form-group"><label>主题</label>
        <select v-model="form.theme">
          <option value="auto">跟随系统</option><option value="light">亮色</option><option value="dark">暗色</option>
        </select></div>
      <div class="form-group"><label>历史记录保留天数</label><input type="number" v-model.number="form.max_history_days" min="1"></div>
      <label class="flex items-center gap-2 mb-4"><span class="text-sm">自动同步</span>
        <label class="toggle"><input type="checkbox" v-model="form.auto_sync"><span class="toggle-slider"></span></label></label>
      <button class="btn btn-primary" @click="save" :disabled="saving">{{saving?'保存中...':'保存设置'}}</button>
    </div>
  </div>`
};

// ----- Logs -----
const Logs = {
  setup() {
    const logs = ref([]);
    const loading = ref(true);
    const level = ref('INFO');
    const autoRefresh = ref(true);
    let timer = null;

    const fetchLogs = async () => {
      try {
        const r = await api.get(`/system/logs?level=${level.value}&lines=200`);
        logs.value = r.lines || r;
      } catch (e) {}
      loading.value = false;
    };

    onMounted(() => {
      fetchLogs();
      if (autoRefresh.value) timer = setInterval(fetchLogs, 5000);
    });
    onUnmounted(() => { if (timer) clearInterval(timer); });

    return { logs, loading, level, fetchLogs };
  },
  template: `<div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="font-bold text-lg">系统日志</h2>
      <div class="flex gap-3 items-center">
        <select v-model="level" @change="fetchLogs" style="width:auto">
          <option value="DEBUG">DEBUG</option><option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option><option value="ERROR">ERROR</option>
        </select>
        <button class="btn btn-sm" @click="fetchLogs">刷新</button>
      </div>
    </div>
    <div class="card" style="font-family:monospace;font-size:12px;line-height:1.6;max-height:70vh;overflow-y:auto;background:var(--bg-input)">
      <div v-if="loading" class="text-center text-secondary">加载中...</div>
      <div v-for="(line, i) in logs" :key="i" style="white-space:pre-wrap;word-break:break-all;padding:1px 0"
        :style="{ color: line.includes('ERROR')?'var(--danger)':line.includes('WARNING')?'var(--warning)':'inherit' }">{{line}}</div>
      <div v-if="!loading && logs.length===0" class="text-center text-muted" style="padding:20px">暂无日志</div>
    </div>
  </div>`
};

// ----- Gallery -----
const Gallery = {
  components: { EmptyState },
  setup() {
    const photos = ref([]);
    const loading = ref(true);
    const page = ref(1);
    const total = ref(0);
    const router = useRouter();

    const fetchData = async () => {
      loading.value = true;
      try {
        const r = await api.get(`/gallery?page=${page.value}&page_size=30`);
        photos.value = r.items || r.photos || r;
        total.value = r.total || photos.value.length;
      } catch (e) {}
      loading.value = false;
    };
    onMounted(fetchData);

    return { photos, loading, page, total, router, fetchData };
  },
  template: `<div>
    <h2 class="font-bold text-lg mb-4">照片画廊</h2>
    <div v-if="loading" class="text-center text-secondary">加载中...</div>
    <div v-else-if="photos.length===0"><EmptyState icon="🖼️" title="暂无照片" description="同步照片后它们会出现在这里"/></div>
    <div v-else>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px">
        <div v-for="p in photos" :key="p.id || p.filename" class="card" style="padding:8px;cursor:pointer"
          @click="router.push('/gallery?file='+(p.filename||p.path))">
          <img :src="(p.thumbnail_url||'/api/v1/gallery/thumbnail/'+(p.id||p.filename))" 
            :alt="p.filename||p.original_name" style="width:100%;height:150px;object-fit:cover;border-radius:8px"
            @error="$event.target.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23e2e8f0%22 width=%22100%22 height=%22100%22/><text x=%2250%22 y=%2250%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%2394a3b8%22>📷</text></svg>'">
          <p class="text-sm text-secondary" style="margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{p.original_name||p.filename||'-'}}</p>
        </div>
      </div>
    </div>
  </div>`
};

// ----- Setup Wizard -----
const SetupWizard = {
  setup() {
    const router = useRouter();
    const step = ref(1);
    const loading = ref(true);
    const status = reactive({ check: 'pending', storage: 'pending', ready: false });
    const profiles = reactive({ name: '默认配置', destination: '/photos', match_type: 'all', sync_mode: 'incremental' });

    onMounted(async () => {
      try {
        const h = await api.get('/system/health');
        status.check = h.status === 'healthy' ? 'ok' : 'error';
        status.ready = h.db?.connected;
      } catch (e) { status.check = 'error'; }
      loading.value = false;
    });

    const finish = async () => {
      try {
        await api.post('/profiles', { name: profiles.name, match_type: profiles.match_type,
          match_value: '', destination: profiles.destination, sync_mode: profiles.sync_mode,
          auto_sync: true, enabled: true, poll_interval: 5, conflict_strategy: 'skip',
          copy_mode: 'copy', file_filters: '*.jpg,*.jpeg,*.png,*.heic,*.dng,*.arw,*.cr2,*.nef',
          auto_eject: false, checksum_verify: false, custom_template: '' });
        router.push('/');
      } catch (e) { alert('创建失败: ' + e.message); }
    };

    return { step, loading, status, profiles, finish, router };
  },
  template: `<div style="max-width:600px;margin:40px auto">
    <h2 class="font-bold text-lg mb-4" style="text-align:center">🎉 欢迎使用 PhotoSync</h2>
    <div class="wizard-steps">
      <div class="wizard-step" :class="{active:step===1,done:step>1}">系统检测</div>
      <div class="wizard-step" :class="{active:step===2,done:step>2}">基本配置</div>
      <div class="wizard-step" :class="{active:step===3}">完成</div>
    </div>
    <div class="card">
      <div v-if="step===1">
        <h3 style="margin-bottom:12px;font-weight:600">🔍 系统检测</h3>
        <div v-if="loading" class="text-center">检测中...</div>
        <div v-else>
          <div class="flex items-center gap-3 mb-2"><span>{{status.check==='ok'?'✅':'❌'}}</span><span>数据库连接</span></div>
          <div class="flex items-center gap-3 mb-4"><span>{{status.ready?'✅':'⏳'}}</span><span>系统状态</span></div>
          <button class="btn btn-primary" @click="step=2" :disabled="!status.ready">下一步</button>
        </div>
      </div>
      <div v-if="step===2">
        <h3 style="margin-bottom:12px;font-weight:600">⚙️ 基本配置</h3>
        <div class="form-group"><label>配置名称</label><input v-model="profiles.name"></div>
        <div class="form-group"><label>目标路径</label><input v-model="profiles.destination" placeholder="/photos"></div>
        <div class="form-group"><label>匹配方式</label>
          <select v-model="profiles.match_type">
            <option value="all">全部储存卡</option>
            <option value="card_label">指定卡标签</option>
          </select></div>
        <div class="form-group"><label>同步模式</label>
          <select v-model="profiles.sync_mode">
            <option value="incremental">增量同步</option><option value="mirror">镜像同步</option>
          </select></div>
        <div class="flex gap-3"><button class="btn" @click="step=1">上一步</button>
          <button class="btn btn-primary" @click="step=3">下一步</button></div>
      </div>
      <div v-if="step===3">
        <h3 style="margin-bottom:12px;font-weight:600">✅ 设置完成</h3>
        <p class="text-secondary mb-4">PhotoSync 已准备好使用。你现在可以：</p>
        <ul class="text-sm text-secondary mb-4" style="padding-left:20px;line-height:2">
          <li>插入储存卡后自动同步照片</li>
          <li>在仪表盘查看同步进度</li>
          <li>创建多个同步配置</li>
          <li>浏览和查看已同步的照片</li>
        </ul>
        <button class="btn btn-primary" @click="finish">开始使用</button>
      </div>
    </div>
  </div>`
};

// ----- Card Browser -----
const CardBrowser = {
  components: { EmptyState },
  setup() {
    const cards = ref([]);
    const loading = ref(true);
    const router = useRouter();
    onMounted(async () => {
      try { cards.value = await api.get('/cards'); } catch (e) {}
      loading.value = false;
    });
    return { cards, loading, router };
  },
  template: `<div>
    <h2 class="font-bold text-lg mb-4">储存卡管理</h2>
    <div v-if="loading" class="text-center text-secondary">扫描中...</div>
    <div v-else-if="cards.length===0"><EmptyState icon="💾" title="未检测到储存卡" description="插入储存卡后会自动识别"/></div>
    <div v-else>
      <div class="grid-2">
        <div v-for="card in cards" :key="card.id||card.device" class="card">
          <div class="flex items-center justify-between">
            <div><h3 class="font-medium">{{card.label||card.device||'未知设备'}}</h3>
              <p class="text-sm text-muted mt-2">{{card.path||'-'}} | {{card.fs_type||''}} {{card.total_size?((card.total_size/1073741824).toFixed(1)+'GB'):''}}</p>
              <p class="text-sm text-secondary mt-2" v-if="card.photo_count">📸 {{card.photo_count}} 张照片</p>
            </div>
            <div class="flex gap-2 flex-col">
              <span class="badge" :class="card.mounted?'badge-green':'badge-yellow'">{{card.mounted?'已挂载':'未挂载'}}</span>
              <button class="btn btn-sm btn-primary" v-if="card.mounted && card.photo_count>0"
                @click="router.push('/profiles/new?source='+card.path)">同步此卡</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>`
};

// Register all view components
const Views = { Dashboard, Profiles, ProfileDetail, History, HistoryDetail, Settings, Logs, Gallery, SetupWizard, CardBrowser, ThemeToggle, Pagination, EmptyState };
