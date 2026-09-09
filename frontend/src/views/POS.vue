<template>
  <div class="page">
    <section class="hero">
      <div>
        <h1 class="hero__title">Касса</h1>
        <p class="hero__lead">Быстрое создание заказа, поиск блюд и оплата без лишних кликов.</p>
      </div>
      <div class="hero__actions">
        <div class="hero__chip">
          <UiIcon name="zap" :size="14" />
          <span>Скорость · минимум действий</span>
        </div>
        <button class="button button--secondary button--sm" title="Обновить вручную" @click="refreshMenu">
          <svg class="progress-ring" width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
            <circle class="progress-ring__track" cx="9" cy="9" r="7" />
            <circle class="progress-ring__bar" cx="9" cy="9" r="7" :style="{ strokeDashoffset: progressOffset }" />
          </svg>
          <span>Обновить</span>
        </button>
      </div>
    </section>

    <section class="content-grid content-grid--two">
      <article class="glass panel panel--large">
        <div class="toolbar" style="margin-top: 0; margin-bottom: 1.25rem;">
          <div class="search-wrapper">
            <UiIcon name="search" :size="18" class="search-icon" />
            <input 
              v-model="query" 
              placeholder="Поиск блюда..." 
              class="input" 
              style="flex: 1; min-width: 280px; padding-left: 3rem;"
            />
          </div>
        </div>

        <div v-if="loading" class="list">
          <div v-for="n in 8" :key="n" class="skeleton" style="height: 8rem; border-radius: 24px;"></div>
        </div>

        <div v-else class="grid-cards grid-cards--3">
          <div 
            v-for="item in filtered" 
            :key="item.id" 
            class="glass-hover panel item" 
            style="cursor: pointer;"
            @click="addItem(item)"
          >
            <div class="item-image-wrapper">
              <div class="item-image">
                <img v-if="item.image" :src="item.image" :alt="item.name" />
              </div>
            </div>
            <div class="item-content">
              <div class="item__title">{{ item.name }}</div>
              <div class="item__sub">
                <span class="status-badge status-badge--neutral">{{ item.category || 'Без категории' }}</span>
              </div>
              <div class="item__meta">{{ formatPrice(item.price) }}</div>
            </div>
          </div>
        </div>
      </article>

      <aside class="glass panel panel--large">
        <div class="shift-panel">
          <div class="shift-panel__head">
            <span class="shift-panel__title">
              <UiIcon name="refresh" :size="16" />
              <span>Смена</span>
            </span>
            <span class="status-badge" :class="activeShift ? 'status-badge--success' : 'status-badge--neutral'">
              <span class="status-dot" />
              {{ activeShift ? 'Открыта' : 'Закрыта' }}
            </span>
          </div>

          <template v-if="activeShift">
            <div class="item__sub">Смена #{{ activeShift.id }} · с {{ formatShiftTime(activeShift.started_at) }}</div>
            <div class="shift-panel__row">
              <span>Выручка за смену</span>
              <strong>{{ formatPrice(activeShift.total_revenue) }}</strong>
            </div>
            <button class="button button--secondary button--sm shift-panel__action" :disabled="shiftBusy" @click="shiftClosingPanel = true">
              <UiIcon name="check-circle" :size="14" />
              <span>Закрыть смену</span>
            </button>
          </template>
          <template v-else>
            <div class="form-group shift-panel__open-form">
              <label class="form-label">Начальный остаток</label>
              <div class="shift-panel__open-row">
                <input v-model.number="openingBalance" class="input" type="number" min="0" step="0.01" placeholder="0.00" />
                <button class="button button--primary button--sm" :disabled="shiftBusy" @click="openShift">
                  <UiIcon name="zap" :size="14" />
                  <span>Открыть</span>
                </button>
              </div>
            </div>
          </template>
        </div>

        <h2 class="section-heading">
          <UiIcon name="receipt" :size="20" />
          <span>Чек</span>
        </h2>

        <div class="pos-options">
          <div class="form-group">
            <UiSelect
              v-model="selectedTableId"
              :options="tableOptions"
              label="Столик"
              placeholder="Без столика"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Способ оплаты</label>
            <div class="payment-methods">
              <button
                v-for="m in paymentMethods"
                :key="m.value"
                type="button"
                class="payment-btn"
                :class="{ 'payment-btn--active': selectedPayment === m.value }"
                @click="selectedPayment = m.value"
              >
                <span class="payment-btn__dot" :class="{ 'payment-btn__dot--on': selectedPayment === m.value }"></span>
                <span>{{ m.label }}</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="tableBill.length" class="bill-panel">
          <div class="bill-panel__top">
            <div>
              <div class="item__title">Счёт столика {{ selectedTableLabel }}</div>
              <div class="item__sub">
                {{ tableBill.length }} {{ pluralOrders(tableBill.length) }} · не оплачен
              </div>
            </div>
            <strong class="bill-panel__sum">{{ formatPrice(tableBillTotal) }}</strong>
          </div>
          <button
            type="button"
            class="button button--primary button--sm"
            style="width: 100%;"
            :disabled="tableBillPaying"
            @click="payTableBill"
          >
            <UiIcon name="check-circle" :size="16" />
            <span>Оплатить счёт столика</span>
          </button>
        </div>

        <Transition name="status">
          <div v-if="statusMsg" class="pos-status" :class="statusOk ? 'pos-status--ok' : 'pos-status--error'">
            <UiIcon :name="statusOk ? 'check-circle' : 'alert-circle'" :size="16" />
            <span>{{ statusMsg }}</span>
          </div>
        </Transition>

        <div class="cart-list" v-if="order.length > 0">
          <div 
            v-for="(item, index) in order" 
            :key="item.id" 
            class="cart-item"
          >
            <div class="cart-item-info">
              <div class="item__title">{{ item.name }}</div>
              <div class="item__sub">x{{ item.qty }} · {{ formatPrice(item.price) }}/{{ formatPrice(item.price * item.qty) }}</div>
            </div>
            <div class="cart-item-controls">
              <button 
                class="button button--ghost button--sm" 
                @click="updateQty(item.id, Math.max(1, item.qty - 1))"
              >
                <UiIcon name="minus" :size="14" />
              </button>
              <span class="cart-qty">{{ item.qty }}</span>
              <button 
                class="button button--ghost button--sm" 
                @click="updateQty(item.id, item.qty + 1)"
              >
                <UiIcon name="plus" :size="14" />
              </button>
            </div>
          </div>
        </div>

        <div v-else class="empty-cart">
          <div class="empty-cart-icon">
            <UiIcon name="shopping-cart" :size="48" style="color: var(--muted);" />
          </div>
          <p class="empty-cart-text">Корзина пуста</p>
          <p class="empty-cart-subtext">Выберите блюда слева для создания заказа</p>
        </div>

        <div class="cart-footer">
          <div class="cart-total">
            <span>Итого</span>
            <strong class="accent">{{ formatPrice(total) }}</strong>
          </div>
          <div class="cart-footer__actions">
            <button
              class="button button--secondary button--lg"
              style="flex: 1;"
              :disabled="order.length === 0"
              @click="sendToKitchen"
            >
              <UiIcon name="zap" :size="18" />
              <span>На кухню</span>
            </button>
            <button
              class="button button--primary button--lg"
              style="flex: 1;"
              :disabled="order.length === 0"
              @click="pay"
            >
              <UiIcon name="check-circle" :size="18" />
              <span>Оплатить</span>
            </button>
          </div>
        </div>
      </aside>
    </section>

    <div v-if="shiftClosingPanel" class="shift-modal">
      <div class="shift-modal__card glass panel panel--large">
        <div class="shift-modal__head">
          <h3 class="section-heading section-heading--compact">
            <UiIcon name="refresh" :size="18" />
            <span>Z-отчёт · закрытие смены</span>
          </h3>
          <button type="button" class="shift-modal__close" title="Закрыть" @click="shiftClosingPanel = false">
            <UiIcon name="x" :size="16" />
          </button>
        </div>

        <div class="shift-modal__grid">
          <div class="shift-modal__key">
            <span class="item__sub">Смена открыта</span>
            <strong>{{ activeShift ? formatShiftTime(activeShift.started_at) : '—' }}</strong>
          </div>
          <div class="shift-modal__key">
            <span class="item__sub">Начальный остаток</span>
            <strong>{{ formatPrice(activeShift?.opening_balance || 0) }}</strong>
          </div>
          <div class="shift-modal__key">
            <span class="item__sub">Оплачено чеков</span>
            <strong>{{ activeShift?.orders_count ?? 0 }}</strong>
          </div>
          <div class="shift-modal__key">
            <span class="item__sub">Выручка за смену</span>
            <strong class="accent">{{ formatPrice(activeShift?.total_revenue || 0) }}</strong>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Остаток в кассе</label>
          <input v-model.number="closingBalance" class="input" type="number" min="0" step="0.01" placeholder="Ожидается: 0.00" />
        </div>
        <p v-if="expectedCash" class="shift-modal__expected">
          Ожидаемые деньги: <strong>{{ formatPrice(expectedCash) }}</strong>
        </p>

        <div class="shift-modal__actions">
          <button type="button" class="button button--secondary" @click="printZReport">
            <UiIcon name="receipt" :size="16" />
            <span>Печать Z-отчёта</span>
          </button>
          <button type="button" class="button button--ghost" @click="shiftClosingPanel = false">
            <UiIcon name="x" :size="16" />
            <span>Отмена</span>
          </button>
          <button type="button" class="button button--primary" :disabled="shiftBusy" @click="closeShift">
            <UiIcon name="check-circle" :size="16" />
            <span>{{ shiftBusy ? 'Закрываем…' : 'Закрыть смену' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import UiSelect from '../components/UiSelect.vue'
import { tableLabel } from '../lib/tableLabel'
import { useAppStore } from '../stores'
import type { SelectOption } from '../components/UiSelect.vue'

interface MenuItem {
  id: number
  name: string
  price: number
  category?: string
  image?: string
}

interface CartItem extends MenuItem {
  qty: number
}

interface Table {
  id: number
  number: string
  name?: string
  seats: number
  zone?: string
  is_active: boolean
}

interface TableOrder {
  id: number
  total: number
  status: string
}

interface ShiftOut {
  id: number
  started_at?: string
  ended_at?: string
  status: string
  opening_balance: number
  closing_balance?: number | null
  expected_cash?: number | null
  notes?: string | null
  orders_count: number
  total_revenue: number
}

interface ReceiptRow {
  name: string
  qty: number
  price: number
}

const route = useRoute()
const appStore = useAppStore()

const items = ref<MenuItem[]>([])
const loading = ref(true)
const query = ref('')
const order = ref<CartItem[]>([])

const tables = ref<Table[]>([])
const selectedTableId = ref<number | null>(null)
const selectedPayment = ref('cash')
const paymentMethods = [
  { value: 'cash', label: 'Наличные' },
  { value: 'card', label: 'Карта' },
  { value: 'other', label: 'Другое' }
]
const statusMsg = ref('')
const statusOk = ref(true)
let statusTimer: ReturnType<typeof setTimeout> | null = null

const tableBill = ref<TableOrder[]>([])
const tableBillPaying = ref(false)

const activeShift = ref<ShiftOut | null>(null)
const shiftBusy = ref(false)
const shiftClosingPanel = ref(false)
const openingBalance = ref(0)
const closingBalance = ref(0)

const expectedCash = computed(() => {
  if (!activeShift.value) return 0
  return (activeShift.value.opening_balance || 0) + (activeShift.value.total_revenue || 0)
})

const formatPrice = (price: number): string => {
  return price.toLocaleString('ru-RU') + ' ₸'
}

const pluralOrders = (n: number): string => {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'чек'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'чека'
  return 'чеков'
}

async function loadMenu() {
  loading.value = true
  try {
    const res = await api.get<MenuItem[]>('/menu/')
    items.value = res.data
  } catch (e) {
    console.error('Failed to load menu:', e)
  } finally {
    loading.value = false
  }
}

function refreshMenu() {
  resetCountdown()
  loadMenu()
  loadTables()
}

const REFRESH_INTERVAL = 10000
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
      refreshMenu()
    } else {
      progressRatio.value = elapsed / REFRESH_INTERVAL
    }
  }, 100)
}

