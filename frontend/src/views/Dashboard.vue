<template>
  <div class="page">
    <CashierDashboard v-if="isCashier" />

    <template v-else>
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="dashboard" :size="16" />
          <span>Центр управления</span>
        </div>
        <h1 class="hero__title">{{ greeting }}, {{ userName }}</h1>
        <p class="hero__lead">
          Оперативный обзор выручки, нагрузки и продаж в реальном времени.
        </p>
      </div>
      <div class="hero__actions">
        <div class="hero__chip hero__chip--live">
          <span class="live-dot" />
          <span>Live sync</span>
        </div>
      </div>
    </section>

    <section v-if="showMetrics" class="grid-cards grid-cards--4 dashboard-metrics">
      <article
        v-for="metric in metrics"
        :key="metric.label"
        class="glass panel metric"
      >
        <div class="metric__icon" :class="metric.iconClass">
          <UiIcon :name="metric.icon" :size="18" />
        </div>
        <p class="metric__label">{{ metric.label }}</p>
        <h3 class="metric__value">{{ metric.value }}</h3>
        <p class="metric__meta" :class="metric.metaClass">
          <UiIcon v-if="metric.trendIcon" :name="metric.trendIcon" :size="14" />
          <span>{{ metric.meta }}</span>
        </p>
      </article>
    </section>

    <section v-if="showMetrics" class="glass panel panel--large goal-panel">
      <div class="goal-panel__top">
        <div class="goal-panel__info">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="spark" :size="20" />
            <span>Цель на месяц</span>
          </h2>
          <p class="goal-panel__subtitle">{{ goalRevenue }} из {{ goalTarget }}</p>
        </div>
        <span class="goal-panel__pct">{{ goalPercent }}%</span>
      </div>
      <div class="goal-bar">
        <div class="goal-bar__fill" :style="{ width: Math.min(goalPercent, 100) + '%' }"></div>
      </div>
    </section>

    <section class="content-grid content-grid--two">
      <article class="glass panel panel--large chart-card">
        <div class="chart-card__header">
          <div>
            <h2 class="section-heading section-heading--compact">
              <UiIcon name="analytics" :size="20" />
              <span>Динамика выручки</span>
            </h2>
            <p class="chart-card__subtitle">Сравнение по дням недели</p>
          </div>
          <div class="period-tabs">
            <button
              v-for="period in periods"
              :key="period.id"
              class="period-tabs__btn"
              :class="{ 'period-tabs__btn--active': activePeriod === period.id }"
              @click="activePeriod = period.id"
            >
              {{ period.label }}
            </button>
          </div>
        </div>
        <div id="chart" class="chart-card__canvas" />
      </article>

      <article class="glass panel panel--large chart-card">
        <div class="chart-card__header">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="coffee" :size="20" />
            <span>Выручка по категориям</span>
          </h2>
        </div>
        <div id="category-chart" class="chart-card__canvas" />
      </article>
    </section>

    <section class="content-grid content-grid--three">
      <aside class="glass panel panel--large">
        <h2 class="section-heading section-heading--compact">
          <UiIcon name="food" :size="20" />
          <span>Топ блюд</span>
        </h2>
        <div v-if="topItems.length" class="list top-list">
          <div v-for="(item, idx) in topItems" :key="item.name" class="item top-item">
            <span class="top-item__rank">{{ idx + 1 }}</span>
            <div class="top-item__body">
              <div class="item__title">{{ item.name }}</div>
              <div class="top-item__bar">
                <div class="top-item__bar-fill" :style="{ width: topPct(item) + '%' }"></div>
              </div>
            </div>
            <span class="top-item__qty">{{ item.qty }}×</span>
          </div>
        </div>
        <p v-else class="empty-hint">Пока нет продаж</p>
      </aside>

      <aside class="glass panel panel--large">
        <h2 class="section-heading section-heading--compact">
          <UiIcon name="zap" :size="20" />
          <span>Пик загрузки</span>
        </h2>
        <p v-if="peakHourLabel" class="peak-hour__value">{{ peakHourLabel }}</p>
        <p v-else class="empty-hint">Сегодня продаж ещё нет</p>
        <p v-if="revenueByHour.length" class="peak-hour__sub">Самый загруженный час по выручке</p>
      </aside>

      <aside v-if="showActivity" class="glass panel panel--large activity-panel">
        <div class="activity-panel__header">
          <h2 class="section-heading section-heading--compact">
            <UiIcon name="activity" :size="20" />
            <span>Сейчас в работе</span>
          </h2>
          <span class="status-badge" :class="liveStatusClass">
            <span class="status-dot" />
            {{ liveStatusText }}
          </span>
        </div>
        <div class="list activity-list">
          <div v-for="o in liveOrders" :key="o.key" class="item activity-item">
            <div class="activity-item__top">
              <div class="item__title">
                <UiIcon name="pos" :size="16" />
                <span>Заказ #{{ o.id }}</span>
              </div>
              <span class="activity-item__time">только что</span>
            </div>
            <div class="item__sub">{{ formatCurrency(o.total) }}</div>
          </div>
          <div v-for="item in activityItems" :key="item.title" class="item activity-item">
            <div class="activity-item__top">
              <div class="item__title">
                <UiIcon :name="item.icon" :size="16" />
                <span>{{ item.title }}</span>
              </div>
              <span class="activity-item__time">{{ item.time }}</span>
            </div>
            <div class="item__sub">{{ item.sub }}</div>
          </div>
        </div>
      </aside>
    </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAppStore } from '../stores'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import CashierDashboard from '../components/CashierDashboard.vue'
