export type ThemeMode = 'dark' | 'light'

const STORAGE_KEY = 'appTheme'

export function getStoredTheme(): ThemeMode {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'dark' || v === 'light') return v
  } catch {
    // ignore unreadable storage
  }
  return 'dark'
}

export function applyTheme(theme: ThemeMode): void {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // ignore unwritable storage
  }
}

export function initTheme(): void {
  if (typeof document === 'undefined') return
  applyTheme(getStoredTheme())
}

export function startThemeEngine() {
  if (typeof document === 'undefined') return

  const storedPrefs = localStorage.getItem('dashboardPrefs')
  if (storedPrefs) {
    try {
      const prefs = JSON.parse(storedPrefs)
      if (prefs.accent) document.documentElement.style.setProperty('--accent', prefs.accent)
      if (prefs.radius) document.documentElement.style.setProperty('--radius-panel', prefs.radius)
      if (prefs.density) document.body.dataset.density = prefs.density
    } catch {
      // ignore invalid local storage
    }
  }
}

export {}