const filtered = computed(() => {
  const q = query.value.toLowerCase()
  return items.value.filter(i => i.name.toLowerCase().includes(q))
})

function addItem(item: MenuItem) {
  const found = order.value.find(x => x.id === item.id)
  if (found) {
    found.qty++
  } else {
    order.value.push({ ...item, qty: 1 })
  }
}

function updateQty(id: number, qty: number) {
  const item = order.value.find(x => x.id === id)
  if (item) {
    item.qty = qty
  }
}

const total = computed(() => {
  return order.value.reduce((sum, item) => sum + item.price * item.qty, 0)
})

const tableBillTotal = computed(() => {
  return tableBill.value.reduce((sum, o) => sum + (o.total || 0), 0)
})

const tableOptions = computed<SelectOption[]>(() => [
  { value: null, label: 'Без столика' },
  ...tables.value.map((t) => ({ value: t.id, label: tableLabel(t) }))
])

const selectedTableLabel = computed(() => {
  const t = tables.value.find(x => x.id === selectedTableId.value)
  return t ? tableLabel(t) : ''
})

async function loadTableBill(tableId: number | null) {
  tableBill.value = []
  if (!tableId) return
  try {
    const res = await api.get<TableOrder[]>('/orders/', {
      params: { status: 'new,kitchen,ready', table_id: tableId }
    })
    tableBill.value = res.data.filter(o => o.status !== 'cancelled')
  } catch (e) {
    console.error('Failed to load table bill:', e)
  }
}

