<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="pos" :size="16" />
          <span>Зал · план столиков</span>
        </div>
        <h1 class="hero__title">Зал</h1>
        <p class="hero__lead">
          Статус столиков, ближайшие брони и открытые счета. Клик по столику — открыть кассу с его счётом.
        </p>
      </div>
      <div class="hero__actions">
        <div class="hero__chip" :class="liveClass">
          <span class="status-dot" />
          <span>{{ liveText }}</span>
        </div>
        <button class="button button--secondary button--sm" title="Обновить вручную" @click="loadData">
          <svg class="progress-ring" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
            <circle class="progress-ring__track" cx="9" cy="9" r="7" />
            <circle class="progress-ring__bar" cx="9" cy="9" r="7" :style="{ strokeDashoffset: progressOffset }" />
          </svg>
          <span>Обновить</span>
        </button>
        <button class="button button--secondary button--sm" @click="openBookingForm">
          <UiIcon name="calendar" :size="14" />
          <span>Забронировать</span>
        </button>
      </div>
    </section>

    <Transition name="status">
      <form v-if="showBookingForm" class="glass panel panel--large floor-booking" @submit.prevent="submitBooking">
        <div class="floor-booking__head">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="calendar" :size="18" />
            <span>Новая бронь</span>
          </h2>
          <button type="button" class="icon-btn" title="Закрыть" @click="showBookingForm = false">
            <UiIcon name="x" :size="16" />
          </button>
        </div>

        <div class="floor-booking__grid">
          <div class="form-group">
            <UiSelect
              v-model="bookingForm.table_id"
              :options="bookingMainOptions"
              label="Столик"
              placeholder="Выберите столик"
            />
          </div>
          <div class="form-group">
            <UiSelect
              v-model="bookingForm.linked_table_id"
              :options="bookingLinkedOptions"
              label="Доп. столик (объединить)"
              placeholder="Не нужен"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Имя гостя</label>
            <input v-model="bookingForm.customer_name" class="input" placeholder="Иван" />
          </div>
          <div class="form-group">
            <label class="form-label">Телефон</label>
            <input v-model="bookingForm.phone" class="input" placeholder="+7 ___ ___-__-__" />
          </div>
          <div class="form-group">
            <label class="form-label">Гостей</label>
            <input v-model.number="bookingForm.guests" class="input" type="number" min="1" placeholder="2" />
          </div>
          <div class="form-group">
            <label class="form-label">Начало брони</label>
            <input v-model="bookingForm.starts_at" class="input" type="datetime-local" required />
          </div>
          <div class="form-group">
            <label class="form-label">Комментарий</label>
            <input v-model="bookingForm.note" class="input" placeholder="Повод, пожелания" />
          </div>
        </div>

        <p class="booking-capacity" :class="{ 'booking-capacity--warn': bookingForm.table_id && bookingForm.guests > bookingCapacity }">
          <UiIcon name="users" :size="16" />
          <span v-if="bookingForm.table_id">
            Вместимость: до {{ bookingCapacity }} мест
            <template v-if="bookingForm.guests > bookingCapacity"> — гостей больше, чем можно разместить</template>
            <template v-else-if="bookingForm.linked_table_id"> (два столика объединены)</template>
          </span>
          <span v-else>Выберите столик</span>
        </p>

        <div class="toolbar floor-booking__actions">
          <button
            type="submit"
            class="button button--primary"
            :disabled="!bookingForm.table_id || !bookingForm.starts_at || bookingSaving"
          >
            <UiIcon name="calendar" :size="16" />
            <span>{{ bookingSaving ? 'Сохраняем…' : 'Забронировать' }}</span>
          </button>
          <button type="button" class="button button--ghost" @click="showBookingForm = false">
            <UiIcon name="x" :size="16" />
            <span>Отмена</span>
          </button>
          <span v-if="bookingMsg" class="form-msg form-msg--ok">{{ bookingMsg }}</span>
          <span v-if="bookingError" class="form-msg form-msg--error">{{ bookingError }}</span>
        </div>
      </form>
    </Transition>

    <div v-if="loading" class="list">
      <div v-for="n in 6" :key="n" class="skeleton" style="height: 8.5rem; border-radius: 24px;"></div>
    </div>

    <template v-else>
      <p v-if="!zones.length" class="empty-hint">Столиков пока нет — добавьте их в настройках.</p>

      <section v-for="zone in zones" :key="zone.name" class="floor-zone">
        <div class="floor-zone__head">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="pos" :size="18" />
            <span>{{ zone.name }}</span>
          </h2>
          <span class="zone-summary">{{ zone.busy }}/{{ zone.tables.length }} занято</span>
        </div>

        <div class="tables-grid">
          <article
            v-for="t in zone.tables"
            :key="t.id"
            class="glass panel table-card"
            :class="`table-card--${states[t.id]?.kind || 'free'}`"
            @click="openTable(t)"
          >
            <div class="table-card__top">
              <div class="table-card__num">{{ tableLabel(t) }}</div>
              <span class="status-badge" :class="states[t.id]?.badgeClass">
                <span class="status-dot" />
                {{ states[t.id]?.badgeText }}
              </span>
            </div>

            <div class="table-card__info">
              <div class="item__sub">{{ t.seats }} мест{{ t.zone ? ' · ' + t.zone : '' }}</div>
            </div>

            <div v-if="states[t.id]?.readyCount" class="table-card__ready">
              <UiIcon name="zap" :size="14" />
              <span>Готово к подаче · {{ states[t.id].readyCount }} {{ pluralOrders(states[t.id].readyCount) }}</span>
            </div>

            <div v-if="states[t.id]?.orders.length" class="table-card__bill">
              <div class="table-card__bill-info">
                <div class="item__title">Счёт столика</div>
                <div class="item__sub">
                  {{ states[t.id].orders.length }} {{ pluralOrders(states[t.id].orders.length) }} · не оплачен
                </div>
              </div>
              <strong class="table-card__sum">{{ money(states[t.id].total) }}</strong>
            </div>

            <div v-else-if="states[t.id]?.booking" class="table-card__booking">
              <div class="table-card__booking-info">
                <div class="item__title">{{ states[t.id].booking.customer_name || 'Бронь' }}</div>
                <div class="item__sub">
                  {{ formatWhen(states[t.id].booking.starts_at) }} · {{ states[t.id].booking.guests }} {{ pluralGuests(states[t.id].booking.guests) }}
                </div>
              </div>
              <div class="table-card__booking-actions">
                <button
                  type="button"
                  class="button button--secondary button--sm"
                  :disabled="bookingBusyId === states[t.id].booking.id"
                  @click.stop="completeBooking(states[t.id].booking)"
                >
                  <UiIcon name="check-circle" :size="14" />
                  <span>Стол занят</span>
                </button>
                <button
                  type="button"
                  class="button button--ghost button--sm"
                  :disabled="bookingBusyId === states[t.id].booking.id"
                  @click.stop="cancelBooking(states[t.id].booking)"
                >
                  <UiIcon name="x" :size="14" />
                  <span>Отменить</span>
                </button>
              </div>
            </div>

            <button
              type="button"
              class="button button--primary button--sm table-card__cta"
              @click.stop="openTable(t)"
            >
              <UiIcon :name="states[t.id]?.orders.length ? 'receipt' : 'plus'" :size="14" />
              <span>
                {{ states[t.id]?.orders.length ? 'Открыть счёт' : 'Новый заказ' }}
              </span>
            </button>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import UiSelect from '../components/UiSelect.vue'
