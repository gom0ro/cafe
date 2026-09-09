<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="food" :size="16" />
          <span>Кухня · живая лента заказов</span>
        </div>
        <h1 class="hero__title">Кухня</h1>
        <p class="hero__lead">Новые заказы появляются автоматически. Принимайте в работу и отмечайте готовность.</p>
      </div>
      <div class="hero__actions">
        <div class="hero__chip" :class="liveStatusClass">
          <span class="status-dot" />
          <span>{{ liveStatusText }}</span>
        </div>
        <button class="button button--secondary button--sm" title="Обновить вручную" @click="loadOrders">
          <svg class="progress-ring" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
            <circle class="progress-ring__track" cx="9" cy="9" r="7" />
            <circle class="progress-ring__bar" cx="9" cy="9" r="7" :style="{ strokeDashoffset: progressOffset }" />
          </svg>
          <span>Обновить</span>
        </button>
      </div>
    </section>

    <div v-if="loading" class="list">
      <div v-for="n in 4" :key="n" class="skeleton" style="height: 10rem; border-radius: 24px;"></div>
    </div>

    <section v-else-if="orders.length" class="kitchen-grid">
      <article v-for="order in orders" :key="order.id" class="glass panel kitchen-card" :class="`kitchen-card--${order.status}`">
        <div class="kitchen-card__header">
          <div>
            <h2 class="kitchen-card__number">Заказ #{{ order.id }}</h2>
            <p class="kitchen-card__table">
              <UiIcon name="pos" :size="14" />
              {{ tableLabel(order.table_id) }}
            </p>
          </div>
          <span class="status-badge" :class="statusBadge(order.status)">
            <span class="status-dot" />
            <span>{{ statusLabel(order.status) }}</span>
          </span>
        </div>

        <div class="kitchen-card__time">{{ timeAgo(order.created_at) }}</div>

        <ul class="kitchen-card__items">
          <li v-for="item in order.items" :key="item.id" class="kitchen-card__item">
            <span class="kitchen-card__qty">{{ item.qty }}×</span>
            <span class="kitchen-card__name">{{ item.name || `Блюдо #${item.menu_item_id}` }}</span>
            <span class="kitchen-card__price">{{ formatMoney(item.price * item.qty) }}</span>
          </li>
        </ul>

        <div v-if="order.notes" class="kitchen-card__notes">
          <UiIcon name="file-text" :size="14" />
          <span>{{ order.notes }}</span>
        </div>

        <div class="kitchen-card__footer">
          <div class="kitchen-card__total">
            <span>Итого</span>
            <strong>{{ formatMoney(order.total) }}</strong>
          </div>
          <div class="kitchen-card__actions">
            <button
              v-if="order.status === 'new'"
              type="button"
              class="button button--primary button--sm"
              :disabled="busyId === order.id"
              @click="setStatus(order, 'kitchen')"
            >
              <UiIcon name="zap" :size="14" />
              <span>Взять в работу</span>
            </button>
            <button
              v-if="order.status === 'kitchen'"
              type="button"
              class="button button--primary button--sm"
              :disabled="busyId === order.id"
              @click="setStatus(order, 'ready')"
            >
              <UiIcon name="check" :size="14" />
              <span>Готово</span>
            </button>
            <button
              v-if="order.status === 'ready'"
              type="button"
              class="button button--secondary button--sm"
              :disabled="busyId === order.id"
              @click="setStatus(order, 'paid', 'card')"
            >
              <UiIcon name="check-circle" :size="14" />
              <span>Подано</span>
            </button>
          </div>
        </div>
      </article>
    </section>

    <section v-else class="glass panel kitchen-empty">
      <div class="kitchen-empty__icon">
        <UiIcon name="coffee" :size="56" style="color: var(--muted);" />
      </div>
      <h2 class="kitchen-empty__title">Нет активных заказов</h2>
      <p class="kitchen-empty__sub">Новые заказы из кассы появятся здесь автоматически.</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import { tableLabel as tableLabelOf } from '../lib/tableLabel'
