<template>
  <section class="tables-manager">
    <div class="settings-divider" />

    <!-- ================= Столики ================= -->
    <section class="manager-section">
      <div class="manager-head">
        <div>
          <h2 class="section-heading">
            <UiIcon name="pos" :size="20" />
            <span>Столики</span>
          </h2>
          <p class="manager-sub">Добавление, изменение и удаление столиков зала.</p>
        </div>
      </div>

      <form class="glass panel panel--large table-form" @submit.prevent="saveTable">
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Название</label>
            <input v-model="tableForm.name" class="input" placeholder="Стол 1 / Окно / VIP" />
          </div>
          <div class="form-group">
            <label class="form-label">Номер</label>
            <input v-model="tableForm.number" class="input" placeholder="Пусто — присвоим автоматически" />
          </div>
          <div class="form-group">
            <label class="form-label">Зона</label>
            <input v-model="tableForm.zone" class="input" placeholder="Зал / Терраса / VIP" />
          </div>
          <div class="form-group">
            <label class="form-label">Мест</label>
            <input v-model.number="tableForm.seats" class="input" type="number" min="1" placeholder="4" />
          </div>
        </div>

        <label class="checkbox-label">
          <input v-model="tableForm.is_active" type="checkbox" />
          <span>Столик активен (виден в POS)</span>
        </label>

        <div class="toolbar">
          <button type="submit" class="button button--primary">
            <UiIcon :name="editingTableId ? 'check' : 'plus'" :size="18" />
            <span>{{ editingTableId ? 'Сохранить столик' : 'Добавить столик' }}</span>
          </button>
          <button v-if="editingTableId" type="button" class="button button--ghost" @click="cancelTableEdit">
            <UiIcon name="x" :size="18" />
            <span>Отмена</span>
          </button>
          <span v-if="tableMsg" class="form-msg form-msg--ok">{{ tableMsg }}</span>
          <span v-if="tableError" class="form-msg form-msg--error">{{ tableError }}</span>
        </div>
      </form>

      <div v-if="tablesLoading" class="tables-grid">
        <div v-for="n in 3" :key="n" class="table-card table-card--skeleton"></div>
      </div>
      <template v-else>
        <div class="tables-grid">
          <article
            v-for="t in tables"
            :key="t.id"
            class="glass panel table-card"
            :class="{ 'table-card--inactive': !t.is_active }"
          >
            <div class="table-card__top">
              <div class="table-card__num">{{ tableLabel(t) }}</div>
              <div class="table-card__actions">
                <span class="status-badge" :class="t.is_active ? 'status-badge--success' : 'status-badge--neutral'">
                  <span class="status-dot" />
                  {{ t.is_active ? 'Активен' : 'Скрыт' }}
                </span>
                <button
                  type="button"
                  class="icon-btn"
                  :disabled="deletingId === t.id"
                  title="Изменить"
                  @click="startTableEdit(t)"
                >
                  <UiIcon name="edit" :size="16" />
                </button>
                <button
                  type="button"
                  class="icon-btn icon-btn--danger"
                  :disabled="deletingId === t.id"
                  title="Удалить"
                  @click="removeTable(t)"
                >
                  <UiIcon name="trash" :size="16" />
                </button>
              </div>
            </div>
            <div class="table-card__info">
              <div class="item__sub">{{ t.seats }} мест{{ t.zone ? ' · ' + t.zone : '' }}</div>
            </div>
          </article>
        </div>
        <p v-if="!tables.length" class="empty-hint">Столиков пока нет — добавьте первый выше.</p>
      </template>
    </section>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import api from '../api'
import UiIcon from './UiIcon.vue'
import { tableLabel } from '../lib/tableLabel'

interface TableRow {
  id: number
  number: string
  name?: string
  seats: number
  zone?: string
  is_active: boolean
}

const tables = ref<TableRow[]>([])
const tablesLoading = ref(true)
const deletingId = ref<number | null>(null)

const tableMsg = ref('')
const tableError = ref('')

const editingTableId = ref<number | null>(null)

const tableForm = reactive({ number: '', name: '', zone: '', seats: 4, is_active: true })

function flash(ok: string, err: string) {
  tableMsg.value = ok
  tableError.value = err
  setTimeout(() => {
    tableMsg.value = ''
    tableError.value = ''
  }, 4000)
}

function errText(e: any): string {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return 'Не удалось выполнить операцию'
}

// ------------------- Tables -------------------

async function loadTables() {
  tablesLoading.value = true
  try {
    tables.value = (await api.get('/tables/')).data
  } catch (e) {
    flash('', 'Не удалось загрузить столики')
  } finally {
    tablesLoading.value = false
  }
}

function resetTableForm() {
  tableForm.number = ''
  tableForm.name = ''
  tableForm.zone = ''
  tableForm.seats = 4
  tableForm.is_active = true
  editingTableId.value = null
}

async function saveTable() {
  try {
    if (editingTableId.value) {
      await api.patch(`/tables/${editingTableId.value}`, { ...tableForm })
      flash('Столик обновлён', '')
      resetTableForm()
    } else {
      await api.post('/tables/', {
        number: tableForm.number || null,
        name: tableForm.name || null,
        zone: tableForm.zone || null,
        seats: tableForm.seats,
        is_active: tableForm.is_active
      })
      flash('Столик добавлен', '')
    }
    await loadTables()
  } catch (e) {
    flash('', errText(e))
  }
}

function startTableEdit(t: TableRow) {
  editingTableId.value = t.id
  tableForm.number = t.number
  tableForm.name = t.name || ''
  tableForm.zone = t.zone || ''
  tableForm.seats = t.seats
  tableForm.is_active = t.is_active
}

function cancelTableEdit() {
  resetTableForm()
}

async function removeTable(t: TableRow) {
  if (!confirm(`Удалить столик ${tableLabel(t)}? Связанные брони будут удалены.`)) return
  deletingId.value = t.id
  try {
    await api.delete(`/tables/${t.id}`)
    await loadTables()
  } catch (e) {
    flash('', errText(e))
  } finally {
    deletingId.value = null
  }
}

onMounted(() => {
  loadTables()
})
</script>

<style scoped>
.tables-manager {
  display: flex;
  flex-direction: column;
}

.settings-divider {
  height: 1px;
  background: var(--border);
}

.manager-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 0;
}

.manager-section + .manager-section {
  margin-top: 1.5rem;
}

.manager-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.manager-sub {
  color: var(--text-muted, var(--muted));
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.table-form {
  margin-bottom: 0.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
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

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--muted);
  cursor: pointer;
}

.checkbox-label input {
  accent-color: var(--accent, #7c3aed);
  width: 1rem;
  height: 1rem;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(230px, 100%), 1fr));
  gap: 1rem;
  max-width: 100%;
}

.table-card {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  min-width: 0;
  max-width: 100%;
  gap: 0.75rem;
  opacity: 1;
  transition: opacity 0.2s;
  box-sizing: border-box;
}

.table-card--inactive {
  opacity: 0.55;
}

.table-card--skeleton {
  min-height: 7rem;
  background: var(--surface, rgba(0, 0, 0, 0.15));
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
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

.table-card__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
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

.icon-btn:active {
  transform: scale(0.95);
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.icon-btn--danger:hover {
  color: var(--danger);
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.35);
}

.empty-hint {
  color: var(--muted);
  font-size: 0.9rem;
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>