import { tableLabel } from '../lib/tableLabel'
import type { SelectOption } from '../components/UiSelect.vue'

interface Table {
  id: number
  number: string
  name?: string
  seats: number
  zone?: string
  is_active: boolean
}

interface Booking {
  id: number
  table_id: number
  linked_table_id?: number | null
  customer_name?: string | null
  phone?: string | null
  guests: number
  starts_at: string
  status: string
  note?: string | null
}

interface Order {
  id: number
  status: string
  total: number
  table_id?: number | null
}

interface TableState {
  orders: Order[]
  total: number
  booking: Booking | null
  readyCount: number
  kind: 'busy' | 'booked' | 'free'
  badgeText: string
  badgeClass: string
}

interface ZoneGroup {
  name: string
  tables: Table[]
  busy: number
}

const router = useRouter()

const tables = ref<Table[]>([])
const bookings = ref<Booking[]>([])
const orders = ref<Order[]>([])
const loading = ref(true)

const liveText = ref('live sync')
const liveClass = ref('hero__chip--live')

const showBookingForm = ref(false)
const bookingSaving = ref(false)
const bookingMsg = ref('')
const bookingError = ref('')
const bookingBusyId = ref<number | null>(null)
const bookingForm = reactive({
  table_id: null as number | null,
  linked_table_id: null as number | null,
  customer_name: '',
  phone: '+7',
  guests: 2,
  starts_at: '',
  note: ''
})