async function payTableBill() {
  if (!tableBill.value.length) return
  tableBillPaying.value = true
  const paidBill = tableBill.value.map(o => o.id)
  const table = selectedTableLabel.value
  const method = paymentLabel(selectedPayment.value)
  const total = tableBillTotal.value
  try {
    await Promise.all(tableBill.value.map(o =>
      api.patch(`/orders/${o.id}/status`, { status: 'paid', payment_method: selectedPayment.value })
    ))
    tableBill.value = []
    order.value = []
    showStatus('Счёт столика оплачен', true)

    const rows: ReceiptRow[] = []
    for (const id of paidBill) {
      try {
        const r = await api.get<{ items?: Array<{ name?: string | null; qty: number; price: number; menu_item_id: number }> }>(`/orders/${id}`)
        for (const it of r.data.items || []) {
          rows.push({ name: it.name || 'Позиция №' + it.menu_item_id, qty: it.qty, price: it.price })
        }
      } catch (e) {
        console.error('Failed to load order for receipt:', e)
      }
    }
    printReceipt({
      title: 'Счёт столика',
      table: table || 'Без столика',
      rows,
      total,
      method,
      createdAt: nowLabel()
    })
  } catch (e) {
    console.error('Failed to pay table bill:', e)
    showStatus('Ошибка при оплате счёта. Попробуйте снова.', false)
  } finally {
    tableBillPaying.value = false
  }
}