import { chartThemeColors, watchThemeChange } from '../composables/useChartTheme'
import { wsUrl } from '../ws'

const appStore = useAppStore()

const isCashier = computed(() => appStore.user?.role === 'cashier')

const showMetrics = computed(() => appStore.dashboardPreferences.show_metrics !== false)
const showActivity = computed(() => appStore.dashboardPreferences.show_activity !== false)

const userName = computed(() => {
  const name = appStore.user?.full_name || appStore.user?.email || 'команда'
  return name.split(' ')[0]
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Доброе утро'
  if (hour < 18) return 'Добрый день'
  return 'Добрый вечер'
})

const metrics = ref([
  {
    label: 'Выручка за день',
    value: '₸0',
    meta: 'Загрузка…',
    icon: 'analytics',
    iconClass: 'metric__icon--green',
    metaClass: 'metric__meta--up',
    trendIcon: 'trending-up'
  },
  {
    label: 'Выручка за месяц',
    value: '₸0',
    meta: 'Цель: 0%',
    icon: 'dashboard',
    iconClass: 'metric__icon--olive',
    metaClass: 'metric__meta--up',
    trendIcon: 'trending-up'
  },
  {
    label: 'Заказы',
    value: '0',
    meta: 'Сегодня',
    icon: 'pos',
    iconClass: 'metric__icon--coffee',
    metaClass: '',
    trendIcon: null
  },
  {
    label: 'Средний чек',
    value: '₸0',
    meta: 'По продажам за сегодня',
    icon: 'inventory',
    iconClass: 'metric__icon--earth',
    metaClass: 'metric__meta--up',
    trendIcon: 'trending-up'
  }
])

const formatCurrency = (n: number): string => {
  if (n >= 1000000) return '₸' + (n / 1000000).toFixed(2).replace('.', ',') + 'M'
  if (n >= 1000) return '₸' + Math.round(n).toLocaleString('ru-RU')
  return '₸' + Math.round(n).toLocaleString('ru-RU')
}

