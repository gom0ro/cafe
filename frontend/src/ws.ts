// Хелпер для WebSocket-подключений через тот же бэкенд, что и REST API.
// В dev (VITE_API_URL не задан) — ведём на location.host (Vite-proxy '/ws').
// В проде (Vercel) — на хост бэкенда из VITE_API_URL.
const API_BASE: string = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

export function wsUrl(path: string): string {
  let host = location.host
  if (API_BASE) {
    host = API_BASE.replace(/^https?:\/\//, '')
  }
  const secure = API_BASE.startsWith('https') || location.protocol === 'https:'
  return `${secure ? 'wss' : 'ws'}://${host}${path}`
}