const bookingMainOptions = computed<SelectOption[]>(() =>
  tables.value
    .filter((t) => t.id !== bookingForm.linked_table_id)
    .map((t) => ({ value: t.id, label: tableLabel(t) }))
)

const bookingLinkedOptions = computed<SelectOption[]>(() => [
  { value: null, label: 'Не нужен' },
  ...tables.value
    .filter((t) => t.id !== bookingForm.table_id)
    .map((t) => ({ value: t.id, label: tableLabel(t) }))
])

const bookingCapacity = computed(() => {
  const cap = (id?: number | null) => {
    const t = tables.value.find((x) => x.id === id)
    return t ? t.seats || 4 : 0
  }
  return cap(bookingForm.table_id) + cap(bookingForm.linked_table_id)
})

function openBookingForm() {
  if (!bookingForm.starts_at) bookingForm.starts_at = defaultBookingStart()
  showBookingForm.value = true
  bookingMsg.value = ''
  bookingError.value = ''
}

function resetBookingForm() {
  bookingForm.table_id = null
  bookingForm.linked_table_id = null
  bookingForm.customer_name = ''
  bookingForm.phone = '+7'
  bookingForm.guests = 2
  bookingForm.starts_at = defaultBookingStart()
  bookingForm.note = ''
}

async function submitBooking() {
  if (!bookingForm.table_id) return
  bookingSaving.value = true
  bookingMsg.value = ''
  bookingError.value = ''
  try {
    await api.post('/bookings/', {
      table_id: bookingForm.table_id,
      linked_table_id: bookingForm.linked_table_id,
      customer_name: bookingForm.customer_name.trim() || null,
      phone: bookingForm.phone.trim() ? bookingForm.phone.trim() : null,
      guests: bookingForm.guests || 1,
      starts_at: bookingForm.starts_at,
      note: bookingForm.note.trim() || null
    })
    bookingMsg.value = 'Бронь создана'
    resetBookingForm()
    await loadData()
    setTimeout(() => {
      if (bookingMsg.value === 'Бронь создана') bookingMsg.value = ''
    }, 3000)
  } catch (e) {
    bookingError.value = errText(e)
  } finally {
    bookingSaving.value = false
  }
}

function errText(e: any): string {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return 'Не удалось выполнить операцию'
}

