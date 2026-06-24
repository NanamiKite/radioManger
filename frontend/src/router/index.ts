import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/logs/LogsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/logs/:id',
    name: 'LogDetail',
    component: () => import('@/views/logs/LogDetailView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dxclusters',
    name: 'DXClusters',
    component: () => import('@/views/dxcluster/DXClusterView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/stations',
    name: 'Stations',
    component: () => import('@/views/stations/StationsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/callsigns',
    name: 'Callsigns',
    component: () => import('@/views/callsigns/CallsignSearchView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/shortcuts',
    name: 'Shortcuts',
    component: () => import('@/views/shortcuts/ShortcutsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/AnalysisView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recycle',
    name: 'RecycleBin',
    component: () => import('@/views/recycle/RecycleBinView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tools',
    name: 'Tools',
    component: () => import('@/views/tools/ToolsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/map',
    name: 'Map',
    component: () => import('@/views/map/MapView.vue'),
    meta: { requiresAuth: true }
  },
  // ── Admin 路由（仅服务器模式） ──
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/admin/UsersView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/system',
    name: 'AdminSystem',
    component: () => import('@/views/admin/SystemView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/audit',
    name: 'AdminAudit',
    component: () => import('@/views/admin/AuditLogView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 未登录 → 跳转登录页
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' })
    return
  }

  // 已登录访问登录/注册 → 跳转首页
  if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }

  // Admin 路由守卫：仅服务器模式 + admin 角色可访问
  if (to.meta.requiresAdmin) {
    // 确保 dbMode 已获取
    if (authStore.dbMode === 'sqlite' && authStore.isAuthenticated) {
      await authStore.fetchDbMode()
    }
    const dbMode = authStore.dbMode
    const isAdmin = authStore.user?.role === 'admin'
    if (dbMode === 'sqlite' || !isAdmin) {
      next({ name: 'Dashboard' })
      return
    }
  }

  next()
})

export default router
