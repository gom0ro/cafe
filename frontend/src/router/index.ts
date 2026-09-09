import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../views/Dashboard.vue'
import Floor from '../views/Floor.vue'
import POS from '../views/POS.vue'
import Menu from '../views/Menu.vue'
import Staff from '../views/Staff.vue'
import Inventory from '../views/Inventory.vue'
import Kitchen from '../views/Kitchen.vue'
import Analytics from '../views/Analytics.vue'
import Settings from '../views/Settings.vue'
import Login from '../views/Login.vue'
import api from '../api'
import { useAppStore } from '../stores'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { public: true } },
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { roles: ['admin', 'cashier', 'waiter', 'chef'] } },
  { path: '/floor', name: 'Floor', component: Floor, meta: { roles: ['admin', 'cashier', 'waiter'] } },
  { path: '/pos', name: 'POS', component: POS, meta: { roles: ['admin', 'cashier', 'waiter'] } },
  { path: '/menu', name: 'Menu', component: Menu, meta: { roles: ['admin', 'cashier', 'waiter'] } },
  { path: '/staff', name: 'Staff', component: Staff, meta: { roles: ['admin'] } },
  { path: '/inventory', name: 'Inventory', component: Inventory, meta: { roles: ['admin', 'chef'] } },
  { path: '/kitchen', name: 'Kitchen', component: Kitchen, meta: { roles: ['admin', 'chef'] } },
  { path: '/analytics', name: 'Analytics', component: Analytics, meta: { roles: ['admin'] } },
  { path: '/settings', name: 'Settings', component: Settings, meta: { roles: ['admin', 'cashier', 'waiter', 'chef'] } }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const appStore = useAppStore()
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  if (!to.meta.public && !token) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.path === '/login' && token) return { path: '/' }

  if (token && !appStore.user) {
    try {
      const [me, profile] = await Promise.all([
        api.get('/auth/me'),
        api.get('/profile/me')
      ])
      appStore.setUser({
        id: me.data.id,
        email: me.data.email,
        full_name: profile.data.full_name || me.data.full_name || me.data.email,
        role: me.data.role,
        avatar: profile.data.avatar || ''
      })
      if (profile.data.dashboard_preferences) appStore.setDashboardPreferences(profile.data.dashboard_preferences)
      if (profile.data.socials) appStore.setSocialLinks(profile.data.socials)
    } catch {
      appStore.clearAuth()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  const roles = (to.meta.roles as string[] | undefined) || []
  if (roles.length && appStore.user?.role && !roles.includes(appStore.user.role)) {
    const roleRedirects: Record<string, string> = {
      admin: '/',
      cashier: '/floor',
      waiter: '/floor',
      chef: '/kitchen'
    }
    return { path: roleRedirects[appStore.user.role] || '/' }
  }
})

export default router
