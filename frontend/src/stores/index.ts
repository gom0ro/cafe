import { defineStore } from 'pinia'

function loadPrefs() {
  try {
    const raw = localStorage.getItem('dashboardPrefs')
    if (raw) return JSON.parse(raw)
  } catch {
    // ignore bad storage
  }
  return null
}

const storedPrefs = loadPrefs() || {}

function getStoredToken() {
  return localStorage.getItem('token') || sessionStorage.getItem('token') || ''
}

export const useAppStore = defineStore('app', {
  state: () => ({
    user: null as null | { id: number; email: string; full_name?: string; role?: string; avatar?: string },
    token: getStoredToken(),
    theme: 'auto',
    dashboardPreferences: {
      accent: storedPrefs.accent || '#3b82f6',
      density: storedPrefs.density || 'comfortable',
      radius: storedPrefs.radius || '24px',
      glass: storedPrefs.glass ?? true,
      show_metrics: storedPrefs.show_metrics ?? true,
      show_activity: storedPrefs.show_activity ?? true
    },
    socialLinks: {
      telegram: '',
      instagram: '',
      whatsapp: '',
      github: '',
      x: '',
      website: ''
    }
  }),
  actions: {
    setUser(u: any) { this.user = u },
    setToken(token: string, remember = true) {
      this.token = token
      sessionStorage.removeItem('token')
      localStorage.removeItem('token')
      if (remember) localStorage.setItem('token', token)
      else sessionStorage.setItem('token', token)
    },
    clearAuth() {
      this.user = null
      this.token = ''
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
    },
    setDashboardPreferences(prefs: Partial<typeof this.dashboardPreferences>) {
      this.dashboardPreferences = { ...this.dashboardPreferences, ...prefs }
    },
    setSocialLinks(links: Partial<typeof this.socialLinks>) {
      this.socialLinks = { ...this.socialLinks, ...links }
    }
  }
})