function defaultBookingStart(): string {
  const d = new Date(Date.now() + 60 * 60 * 1000)
  d.setMinutes(0, 0, 0)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const money = (n: number): string => Math.round(n || 0).toLocaleString('ru-RU') + ' ₸'

const pad = (n: number): string => String(n).padStart(2, '0')

const pluralOrders = (n: number): string => {
  const m10 = n % 10
  const m100 = n % 100
  if (m10 === 1 && m100 !== 11) return 'чек'
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return 'чека'
  return 'чеков'
}

const pluralGuests = (n: number): string => {
  const m10 = n % 10
  const m100 = n % 100
  if (m10 === 1 && m100 !== 11) return 'гость'
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return 'гостя'
  return 'гостей'
}

const formatWhen = (iso: string): string => {
  const d = new Date(iso)
  const now = new Date()
  const tomorrow = new Date(now)
  tomorrow.setDate(now.getDate() + 1)
  const hm = pad(d.getHours()) + ':' + pad(d.getMinutes())
  if (d.toDateString() === now.toDateString()) return 'сегодня в ' + hm
  if (d.toDateString() === tomorrow.toDateString()) return 'завтра в ' + hm
  return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + ' в ' + hm
}

const states = computed<Record<number, TableState>>(() => {
  const openByTable = new Map<number, Order[]>()
  for (const o of orders.value) {
    if (!o.table_id || o.status === 'cancelled') continue
    const list = openByTable.get(o.table_id) || []
    list.push(o)
    openByTable.set(o.table_id, list)
  }

  const booked = new Map<number, Booking>()
  for (const b of bookings.value) {
    if (b.status !== 'confirmed') continue
    const ts = new Date(b.starts_at).getTime()
    const attach = (id: number) => {
      const cur = booked.get(id)
      if (!cur || ts < new Date(cur.starts_at).getTime()) booked.set(id, b)
    }
    attach(b.table_id)
    if (b.linked_table_id) attach(b.linked_table_id)
  }

  const result: Record<number, TableState> = {}
  for (const t of tables.value) {
    const list = openByTable.get(t.id) || []
    const total = list.reduce((sum, o) => sum + (o.total || 0), 0)
    const readyCount = list.filter((o) => o.status === 'ready').length
    const booking = booked.get(t.id) || null
    let kind: TableState['kind'] = 'free'
    if (list.length) kind = 'busy'
    else if (booking) kind = 'booked'
    result[t.id] = {
      orders: list,
      total,
      booking,
      readyCount,
      kind,
      badgeText: readyCount && list.length ? 'Готово' : kind === 'busy' ? 'Занят' : kind === 'booked' ? 'Бронь' : 'Свободен',
      badgeClass: readyCount && list.length ? 'status-badge--success' : kind === 'busy' ? 'status-badge--success' : kind === 'booked' ? 'status-badge--warning' : 'status-badge--neutral'
    }
  }
  return result
})

const zones = computed<ZoneGroup[]>(() => {
  const groups = new Map<string, Table[]>()
  for (const t of tables.value) {
    const zoneName = t.zone?.trim() || 'Зал'
    const list = groups.get(zoneName) || []
    list.push(t)
    groups.set(zoneName, list)
  }
  return Array.from(groups.entries()).map(([name, list]) => ({
    name,
    tables: list,
    busy: list.filter((t) => states.value[t.id]?.kind === 'busy').length
  }))
})

function openTable(t: Table) {
  router.push('/pos?table=' + t.id)
}

async function completeBooking(b: Booking) {
  if (bookingBusyId.value) return
  bookingBusyId.value = b.id
  try {
    await api.patch(`/bookings/${b.id}`, { status: 'completed' })
    await loadData()
  } catch (e) {
    console.error('Failed to complete booking:', e)
  } finally {
    bookingBusyId.value = null
  }
}

async function cancelBooking(b: Booking) {
  if (bookingBusyId.value) return
  bookingBusyId.value = b.id
  try {
    await api.patch(`/bookings/${b.id}`, { status: 'cancelled' })
    await loadData()
  } catch (e) {
    console.error('Failed to cancel booking:', e)
  } finally {
    bookingBusyId.value = null
  }
}

async function loadData() {
  resetCountdown()
  try {
    const [tablesRes, allBookingsRes, ordersRes] = await Promise.all([
      api.get<Table[]>('/tables/'),
      api.get<Booking[]>('/bookings/'),
      api.get<Order[]>('/orders/', { params: { status: 'new,kitchen,ready', limit: 500 } })
    ])
    tables.value = tablesRes.data.filter((t) => t.is_active)
    orders.value = ordersRes.data.filter((o) => o.status !== 'cancelled')

    const now = new Date()
    const pastConfirmed = allBookingsRes.data.filter(
      (b) => b.status === 'confirmed' && new Date(b.starts_at).getTime() < now.getTime()
    )
    for (const b of pastConfirmed) {
      try {
        await api.patch(`/bookings/${b.id}`, { status: 'completed' })
      } catch (err) {
        console.error('Failed to auto-complete booking:', err)
      }
    }
    bookings.value = allBookingsRes.data.filter(
      (b) => b.status === 'confirmed' && new Date(b.starts_at).getTime() >= now.getTime()
    )

    liveText.value = 'live sync'
    liveClass.value = 'hero__chip--live'
  } catch (e) {
    liveText.value = 'нет связи'
    liveClass.value = 'hero__chip--error'
    console.error('Failed to load floor:', e)
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
      loadData()
    } else {
      progressRatio.value = elapsed / REFRESH_INTERVAL
    }
  }, 100)
}