function sendToKitchen() {
  if (order.value.length === 0) return
  createOrder('new')
}

async function createOrder(status: 'new' | 'paid'): Promise<boolean> {
  const tableId = selectedTableId.value ?? null
  try {
    await api.post('/orders/', {
      items: order.value.map(i => ({ menu_item_id: i.id, qty: i.qty })),
      table_id: tableId,
      payment_method: status === 'paid' ? selectedPayment.value : null
    })

    order.value = []
    if (status === 'paid') {
      selectedTableId.value = null
      showStatus('Заказ оплачен успешно!', true)
    } else {
      showStatus('Заказ передан на кухню', true)
      if (tableId) loadTableBill(tableId)
    }
    return true
  } catch (e) {
    console.error('Failed to create order:', e)
    showStatus(status === 'paid' ? 'Ошибка при оплате. Попробуйте снова.' : 'Ошибка при отправке заказа.', false)
    return false
  }
}

async function loadTables() {
  try {
    const r = await api.get<Table[]>('/tables/')
    tables.value = r.data.filter((t) => t.is_active)
  } catch (e) {
    console.error('Failed to load tables:', e)
    tables.value = []
  }
}

function showStatus(msg: string, ok: boolean) {
  statusMsg.value = msg
  statusOk.value = ok
  if (statusTimer) clearTimeout(statusTimer)
  statusTimer = setTimeout(() => { statusMsg.value = '' }, 3000)
}

