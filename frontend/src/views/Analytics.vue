<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="analytics" :size="16" />
          <span>Аналитические отчёты</span>
        </div>
        <h1 class="hero__title">Аналитика</h1>
        <p class="hero__lead">Отчёты по выручке и динамике кафе в реальном времени.</p>
      </div>
      <div class="hero__chip">
        <span v-if="!loading">{{ fmtMoney(revenueAll) }} за всё время</span>
        <span v-else>Загрузка…</span>
      </div>
    </section>

    <section v-if="loading" class="grid-cards grid-cards--3" style="margin-bottom: 1.5rem;">
      <div v-for="n in 3" :key="n" class="skeleton" style="height: 7.5rem; border-radius: 24px;"></div>
    </section>

    <template v-else>
      <section class="grid-cards grid-cards--3" style="margin-bottom: 1.5rem;">
        <article class="glass panel metric">
          <div class="metric__label">Выручка за неделю</div>
          <h3 class="metric__value">₽{{ fmtMoney(weeklyRevenue) }}</h3>
          <p class="metric__meta" :class="weekDelta >= 0 ? 'metric__meta--up' : 'metric__meta--down'">
            <UiIcon :name="weekDelta >= 0 ? 'trending-up' : 'trending-down'" :size="14" />
            <span>{{ weekDelta >= 0 ? '+' : '' }}{{ weekDelta }}% к прошлой неделе</span>
          </p>
        </article>
        <article class="glass panel metric">
          <div class="metric__label">Средний чек</div>
          <h3 class="metric__value">₽{{ fmtMoney(avgCheck) }}</h3>
          <p class="metric__meta">
            <span>По продажам за сегодня</span>
          </p>
        </article>
        <article class="glass panel metric">
          <div class="metric__label">Заказов за день</div>
          <h3 class="metric__value">{{ dailyOrders }}</h3>
          <p class="metric__meta">
            <span>Пик: {{ peakHour }}</span>
          </p>
        </article>
      </section>

      <section class="content-grid content-grid--two">
        <article class="glass panel panel--large chart-card">
          <div class="chart-card__header">
            <div>
              <h2 class="section-heading">
                <UiIcon name="analytics" :size="20" />
                <span>Динамика выручки</span>
              </h2>
              <p class="chart-card__subtitle">По дням недели</p>
            </div>
          </div>
          <div v-if="hasChart" id="chart-area" class="chart-canvas"></div>
          <p v-else class="empty-hint">Пока нет данных для графика</p>
        </article>

        <aside class="glass panel panel--large">
          <h2 class="section-heading">
            <UiIcon name="file-text" :size="20" />
            <span>Отчёты</span>
          </h2>
          <div class="list">
            <div class="item">
              <div class="item__title">
                <UiIcon name="calendar" :size="16" />
                <span>День</span>
              </div>
              <div class="item__sub">
                <span class="success">Сегодня:</span> ₽{{ fmtMoney(revenueToday) }} · {{ dailyOrders }} заказов
              </div>
            </div>
            <div class="item">
              <div class="item__title">
                <UiIcon name="calendar" :size="16" />
                <span>Неделя</span>
              </div>
              <div class="item__sub">
                <span class="success">Рост:</span> {{ weekDelta >= 0 ? '+' : '' }}{{ weekDelta }}% к прошлой неделе
              </div>
            </div>
            <div class="item">
              <div class="item__title">
                <UiIcon name="calendar" :size="16" />
                <span>Месяц</span>
              </div>
              <div class="item__sub">
                <span class="success">Лучший день:</span> {{ bestDay }}
              </div>
            </div>
            <div class="item">
              <div class="item__title">
                <UiIcon name="users" :size="16" />
                <span>Выручка всего</span>
              </div>
              <div class="item__sub">
                <span class="success">За всё время:</span> ₽{{ fmtMoney(revenueAll) }}
              </div>
            </div>
          </div>

          <div class="export-actions" style="margin-top: 1.5rem;">
            <button class="button button--secondary button--block" @click="exportCSV">
              <UiIcon name="download" :size="16" />
              <span>Экспорт Excel</span>
            </button>
            <button class="button button--secondary button--block" style="margin-top: 0.75rem;" @click="exportPDF">
              <UiIcon name="download" :size="16" />
              <span>Экспорт PDF</span>
            </button>
          </div>
        </aside>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import { chartThemeColors, watchThemeChange } from '../composables/useChartTheme'

