import axios from 'axios'

// Обязательно задайте VITE_API_URL при сборке на Vercel (напр. https://cafe-backend.up.railway.app).
// В dev остаётся "/api" — прокси. Проксируется в vite.config.ts.
const API_BASE: string = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

const api = axios.create({
  baseURL: API_BASE ? `${API_BASE}/api` : '/api',
  timeout: 10_000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
