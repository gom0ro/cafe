<template>
  <Particles />
  <div v-if="isPublicRoute" class="public-page">
    <button
      class="theme-toggle theme-toggle--floating"
      :title="isDarkTheme ? 'Включить светлую тему' : 'Включить тёмную тему'"
      :aria-label="isDarkTheme ? 'Включить светлую тему' : 'Включить тёмную тему'"
      @click="toggleTheme"
    >
      <UiIcon :name="isDarkTheme ? 'sun' : 'moon'" :size="18" />
    </button>
    <router-view />
  </div>
  <div
    v-else
    class="app-shell"
    :class="{
      'app-shell--sidebar-open': menuOpen,
      'app-shell--sidebar-collapsed': collapsed
    }"
  >
    <div
      v-if="menuOpen"
      class="sidebar-overlay"
      aria-hidden="true"
      @click="menuOpen = false"
    />

    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar__brand">
          <div class="brand__mark">CF</div>
          <div class="sidebar__brand-text">
            <div class="brand__title">Cafe</div>
            <div class="brand__subtitle">Management</div>
          </div>
        </div>
        <button
          class="sidebar-close"
          aria-label="Закрыть меню"
          title="Закрыть меню"
          @click="closeMobileMenu"
        >
          <UiIcon name="x" :size="20" />
        </button>
      </div>

      <nav class="sidebar__nav">
        <router-link
          v-for="item in visibleNav"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :title="item.label"
          @click="closeMobileMenu"
        >
          <UiIcon :name="item.icon" :size="18" class="sidebar-link__icon" />
          <span class="sidebar-link__label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div v-if="appStore.user" class="sidebar__footer">
        <div class="sidebar-user">
          <img
            v-if="appStore.user.avatar"
            :src="appStore.user.avatar"
            class="user-chip__avatar user-chip__avatar--img"
            alt="avatar"
          />
          <div v-else class="user-chip__avatar">
            {{ avatarInitials }}
          </div>
          <div class="sidebar-user__meta">
            <div class="user-chip__name">{{ displayName }}</div>
            <div class="user-chip__role">{{ roleLabel }}</div>
          </div>
        </div>
        <button
          class="button button--ghost button--sm sidebar-logout"
          title="Выход"
          @click="logout"
        >
          <UiIcon name="log-out" :size="16" />
          <span>Выход</span>
        </button>
      </div>
    </aside>

    <div class="app-body">
      <header class="content-topbar">
        <button
          class="burger-toggle"
          :class="{ 'burger-toggle--active': isMobile ? menuOpen : !collapsed }"
          aria-label="Меню"
          @click="toggleSidebar"
        >
          <span class="burger-lines">
            <span class="line line--1" />
            <span class="line line--2" />
            <span class="line line--3" />
          </span>
        </button>

        <div class="content-topbar__title">
          <span class="content-topbar__page">{{ currentPageTitle }}</span>
        </div>

        <div class="content-topbar__actions">
          <button
            class="theme-toggle"
            :title="isDarkTheme ? 'Включить светлую тему' : 'Включить тёмную тему'"
            :aria-label="isDarkTheme ? 'Включить светлую тему' : 'Включить тёмную тему'"
            @click="toggleTheme"
          >
            <UiIcon :name="isDarkTheme ? 'sun' : 'moon'" :size="18" />
          </button>
          <div class="role-badge role-badge--compact">
            <UiIcon name="shield" :size="15" class="role-badge__icon" />
            <span>{{ roleLabel }}</span>
          </div>
        </div>
      </header>

      <main class="app-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from './api'
import { useAppStore } from './stores'
import { applyTheme, getStoredTheme, startThemeEngine, type ThemeMode } from './composables/useTheme'
import UiIcon from './components/UiIcon.vue'
import Particles from './components/Particles.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
startThemeEngine()

const theme = ref<ThemeMode>(getStoredTheme())
const isDarkTheme = computed(() => theme.value === 'dark')

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  applyTheme(theme.value)
}

const menuOpen = ref(false)
const collapsed = ref(false)
const isMobile = ref(false)

const isPublicRoute = computed(() => route.meta.public === true)

const role = computed(() => appStore.user?.role || 'guest')
const displayName = computed(() => appStore.user?.full_name || appStore.user?.email || 'Guest')
const roleLabel = computed(() => {
  const labels: Record<string, string> = {
    admin: 'Администратор',
    cashier: 'Кассир',
    waiter: 'Официант',
    chef: 'Повар',
    guest: 'Гость'
  }
  return labels[role.value] || 'Сотрудник'
})

const navItems = [
  { to: '/', label: 'Дашборд', icon: 'dashboard' },
  { to: '/floor', label: 'Зал', icon: 'coffee' },
  { to: '/pos', label: 'Касса', icon: 'pos' },
  { to: '/menu', label: 'Меню', icon: 'menu' },
  { to: '/staff', label: 'Персонал', icon: 'users' },
  { to: '/inventory', label: 'Склад', icon: 'inventory' },
  { to: '/kitchen', label: 'Кухня', icon: 'food' },
  { to: '/analytics', label: 'Аналитика', icon: 'analytics' },
  { to: '/settings', label: 'Настройки', icon: 'settings' }
]

const visibleNav = computed(() => {
  const permissions: Record<string, string[]> = {
    admin: ['/', '/floor', '/pos', '/menu', '/staff', '/inventory', '/kitchen', '/analytics', '/settings'],
    cashier: ['/', '/floor', '/pos', '/menu', '/settings'],
    waiter: ['/', '/floor', '/pos', '/menu', '/settings'],
    chef: ['/', '/inventory', '/kitchen', '/settings']
  }
  const allowed = permissions[role.value] || []
  return navItems.filter((item) => allowed.includes(item.to))
})

const currentPageTitle = computed(() => {
  const match = navItems.find((item) => item.to === route.path)
  return match?.label || 'Cafe Management'
})

const avatarInitials = computed(() => {
  const source = displayName.value.trim()
  if (!source) return 'CF'
  return source.split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'CF'
})

function updateViewport() {
  isMobile.value = window.innerWidth < 1024
  if (!isMobile.value) {
    menuOpen.value = false
  }
}

function toggleSidebar() {
  if (isMobile.value) {
    menuOpen.value = !menuOpen.value
  } else {
    collapsed.value = !collapsed.value
  }
}

function closeMobileMenu() {
  if (isMobile.value) {
    menuOpen.value = false
  }
}

async function logout() {
  appStore.clearAuth()
  await router.push('/login')
}

watch(() => route.path, closeMobileMenu)

onMounted(async () => {
  updateViewport()
  window.addEventListener('resize', updateViewport)

  // The router guard already loads the profile; only fall back if it didn't.
  await router.isReady()
  if (!appStore.token || appStore.user) return
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
    if (profile.data.dashboard_preferences) {
      appStore.setDashboardPreferences(profile.data.dashboard_preferences)
    }
    if (profile.data.socials) {
      appStore.setSocialLinks(profile.data.socials)
    }
  } catch (e) {
    console.error('Failed to load user profile:', e)
    appStore.clearAuth()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', updateViewport)
})
</script>

<style scoped>
.public-page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--overlay-04);
  color: var(--text-control);
  flex-shrink: 0;
  transition: 0.18s ease;
}

.theme-toggle:hover {
  background: var(--overlay-09);
  color: var(--accent);
  box-shadow: var(--shadow-soft);
}

.theme-toggle--floating {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  z-index: 20;
}
</style>