async function loadStats() {
  try {
    const res = await api.get('/dashboard/stats')
    const s = res.data

    metrics.value = [
      {
        label: 'Выручка за день',
        value: formatCurrency(s.revenue_today),
        meta: `Всего: ${formatCurrency(s.revenue_all)}`,
        icon: 'analytics',
        iconClass: 'metric__icon--green',
        metaClass: 'metric__meta--up',
        trendIcon: 'trending-up'
      },
      {
        label: 'Выручка за месяц',
        value: formatCurrency(s.revenue_month),
        meta: `Цель: ${s.month_goal_pct}%`,
        icon: 'dashboard',
        iconClass: 'metric__icon--olive',
        metaClass: 'metric__meta--up',
        trendIcon: 'trending-up'
      },
      {
        label: 'Заказы',
        value: String(s.orders_today),
        meta: `Всего: ${s.orders_total}`,
        icon: 'pos',
        iconClass: 'metric__icon--coffee',
        metaClass: '',
        trendIcon: null
      },
      {
        label: 'Средний чек',
        value: formatCurrency(s.avg_check),
        meta: 'По продажам за сегодня',
        icon: 'inventory',
        iconClass: 'metric__icon--earth',
        metaClass: 'metric__meta--up',
        trendIcon: 'trending-up'
      }
    ]

    const hasData = s.week_values.some((v: number) => v > 0) || s.month_values.some((v: number) => v > 0)
    if (hasData) {
      chartData.value = {
        week: { labels: s.week_labels, values: s.week_values },
        month: { labels: s.month_labels, values: s.month_values }
      }
      updateChart()
    }

    goalPercent.value = s.month_goal_pct
    goalRevenue.value = formatCurrency(s.revenue_month)
    goalTarget.value = formatCurrency(s.month_goal)

    const maxTop = s.top_items.length ? Math.max(...s.top_items.map((t: { qty: number }) => t.qty)) : 1
    topItems.value = s.top_items.map((t: { name: string; qty: number }) => ({
      name: t.name,
      qty: t.qty,
      pct: Math.round((t.qty / maxTop) * 100)
    }))

    revenueByHour.value = s.revenue_by_hour || []
    if (s.revenue_by_category && s.revenue_by_category.length) {
      lastCategoryData = s.revenue_by_category
      renderCategoryChart(lastCategoryData)
    }

    if (liveOrders.value.length) {
      liveOrders.value = liveOrders.value.slice(0, 5)
    }

    const activity: Array<Record<string, unknown>> = []
    if (s.low_stock.length) {
      activity.push({
        title: 'Склад',
        sub: `${s.low_stock.length} поз. требуют пополнения`,
        icon: 'inventory',
        time: 'внимание'
      })
    }
    if (s.top_items.length) {
      const top = s.top_items[0]
      activity.push({
        title: 'Популярное блюдо',
        sub: `${top.name} — ${top.qty} × продаж`,
        icon: 'food',
        time: 'лидер продаж'
      })
    }
    if (activity.length) {
      activityItems.value = activity
    } else {
      activityItems.value = []
    }
  } catch (e) {
    console.error('Failed to load dashboard stats:', e)
  }
}

const periods = [
  { id: 'week', label: 'Неделя' },
  { id: 'month', label: 'Месяц' }
]

const activePeriod = ref('week')

const chartData = ref({
  week: {
    labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
    values: [120, 200, 150, 80, 70, 110, 130]
  },
  month: {
    labels: ['1', '5', '10', '15', '20', '25', '30'],
    values: [90, 140, 160, 120, 180, 210, 195]
  }
})

const activityItems = ref<Array<{ title: string; sub: string; icon: string; time: string }>>([])

const goalRevenue = ref('₸0')
const goalTarget = ref('₸500 000')
const goalPercent = ref(0)
const topItems = ref<Array<{ name: string; qty: number; pct: number }>>([])
const revenueByHour = ref<Array<{ label: string; value: number }>>([])
const peakHourLabel = computed(() => {
  if (!revenueByHour.value.length) return ''
  const peak = revenueByHour.value.reduce((a, b) => (b.value > a.value ? b : a))
  return peak.value > 0 ? peak.label : ''
})
const liveOrders = ref<Array<{ id: number; total: number; key: number }>>([])
const liveStatusText = ref('live sync')
const liveStatusClass = ref('status-badge--success')
let ws: WebSocket | null = null
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
let wsKey = 0

function connectWebSocket() {
  const socket = new WebSocket(wsUrl('/ws/orders'))
  ws = socket

  socket.onopen = () => {
    liveStatusText.value = 'live sync'
    liveStatusClass.value = 'status-badge--success'
  }

  socket.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data)
      if (data && typeof data.order_id === 'number') {
        wsKey += 1
        liveOrders.value = [
          { id: data.order_id, total: data.total ?? 0, key: wsKey },
          ...liveOrders.value
        ].slice(0, 5)
      }
    } catch {
      // ignore malformed frames
    }
  }

  socket.onclose = () => {
    liveStatusText.value = 'offline'
    liveStatusClass.value = 'status-badge--danger'
    if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
    wsReconnectTimer = setTimeout(() => {
      if (document.visibilityState !== 'hidden') connectWebSocket()
    }, 5000)
  }

  socket.onerror = () => socket.close()
}

function disconnectWebSocket() {
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
  ws?.close()
  ws = null
}

function topPct(item: { pct: number }): number {
  return Math.max(item.pct, 4)
}