async function pay() {
  if (order.value.length === 0) return
  const rows = order.value.map(i => ({ name: i.name, qty: i.qty, price: i.price }))
  const table = selectedTableLabel.value
  const method = paymentLabel(selectedPayment.value)
  const total = total.value
  const ok = await createOrder('paid')
  if (ok) {
    printReceipt({ title: 'Чек', table: table || 'Без столика', rows, total, method, createdAt: nowLabel() })
  }
}

function paymentLabel(value: string): string {
  if (value === 'cash') return 'Наличные'
  if (value === 'card') return 'Карта'
  return 'Другое'
}

function formatShiftTime(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function nowLabel(): string {
  return new Date().toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function operatorName(): string {
  return appStore.user?.full_name || appStore.user?.email || 'Касса'
}

function escHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string))
}

function money(n: number): string {
  return n.toLocaleString('ru-RU', { maximumFractionDigits: 2 }) + ' ₸'
}

function receiptHtml(o: {
  title: string
  table: string
  createdAt: string
  rows: ReceiptRow[]
  total: number
  method: string
}): string {
  const rows = o.rows.map(r =>
    `<div class="r"><span>${escHtml(r.name)}${r.qty > 1 ? ' ×' + r.qty : ''}</span><span>${money(r.price * r.qty)}</span></div>`
  ).join('')
  return `<!doctype html><html><head><meta charset="utf-8"><title>${escHtml(o.title)}</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 16px; width: 300px; font: 12px/1.55 'Consolas','Courier New',monospace; color: #000; }
  .c { text-align: center; font-weight: 700; font-size: 16px; }
  .s { text-align: center; margin: 2px 0 8px; }
  .m { display: flex; justify-content: space-between; gap: 12px; margin: 1px 0; }
  .line { border-top: 1px dashed #000; margin: 8px 0; }
  .r { display: flex; justify-content: space-between; gap: 12px; }
  .t { display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; margin-top: 2px; }
  .f { margin-top: 10px; text-align: center; color: #333; }
</style></head><body>
  <div class="c">CAFE</div>
  <div class="s">${escHtml(o.title)}</div>
  <div class="m"><span>Столик</span><span>${escHtml(o.table)}</span></div>
  <div class="m"><span>Время</span><span>${escHtml(o.createdAt)}</span></div>
  <div class="line"></div>
  ${rows}
  <div class="t"><span>ИТОГО</span><span>${money(o.total)}</span></div>
  <div class="m"><span>Оплата</span><span>${escHtml(o.method)}</span></div>
  <div class="m"><span>Кассир</span><span>${escHtml(operatorName())}</span></div>
  <div class="f">Спасибо за визит!</div>
</body></html>`
}