import { useAppStore } from '../stores'
import { wsUrl } from '../ws'

interface OrderItem {
  id: number
  menu_item_id: number
  name?: string
  qty: number
  price: number
}

interface Order {
  id: number
  status: string
  total: number
  notes?: string
  table_id?: number | null
  created_at?: string
  items: OrderItem[]
}

interface Table {
  id: number
  number: string
}

const appStore = useAppStore()

const orders = ref<Order[]>([])
const tables = ref<Table[]>([])
const loading = ref(true)
const busyId = ref<number | null>(null)

const liveStatusText = ref('live sync')
const liveStatusClass = ref('hero__chip--live')

const formatMoney = (n: number): string => Math.round(n).toLocaleString('ru-RU') + ' ₸'

const statusLabels: Record<string, string> = {
  new: 'Новый',
  kitchen: 'В работе',
  ready: 'Готов',
  paid: 'Оплачен',
  cancelled: 'Отменён'
}

const statusBadge = (status: string): string => {
  const map: Record<string, string> = {
    new: 'status-badge--neutral',
    kitchen: 'status-badge--warning',
    ready: 'status-badge--success',
    paid: 'status-badge--success',
    cancelled: 'status-badge--danger'
  }
  return map[status] || 'status-badge--neutral'
}

const statusLabel = (status: string): string => statusLabels[status] || status

function tableLabel(id?: number | null): string {
  if (!id) return 'Без столика'
  const t = tables.value.find((x) => x.id === id)
  return t ? tableLabelOf(t) : `Стол #${id}`
}

const sortedOrders = computed(() =>
  orders.value.sort((a, b) => {
    const rank: Record<string, number> = { new: 0, kitchen: 1, ready: 2 }
    if (rank[a.status] !== rank[b.status]) return rank[a.status] - rank[b.status]
    return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  })
)

