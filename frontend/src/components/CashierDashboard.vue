<template>
  <div>
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="pos" :size="16" />
          <span>Касса · день</span>
        </div>
        <h1 class="hero__title">Добрый день, {{ userName }}</h1>
        <p class="hero__lead">Выручка, способы оплаты и открытые счета за сегодня.</p>
      </div>
      <div class="hero__actions">
        <div class="hero__chip" :class="liveStatusClass">
          <span class="status-dot" />
          <span>{{ liveStatusText }}</span>
        </div>
        <button class="button button--secondary button--sm" title="Обновить вручную" @click="loadStats">
          <svg class="progress-ring" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
            <circle class="progress-ring__track" cx="9" cy="9" r="7" />
            <circle class="progress-ring__bar" cx="9" cy="9" r="7" :style="{ strokeDashoffset: progressOffset }" />
          </svg>
          <span>Обновить</span>
        </button>
        <button class="button button--primary button--sm" @click="router.push('/pos')">
          <UiIcon name="pos" :size="14" />
          <span>Открыть кассу</span>
        </button>
      </div>
    </section>

    <div v-if="loading" class="list">
      <div v-for="n in 4" :key="n" class="skeleton" style="height: 9rem; border-radius: 24px;"></div>
    </div>

    <template v-else>
      <section class="grid-cards grid-cards--4 dashboard-metrics">
        <article v-for="metric in metrics" :key="metric.label" class="glass panel metric">
          <div class="metric__icon" :class="metric.iconClass">
            <UiIcon :name="metric.icon" :size="18" />
          </div>
          <p class="metric__label">{{ metric.label }}</p>
          <h3 class="metric__value">{{ metric.value }}</h3>
        </article>
      </section>

      <section class="content-grid content-grid--two">
        <article class="glass panel panel--large">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="receipt" :size="20" />
            <span>Способы оплаты</span>
          </h2>

          <div v-if="payments.length" class="list pay-list">
            <div v-for="p in payments" :key="p.method" class="item pay-item">
              <div class="pay-item__info">
                <div class="item__title">{{ p.label }}</div>
                <div class="item__sub">{{ p.count }} {{ pluralOrders(p.count) }} · {{ pct(p) }}</div>
              </div>
              <strong class="pay-item__sum">{{ money(p.value) }}</strong>
            </div>
          </div>
          <p v-else class="empty-hint">Сегодня оплат ещё нет</p>
        </article>

        <article class="glass panel panel--large">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="inventory" :size="20" />
            <span>Счета за столиками</span>
          </h2>

          <div v-if="openTables.length" class="list table-list">
            <div
              v-for="t in openTables"
              :key="t.id"
              class="item table-item"
              title="Перейти к оплате"
              @click="router.push('/pos?table=' + t.id)"
            >
              <div>
                <div class="item__title">
                  {{ tableLabel(t) }}
                </div>
                <div class="table-item__badges">
                  <span v-for="o in t.orders" :key="o.order_id" class="status-badge" :class="badgeClass(o.status)">
                    <span class="status-dot" />
                    #{{ o.order_id }} · {{ statusLabel(o.status) }} · {{ money(o.total) }}
                  </span>
                </div>
              </div>
              <strong class="pay-item__sum">{{ money(t.total) }}</strong>
            </div>
          </div>
          <p v-else class="empty-hint">Нет активных счетов</p>
        </article>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import { tableLabel } from '../lib/tableLabel'
import { useAppStore } from '../stores'

interface PaymentRow { method: string; label: string; value: number; count: number }
interface OpenTableOrder { order_id: number; status: string; total: number }
interface OpenTable { id: number; number: string; name?: string; total: number; orders: OpenTableOrder[] }
interface CashierStats {
  revenue_today: number
  orders_today: number
  avg_check: number
  payments: PaymentRow[]
  open_tables: OpenTable[]
}

const router = useRouter()
const appStore = useAppStore()

const userName = computed(() => {
  const name = appStore.user?.full_name || appStore.user?.email || 'коллега'
  return name.split(' ')[0]
})

const emptyStats = (): CashierStats => ({
  revenue_today: 0,
  orders_today: 0,
  avg_check: 0,
  payments: [],
  open_tables: []
})