function printHtml(html: string) {
  const w = window.open('', '_blank', 'width=360,height=640')
  if (!w) {
    alert('Разрешите всплывающие окна, чтобы напечатать чек')
    return
  }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 300)
}

function printReceipt(o: { title: string; table: string; createdAt: string; rows: ReceiptRow[]; total: number; method: string }) {
  printHtml(receiptHtml(o))
}

function printZReport(s: ShiftOut = activeShift.value ?? null) {
  if (!s) return
  const b = (k: string, v: string) => `<div class="m"><span>${escHtml(k)}</span><span>${escHtml(v)}</span></div>`
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>Z-отчёт</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 16px; width: 300px; font: 12px/1.55 'Consolas','Courier New',monospace; color: #000; }
  .c { text-align: center; font-weight: 700; font-size: 16px; }
  .s { text-align: center; margin: 2px 0 8px; }
  .m { display: flex; justify-content: space-between; gap: 12px; margin: 1px 0; }
  .line { border-top: 1px dashed #000; margin: 8px 0; }
  .f { margin-top: 10px; text-align: center; color: #333; }
</style></head><body>
  <div class="c">CAFE</div>
  <div class="s">Z-отчёт · смена #${s.id}</div>
  <div class="m"><span>Время</span><span>${nowLabel()}</span></div>
  <div class="m"><span>Оператор</span><span>${escHtml(operatorName())}</span></div>
  <div class="line"></div>
  ${b('Смена открыта', formatShiftTime(s.started_at))}
  ${b('Начальный остаток', money(s.opening_balance || 0))}
  ${b('Оплачено чеков', String(s.orders_count ?? 0))}
  ${b('Выручка', money(s.total_revenue || 0))}
  ${b('Ожидаемые деньги', money((s.opening_balance || 0) + (s.total_revenue || 0)))}
  <div class="line"></div>
  <div class="f">Смена закрыта</div>
</body></html>`
  printHtml(html)
}

async function loadActiveShift() {
  try {
    const res = await api.get<ShiftOut | null>('/shifts/me/active')
    activeShift.value = res.data
  } catch (e) {
    console.error('Failed to load active shift:', e)
    activeShift.value = null
  }
}

async function openShift() {
  shiftBusy.value = true
  try {
    const res = await api.post<ShiftOut>('/shifts/open', { opening_balance: openingBalance.value || 0 })
    activeShift.value = res.data
    showStatus('Смена открыта', true)
  } catch (e) {
    console.error('Failed to open shift:', e)
    showStatus('Ошибка при открытии смены', false)
  } finally {
    shiftBusy.value = false
  }
}

async function closeShift() {
  if (!activeShift.value) return
  shiftBusy.value = true
  try {
    const res = await api.post<ShiftOut>('/shifts/close', { closing_balance: closingBalance.value || 0 })
    activeShift.value = null
    shiftClosingPanel.value = false
    closingBalance.value = 0
    showStatus('Смена закрыта · Z-отчёт сформирован', true)
    printZReport(res.data)
  } catch (e) {
    console.error('Failed to close shift:', e)
    showStatus('Ошибка при закрытии смены', false)
  } finally {
    shiftBusy.value = false
  }
}

watch(selectedTableId, (id) => {
  loadTableBill(id)
})

onMounted(async () => {
  loadMenu()
  await loadTables()
  startAutoRefresh()
  loadActiveShift()

  const tableId = Number(route.query.table)
  if (tableId && tables.value.some(t => t.id === tableId)) {
    selectedTableId.value = tableId
  } else if (tableId) {
    loadTableBill(tableId)
    selectedTableId.value = tableId
  }
})

onUnmounted(() => {
  if (statusTimer) clearTimeout(statusTimer)
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

.search-wrapper {
  position: relative;
  flex: 1;
  min-width: 280px;
}

.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(245, 245, 245, 0.5);
}

.item {
  display: flex;
  gap: 1.25rem;
  align-items: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.item:hover {
  transform: translateY(-2px);
}

.item-image-wrapper {
  width: 5.5rem;
  height: 5.5rem;
  border-radius: 20px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--surface);
}

.item-image {
  width: 100%;
  height: 100%;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.item-content .item__title {
  margin-bottom: 0.35rem;
}

.cart-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 0.4rem;
}

.cart-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 20px;
  background: var(--item-bg);
  border: 1px solid var(--border);
}

.cart-item-info {
  flex: 1;
}

.cart-qty {
  font-weight: 600;
  color: var(--text-control);
  min-width: 2rem;
  text-align: center;
}

.cart-footer {
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cart-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1rem;
}

.cart-total strong {
  font-size: 1.35rem;
}

.empty-cart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: var(--muted);
}

.empty-cart-icon {
  margin-bottom: 1rem;
}

.empty-cart-text {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.empty-cart-subtext {
  font-size: 0.9rem;
}

.pos-options {
  display: grid;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.bill-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1.25rem;
  border-radius: 20px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.bill-panel__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.bill-panel__sum {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--forest-light);
  white-space: nowrap;
}

.cart-footer__actions {
  display: flex;
  gap: 0.65rem;
}

.payment-methods {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.payment-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.9rem;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-control);
  cursor: pointer;
  background: var(--control-bg);
  border: 1px solid var(--border);
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.payment-btn:hover {
  background: var(--control-bg-hover);
}

.payment-btn--active {
  border-color: var(--forest-mid);
  color: var(--text-strong);
}

.payment-btn__dot {
  width: 0.6rem;
  height: 0.6rem;
  border-radius: 50%;
  border: 2px solid var(--control-arrow);
  transition: background 0.18s ease, border-color 0.18s ease;
}

.payment-btn__dot--on {
  background: var(--forest-mid);
  border-color: var(--forest-mid);
}

.pos-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 0.9rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.pos-status--ok {
  color: var(--forest-dark);
  background: rgba(34, 197, 94, 0.14);
  border: 1px solid rgba(34, 197, 94, 0.35);
}

.pos-status--error {
  color: var(--danger-soft);
  background: rgba(239, 68, 68, 0.14);
  border: 1px solid rgba(239, 68, 68, 0.35);
}

.status-enter-active,
.status-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.status-enter-from,
.status-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.shift-panel {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.75rem;
  margin-bottom: 1.25rem;
  border-radius: 14px;
  background: var(--overlay-04);
  border: 1px solid var(--border);
}

.shift-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.shift-panel__title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-weight: 700;
  font-size: 0.92rem;
}

.shift-panel__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.shift-panel__action,
.shift-panel__open {
  width: 100%;
  justify-content: center;
}

.shift-panel__open-form {
  margin: 0;
}

.shift-panel__open-row {
  display: flex;
  gap: 0.5rem;
}

.shift-panel__open-row .input {
  flex: 1;
  min-width: 0;
}

.shift-modal {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.55);
}

.shift-modal__card {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.shift-modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.shift-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  border: 1px solid var(--border);
  background: var(--overlay-05);
  color: var(--muted);
  cursor: pointer;
  transition: 0.15s;
}

.shift-modal__close:hover {
  color: var(--danger);
  border-color: rgba(239, 68, 68, 0.4);
}

.shift-modal__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.shift-modal__key {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: var(--overlay-04);
  border: 1px solid var(--border);
}

.shift-modal__expected {
  font-size: 0.9rem;
}

.shift-modal__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.shift-modal__actions .button {
  flex: 1;
  justify-content: center;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .item-image-wrapper {
    width: 4.5rem;
    height: 4.5rem;
  }
}
</style>