function timeAgo(iso?: string): string {
  if (!iso) return ''
  const diff = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (diff < 60) return 'только что'
  if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`
  return `${Math.floor(diff / 3600)} ч назад`
}

async function loadTables() {
  try {
    const r = await api.get<Table[]>('/tables/')
    tables.value = r.data
  } catch {
    tables.value = []
  }
}

const REFRESH_INTERVAL = 10000
const RING_CIRC = 2 * Math.PI * 7

const progressRatio = ref(0)
let lastRefreshAt = Date.now()

const progressOffset = computed(() => {
  const p = Math.min(1, Math.max(0, progressRatio.value))
  return String(RING_CIRC * (1 - p))
})

function resetCountdown() {
  lastRefreshAt = Date.now()
  progressRatio.value = 0
}

async function fetchOrders() {
  try {
    const r = await api.get<Order[]>('/orders/', { params: { status: 'new,kitchen,ready', limit: 100 } })
    orders.value = r.data
    liveStatusText.value = 'live sync'
    liveStatusClass.value = 'hero__chip--live'
  } catch (e) {
    liveStatusText.value = 'нет связи'
    liveStatusClass.value = 'hero__chip--error'
    console.error('Failed to load orders:', e)
  } finally {
    loading.value = false
  }
}

async function loadOrders() {
  resetCountdown()
  await fetchOrders()
}

async function setStatus(order: Order, status: string, payment_method?: string) {
  busyId.value = order.id
  try {
    const payload: Record<string, string> = { status }
    if (payment_method) payload.payment_method = payment_method
    await api.patch(`/orders/${order.id}/status`, payload)
    await loadOrders()
  } catch (e) {
    console.error('Failed to update order status:', e)
    liveStatusText.value = 'ошибка обновления'
    liveStatusClass.value = 'hero__chip--error'
  } finally {
    busyId.value = null
  }
}

let ws: WebSocket | null = null
let wsTimer: ReturnType<typeof setTimeout> | null = null
let tickTimer: ReturnType<typeof setInterval> | null = null

function startAutoRefresh() {
  tickTimer = setInterval(() => {
    const elapsed = Date.now() - lastRefreshAt
    if (elapsed >= REFRESH_INTERVAL) {
      loadOrders()
    } else {
      progressRatio.value = elapsed / REFRESH_INTERVAL
    }
  }, 100)
}

function connectWebSocket() {
  const socket = new WebSocket(wsUrl('/ws/orders'))
  ws = socket

  socket.onopen = () => {
    liveStatusText.value = 'live sync'
    liveStatusClass.value = 'hero__chip--live'
  }

  socket.onmessage = () => fetchOrders()

  socket.onclose = () => {
    liveStatusText.value = 'offline'
    liveStatusClass.value = 'hero__chip--error'
    if (wsTimer) clearTimeout(wsTimer)
    wsTimer = setTimeout(() => {
      if (document.visibilityState !== 'hidden') connectWebSocket()
    }, 5000)
  }

  socket.onerror = () => socket.close()
}

function disconnectWebSocket() {
  if (wsTimer) clearTimeout(wsTimer)
  ws?.close()
  ws = null
}

onMounted(() => {
  loadOrders()
  loadTables()
  startAutoRefresh()
  connectWebSocket()
})

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer)
  disconnectWebSocket()
})
</script>

<style scoped>
.hero__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}

.hero__chip--live {
  gap: 0.55rem;
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.35);
  color: #059669;
}

.hero__chip--live .status-dot {
  animation: chip-pulse 1.6s ease-in-out infinite;
}

@keyframes chip-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.45);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
    transform: scale(1.2);
  }
}

.hero__chip--error {
  color: var(--danger-soft);
  border-color: rgba(239, 68, 68, 0.35);
}

.progress-ring {
  display: block;
}

.progress-ring__track {
  fill: none;
  stroke: var(--overlay-12);
  stroke-width: 2;
}

.progress-ring__bar {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-dasharray: 43.9823;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
  transition: stroke-dashoffset 0.1s linear;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.kitchen-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.kitchen-card {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-left: 3px solid var(--overlay-12);
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.kitchen-card--new {
  border-left-color: var(--accent);
}

.kitchen-card--kitchen {
  border-left-color: var(--olive-bright);
}

.kitchen-card--ready {
  border-left-color: var(--forest-mid);
}

.kitchen-card:hover {
  transform: translateY(-2px);
}

.kitchen-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.kitchen-card__number {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 750;
  color: var(--text-strong);
}

.kitchen-card__table {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin: 0.3rem 0 0;
  color: var(--muted);
  font-size: 0.85rem;
}

.kitchen-card__time {
  font-size: 0.8rem;
  color: var(--muted);
}

.kitchen-card__items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.kitchen-card__item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  background: var(--item-bg);
  border: 1px solid var(--border);
}

.kitchen-card__qty {
  font-weight: 800;
  color: var(--accent);
  min-width: 2rem;
}

.kitchen-card__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.kitchen-card__price {
  color: var(--muted);
  font-size: 0.85rem;
}

.kitchen-card__notes {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  padding: 0.6rem 0.75rem;
  border-radius: 12px;
  background: rgba(250, 204, 21, 0.08);
  border: 1px solid rgba(250, 204, 21, 0.25);
  color: var(--text-control);
  font-size: 0.85rem;
}

.kitchen-card__footer {
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.kitchen-card__total {
  display: flex;
  flex-direction: column;
  font-size: 0.82rem;
  color: var(--muted);
}

.kitchen-card__total strong {
  font-size: 1.1rem;
  color: var(--text-strong);
}

.kitchen-card__actions {
  display: flex;
  gap: 0.5rem;
}

.kitchen-empty {
  text-align: center;
  padding: 4rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.kitchen-empty__title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-strong);
}

.kitchen-empty__sub {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
}
</style>