const stats = ref<CashierStats>(emptyStats())
const loading = ref(true)
const liveStatusText = ref('live sync')
const liveStatusClass = ref('hero__chip--live')

const money = (n: number): string => Math.round(n).toLocaleString('ru-RU') + ' ₸'

const payments = computed(() => stats.value.payments)
const openTables = computed(() => stats.value.open_tables)

const metrics = computed(() => [
  { label: 'Выручка сегодня', value: money(stats.value.revenue_today), icon: 'analytics', iconClass: 'metric__icon--green' },
  { label: 'Оплачено чеков', value: String(stats.value.orders_today), icon: 'pos', iconClass: 'metric__icon--coffee' },
  { label: 'Средний чек', value: money(stats.value.avg_check), icon: 'receipt', iconClass: 'metric__icon--olive' },
  { label: 'Счетов за столиками', value: String(openTables.value.length), icon: 'inventory', iconClass: 'metric__icon--earth' }
])

const pct = (p: PaymentRow): string => {
  const total = stats.value.revenue_today
  if (!total) return '0%'
  return Math.round((p.value / total) * 100) + '%'
}

const statusLabels: Record<string, string> = {
  new: 'Новый',
  kitchen: 'В работе',
  ready: 'Готов'
}

const statusLabel = (s: string): string => statusLabels[s] || s

const badgeClass = (s: string): string => {
  const map: Record<string, string> = {
    new: 'status-badge--neutral',
    kitchen: 'status-badge--warning',
    ready: 'status-badge--success'
  }
  return map[s] || 'status-badge--neutral'
}

const pluralOrders = (n: number): string => {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'чек'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'чека'
  return 'чеков'
}

async function loadStats() {
  resetCountdown()
  try {
    const res = await api.get<CashierStats>('/dashboard/cashier')
    stats.value = res.data
    liveStatusText.value = 'live sync'
    liveStatusClass.value = 'hero__chip--live'
  } catch (e) {
    liveStatusText.value = 'нет связи'
    liveStatusClass.value = 'hero__chip--error'
    console.error('Failed to load cashier stats:', e)
  } finally {
    loading.value = false
  }
}

const REFRESH_INTERVAL = 15000
const RING_CIRC = 2 * Math.PI * 7

const progressRatio = ref(0)
let lastRefreshAt = Date.now()
let tickTimer: ReturnType<typeof setInterval> | null = null

const progressOffset = computed(() => {
  const p = Math.min(1, Math.max(0, progressRatio.value))
  return String(RING_CIRC * (1 - p))
})

function resetCountdown() {
  lastRefreshAt = Date.now()
  progressRatio.value = 0
}

function startAutoRefresh() {
  tickTimer = setInterval(() => {
    const elapsed = Date.now() - lastRefreshAt
    if (elapsed >= REFRESH_INTERVAL) {
      loadStats()
    } else {
      progressRatio.value = elapsed / REFRESH_INTERVAL
    }
  }, 100)
}

onMounted(() => {
  loadStats()
  startAutoRefresh()
})

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer)
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
  animation: chip-pulse-live 1.6s ease-in-out infinite;
}

@keyframes chip-pulse-live {
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

.dashboard-metrics {
  margin-bottom: 1.5rem;
  gap: 1.5rem;
}

.metric__icon--green {
  background: rgba(34, 197, 94, 0.14);
  color: var(--forest-light);
}

.metric__icon--olive {
  background: rgba(22, 163, 74, 0.14);
  color: var(--forest-light);
}

.metric__icon--coffee {
  background: rgba(74, 222, 128, 0.14);
  color: var(--forest-light);
}

.metric__icon--earth {
  background: rgba(134, 239, 172, 0.1);
  color: var(--forest-light);
}

.pay-list,
.table-list {
  gap: 0.75rem;
}

.pay-item,
.table-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.pay-item__info {
  min-width: 0;
}

.pay-item__sum {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--forest-light);
  white-space: nowrap;
}

.table-item {
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.table-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}

.table-item__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.5rem;
}

.empty-hint {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0.5rem 0 0;
}
</style>