<template>
  <div class="page">
    <section class="hero">
      <div>
        <h1 class="hero__title">Касса</h1>
        <p class="hero__lead">Быстрое создание заказа, поиск блюд и оплата без лишних кликов.</p>
      </div>
      <div class="hero__chip">
        <UiIcon name="zap" :size="14" />
        <span>Скорость · минимум действий</span>
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
          <button class="button button--secondary" @click="refreshMenu">
            <UiIcon name="refresh" :size="16" />
            <span>Обновить</span>
          </button>
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
        <h2 class="section-heading">
          <UiIcon name="receipt" :size="20" />
          <span>Чек</span>
        </h2>

        <div class="pos-options">
          <div class="form-group">
            <label class="form-label">Столик</label>
            <select v-model="selectedTableId" class="input">
              <option :value="null">Без столика</option>
              <option v-for="t in tables" :key="t.id" :value="t.id">
                №{{ t.number }}{{ t.name ? ' · ' + t.name : '' }}
              </option>
            </select>
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
          <button 
            class="button button--primary button--lg" 
            style="width: 100%;"
            :disabled="order.length === 0"
            @click="pay"
          >
            <UiIcon name="check-circle" :size="20" />
            <span>Оплатить</span>
          </button>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'

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

const formatPrice = (price: number): string => {
  return price.toLocaleString('ru-RU') + ' ₽'
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
  loadMenu()
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

  try {
    await api.post('/orders/', {
      items: order.value.map(i => ({ menu_item_id: i.id, qty: i.qty })),
      table_id: selectedTableId.value ?? null,
      payment_method: selectedPayment.value
    })
    
    order.value = []
    selectedTableId.value = null
    showStatus('Заказ оплачен успешно!', true)
  } catch (e) {
    console.error('Payment failed:', e)
    showStatus('Ошибка при оплате. Попробуйте снова.', false)
  }
}

onMounted(() => {
  loadMenu()
  loadTables()
})

onUnmounted(() => {
  if (statusTimer) clearTimeout(statusTimer)
})
</script>

<style scoped>
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

@media (max-width: 768px) {
  .item-image-wrapper {
    width: 4.5rem;
    height: 4.5rem;
  }
}
</style>