onMounted(() => {
  loadData()
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

.floor-zone {
  margin-bottom: 1.75rem;
}

.floor-booking {
  margin-bottom: 1.75rem;
}

.floor-booking__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.floor-booking__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(220px, 100%), 1fr));
  gap: 1rem;
}

.floor-booking__actions {
  margin-top: 0.5rem;
}

.booking-capacity {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1rem 0 0;
  padding: 0.6rem 0.85rem;
  border-radius: 12px;
  font-size: 0.9rem;
  color: var(--muted);
  background: var(--overlay-04);
  border: 1px solid var(--border);
}

.booking-capacity--warn {
  color: var(--danger-soft);
  border-color: rgba(239, 68, 68, 0.4);
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  flex-shrink: 0;
  color: var(--text-control);
  background: var(--overlay-05);
  border: 1px solid var(--overlay-12);
  border-radius: 9px;
  cursor: pointer;
  transition: color 0.16s ease, background 0.16s ease, border-color 0.16s ease, transform 0.12s ease;
}

.icon-btn:hover {
  color: var(--text-strong);
  background: var(--overlay-09);
  border-color: var(--overlay-14);
}

.form-msg {
  align-self: center;
  font-size: 0.9rem;
}

.form-msg--ok {
  color: var(--success, #22c55e);
}

.form-msg--error {
  color: var(--danger, #ef4444);
}

.status-enter-active,
.status-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.status-enter-from,
.status-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.floor-zone__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.zone-summary {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: var(--overlay-04);
  border: 1px solid var(--border);
  white-space: nowrap;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(240px, 100%), 1fr));
  gap: 1rem;
  max-width: 100%;
}

.table-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.table-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-soft);
}

.table-card--busy {
  border-color: rgba(34, 197, 94, 0.45);
}

.table-card--booked {
  border-color: rgba(245, 158, 11, 0.45);
}

.table-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.table-card__num {
  font-weight: 700;
  font-size: 1.15rem;
}

.table-card__info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.table-card__bill,
.table-card__booking {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: 12px;
  background: var(--overlay-04);
  border: 1px solid var(--border);
}

.table-card__booking {
  flex-direction: column;
  align-items: stretch;
  gap: 0.6rem;
}

.table-card__booking-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.table-card__booking-actions .button {
  flex: 1;
  white-space: nowrap;
}

.table-card__ready {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  font-size: 0.88rem;
  font-weight: 700;
  color: #059669;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.35);
  animation: ready-pulse 1.8s ease-in-out infinite;
}

@keyframes ready-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.0);
  }
  50% {
    box-shadow: 0 0 0 5px rgba(16, 185, 129, 0.08);
  }
}

.table-card__bill-info {
  min-width: 0;
}

.table-card__sum {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--forest-light);
  white-space: nowrap;
}

.table-card__cta {
  width: 100%;
  margin-top: auto;
}

.empty-hint {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0.5rem 0 0;
}
</style>