function buildChartOption(period: 'week' | 'month') {
  const data = chartData.value[period]
  const c = chartThemeColors()
  const el = document.getElementById('chart')
  const narrow = el ? el.clientWidth < 420 : false
  const dense = data.labels.length > 9
  return {
    grid: { left: 8, right: 16, top: 16, bottom: 12, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: c.tooltipBg,
      borderWidth: 0,
      padding: [10, 14],
      textStyle: { color: c.tooltipText, fontSize: 12 },
      extraCssText: `box-shadow: ${c.tooltipShadow}; border-radius: 8px;`
    },
    xAxis: {
      type: 'category',
      data: data.labels,
      axisLine: { lineStyle: { color: c.axis } },
      axisLabel: {
        color: c.label,
        fontSize: narrow ? 10 : 12,
        padding: [4, 0, 0, 0],
        interval: dense ? Math.ceil(data.labels.length / (narrow ? 5 : 8)) : 0
      },
      splitLine: { lineStyle: { color: c.split } }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: c.split } },
      axisLabel: { color: c.label, fontSize: narrow ? 10 : 12 },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [{
      data: data.values,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: narrow ? 5 : 8,
      lineStyle: {
        width: 3,
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#22c55e' },
          { offset: 1, color: '#16a34a' }
        ])
      },
      itemStyle: {
        color: '#22c55e',
        borderColor: c.border,
        borderWidth: 3
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(34, 197, 94, 0.25)' },
          { offset: 1, color: 'rgba(34, 197, 94, 0.02)' }
        ])
      },
      emphasis: { focus: 'series' }
    }]
  }
}

function updateChart() {
  if (!chartInstance) return
  chartInstance.setOption(buildChartOption(activePeriod.value as 'week' | 'month'), true)
}

function renderCategoryChart(data: Array<{ label: string; value: number }>) {
  if (!categoryChartInstance) {
    const el = document.getElementById('category-chart')
    if (!el) return
    categoryChartInstance = echarts.init(el)
  }
  const c = chartThemeColors()
  const catEl = document.getElementById('category-chart')
  const narrow = catEl ? catEl.clientWidth < 380 : false
  categoryChartInstance.setOption({
    color: ['#22c55e', '#4ade80', '#86efac', '#16a34a', '#15803d', '#65a30d', '#3f6212'],
    tooltip: {
      trigger: 'item',
      backgroundColor: c.tooltipBg,
      borderWidth: 0,
      textStyle: { color: c.tooltipText, fontSize: 12 },
      extraCssText: `box-shadow: ${c.tooltipShadow}; border-radius: 8px;`
    },
    legend: {
      bottom: 0,
      left: 'center',
      type: narrow ? 'scroll' : 'plain',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { color: c.legend, fontSize: narrow ? 10 : 11 }
    },
    series: [{
      type: 'pie',
      radius: narrow ? ['52%', '74%'] : ['48%', '72%'],
      center: narrow ? ['50%', '42%'] : ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: c.border, borderWidth: 3 },
      label: {
        color: c.label,
        fontSize: narrow ? 9 : 11,
        formatter: narrow ? '{b}' : '{b}: {c}'
      },
      data: data.map((d) => ({ name: d.label, value: d.value }))
    }]
  }, true)
}

let themeObserverStop: (() => void) | null = null
let lastCategoryData: Array<{ label: string; value: number }> = []
let pollTimer: ReturnType<typeof setInterval> | null = null
let chartInstance: ReturnType<typeof echarts.init> | null = null
let categoryChartInstance: ReturnType<typeof echarts.init> | null = null
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (isCashier.value) return
  const el = document.getElementById('chart')
  if (el) {
    chartInstance = echarts.init(el)
    updateChart()
  }
  loadStats()
  pollTimer = setInterval(loadStats, 15000)
  connectWebSocket()

  resizeObserver = new ResizeObserver(() => {
    chartInstance?.resize()
    categoryChartInstance?.resize()
  })
  if (el) resizeObserver.observe(el)
  const catEl = document.getElementById('category-chart')
  if (catEl) resizeObserver.observe(catEl)

  themeObserverStop = watchThemeChange(() => {
    updateChart()
    if (lastCategoryData.length && categoryChartInstance) {
      renderCategoryChart(lastCategoryData)
    }
  })
})

watch(activePeriod, updateChart)