const loading = ref(true)
const weeklyRevenue = ref(0)
const avgCheck = ref(0)
const dailyOrders = ref(0)
const peakHour = ref('—')
const revenueToday = ref(0)
const revenueAll = ref(0)
const weekDelta = ref(0)
const bestDay = ref('—')
const weekLabels = ref<string[]>([])
const weekValues = ref<number[]>([])
const hasChart = ref(false)

const fmtMoney = (n: number): string => Math.round(n).toLocaleString('ru-RU')

let chartInstance: echarts.ECharts | null = null
let themeObserverStop: (() => void) | null = null
let resizeObserver: ResizeObserver | null = null

function renderChart() {
  if (!chartInstance) return
  const labels = weekLabels.value.length ? weekLabels.value : weekValues.value.map((_, i) => String(i + 1))
  const c = chartThemeColors()
  const el = document.getElementById('chart-area')
  const narrow = el ? el.clientWidth < 420 : false
  const dense = labels.length > 9
  chartInstance.setOption({
    grid: { left: 20, right: 20, top: 24, bottom: 20, containLabel: true },
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
      data: labels,
      axisLine: { lineStyle: { color: c.axis } },
      axisLabel: {
        color: c.label,
        fontSize: narrow ? 10 : 11,
        padding: [4, 0, 0, 0],
        interval: dense ? Math.ceil(labels.length / (narrow ? 5 : 8)) : 0
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
      name: 'Выручка (руб)',
      data: weekValues.value,
      type: 'bar',
      barMaxWidth: 42,
      itemStyle: {
        borderRadius: [8, 8, 4, 4],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#22c55e' },
          { offset: 1, color: '#16a34a' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#4ade80' },
            { offset: 1, color: '#22c55e' }
          ])
        }
      }
    }]
  }, true)
}

async function loadStats() {
  try {
    const { data } = await api.get('/dashboard/stats')

    weeklyRevenue.value = (data.week_values || []).reduce((a: number, b: number) => a + b, 0)
    avgCheck.value = data.avg_check || 0
    dailyOrders.value = data.orders_today || 0

    const peaks = data.revenue_by_hour || []
    const peak = peaks.reduce((a: { label: string; value: number }, b: { label: string; value: number }) =>
      b.value > a.value ? b : a, { label: '', value: 0 })
    peakHour.value = peak.value > 0 ? peak.label : '—'

    revenueToday.value = data.revenue_today || 0
    revenueAll.value = data.revenue_all || 0
    weekDelta.value = data.week_delta_pct || 0
    weekLabels.value = data.week_labels || []
    weekValues.value = data.week_values || []
    hasChart.value = weekValues.value.some((v: number) => v > 0)

    const monthValues = data.month_values || []
    const monthLabels = data.month_labels || []
    if (monthValues.length) {
      const mx = Math.max(...monthValues)
      const idx = monthValues.indexOf(mx)
      bestDay.value = mx > 0 ? String(monthLabels[idx] ?? idx + 1) : '—'
    }

    renderChart()
  } catch (e) {
    console.error('Failed to load analytics:', e)
  } finally {
    loading.value = false
  }
}

function exportCSV() {
  const rows: Array<Array<string | number>> = [
    ['Отчёт по выручке'],
    ['День', 'Выручка (₽)'],
    ...weekLabels.value.map((l, i) => [l, weekValues.value[i] || 0]),
    [],
    ['Средний чек (₽)', avgCheck.value],
    ['Заказов за день', dailyOrders.value],
    ['За сегодня (₽)', revenueToday.value],
    ['За всё время (₽)', revenueAll.value]
  ]
  const csv = rows.map((r) => r.map((v) => (v === '' ? '' : String(v).replace(';', ',')).trim()).join(';')).join('\r\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'analytics.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function exportPDF() {
  window.print()
}

const handleResize = () => {
  if (chartInstance) chartInstance.resize()
}

onMounted(() => {
  const el = document.getElementById('chart-area')
  if (el) {
    chartInstance = echarts.init(el)
    renderChart()
    resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(el)
  }
  loadStats()

  themeObserverStop = watchThemeChange(renderChart)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  themeObserverStop?.()
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.export-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.button--block {
  width: 100%;
}

.chart-card {
  display: flex;
  flex-direction: column;
  min-height: 22rem;
}

.chart-card__header {
  margin-bottom: 0.75rem;
}

.chart-card__subtitle {
  margin: 0.25rem 0 0;
  color: var(--muted);
  font-size: 0.88rem;
}

.chart-canvas {
  flex: 1;
  height: 16rem;
  width: 100%;
}

.empty-hint {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0.5rem 0 0;
}
</style>