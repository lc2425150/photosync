const { createApp, ref, onMounted } = Vue;
const { createRouter, createWebHistory } = VueRouter;
const { createPinia } = Pinia;

// --- Routes ---
const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard',             component: Views.Dashboard },
  { path: '/profiles',              component: Views.Profiles },
  { path: '/profiles/new',          component: Views.ProfileDetail, props: { mode: 'create' } },
  { path: '/profiles/:id',          component: Views.ProfileDetail, props: true },
  { path: '/history',               component: Views.History },
  { path: '/history/:id',           component: Views.HistoryDetail },
  { path: '/gallery',               component: Views.Gallery },
  { path: '/cards',                 component: Views.CardBrowser },
  { path: '/logs',                  component: Views.Logs },
  { path: '/settings',              component: Views.Settings },
  { path: '/setup',                 component: Views.SetupWizard },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// --- Pinia ---
const pinia = createPinia();

// --- App ---
const app = createApp({
  setup() {
    const loading = ref(true);
    const isDark = ref(false);

    const navItems = [
      { path: '/dashboard', label: '仪表盘' },
      { path: '/profiles',  label: '同步配置' },
      { path: '/history',   label: '同步历史' },
      { path: '/gallery',   label: '照片浏览' },
      { path: '/cards',     label: '储存卡' },
      { path: '/logs',      label: '日志' },
      { path: '/settings',  label: '设置' },
    ];

    function toggleTheme() {
      isDark.value = !isDark.value;
      document.documentElement.classList.toggle('dark', isDark.value);
      localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
    }

    onMounted(async () => {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        isDark.value = true;
        document.documentElement.classList.add('dark');
      }
      try {
        await useSystemStore().checkHealth();
      } catch (_) { /* ignore */ }
      loading.value = false;
    });

    return { loading, isDark, navItems, toggleTheme };
  },
});

app.use(pinia);
app.use(router);
app.mount('#app');