onUnmounted(() => {
  resizeObserver?.disconnect()
  themeObserverStop?.()
  chartInstance?.dispose()
  chartInstance = null
  categoryChartInstance?.dispose()
  categoryChartInstance = null
  if (pollTimer) clearInterval(pollTimer)
  disconnectWebSocket()
})
</script>

<style scoped>
.dashboard-metrics {
  margin-bottom: 1.5rem;
  gap: 1.5rem;
}

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

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
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

.chart-card {
  display: flex;
  flex-direction: column;
  height: auto;
  min-height: 22rem;
}

.chart-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.chart-card__subtitle {
  margin: 0.25rem 0 0;
  color: var(--muted);
  font-size: 0.88rem;
}

.chart-card__canvas {
  flex: 1;
  min-height: 16rem;
  width: 100%;
}

.period-tabs {
  display: flex;
  gap: 0.35rem;
  padding: 0.25rem;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--border);
}

.period-tabs__btn {
  border: none;
  background: transparent;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: 0.18s ease;
}

.period-tabs__btn--active {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #fff;
  box-shadow: 0 6px 16px rgba(34, 197, 94, 0.24);
}

.activity-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.activity-list {
  gap: 0.65rem;
}

.activity-item {
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.activity-item:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-soft);
}

.activity-item__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.activity-item__time {
  font-size: 0.78rem;
  color: var(--muted);
  white-space: nowrap;
}

.goal-panel {
  margin-bottom: 1.5rem;
}

.content-grid + .content-grid {
  margin-top: 1.5rem;
}

@media (max-width: 1240px) {
  .content-grid--two {
    grid-template-columns: 1fr;
  }
}

.goal-panel__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.goal-panel__info {
  min-width: 0;
}

.goal-panel__subtitle {
  margin: 0.3rem 0 0;
  color: var(--muted);
  font-size: 0.85rem;
}

.goal-panel__pct {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--forest-light);
}

.goal-bar {
  height: 0.75rem;
  border-radius: 999px;
  background: var(--overlay-07);
  overflow: hidden;
}

.goal-bar__fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--forest-dark), var(--forest-mid));
  box-shadow: 0 0 14px rgba(34, 197, 94, 0.4);
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.top-list {
  gap: 0.7rem;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.top-item__rank {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 999px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
}

.top-item__body {
  flex: 1;
  min-width: 0;
}

.top-item__bar {
  height: 0.4rem;
  border-radius: 999px;
  background: var(--overlay-07);
  margin-top: 0.35rem;
  overflow: hidden;
}

.top-item__bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.5), var(--forest-mid));
}

.top-item__qty {
  font-weight: 700;
  color: var(--forest-light);
  white-space: nowrap;
}

.peak-hour__value {
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--forest-light);
  margin: 0.25rem 0 0;
}

.peak-hour__sub {
  color: var(--muted);
  font-size: 0.85rem;
  margin: 0.35rem 0 0;
}

.empty-hint {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0.5rem 0 0;
}

@media (max-width: 720px) {
  .chart-card__header {
    flex-direction: column;
    align-items: stretch;
  }

  .period-tabs {
    align-self: flex-start;
  }
}

.panel--large {
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.metric {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric__label {
  margin: 0;
}

.metric__value {
  margin: 0;
  margin-top: 0.15rem;
}

.metric__meta {
  margin: 0;
  margin-top: 0.15rem;
}

.chart-card__header {
  margin-bottom: 0;
}

.chart-card__subtitle {
  margin-top: 0.5rem;
}

.period-tabs {
  gap: 0.5rem;
  padding: 0.35rem;
}

.period-tabs__btn {
  padding: 0.55rem 1rem;
}

.activity-panel__header {
  margin-bottom: 0;
}

.activity-list {
  gap: 1.25rem;
}

.activity-item {
  padding: 1.25rem;
}

.activity-item__top {
  margin-bottom: 0.75rem;
}

.activity-item .item__sub {
  margin-top: 0.75rem;
}

.top-list {
  gap: 1.25rem;
}

.top-item {
  padding: 1.15rem;
}

.top-item__bar {
  margin-top: 0.6rem;
}

.goal-panel__top {
  margin-bottom: 0;
}

.goal-panel__subtitle {
  margin-top: 0.5rem;
}

.peak-hour__value {
  margin-top: 0.2rem;
}

.peak-hour__sub {
  margin-top: 0.5rem;
}

.empty-hint {
  margin-top: 0.2rem;
}
</style>
