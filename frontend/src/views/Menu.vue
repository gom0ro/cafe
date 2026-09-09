<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="menu" :size="16" />
          <span>Каталог блюд</span>
        </div>
        <h1 class="hero__title">Меню</h1>
        <p class="hero__lead">Управление блюдами, ценами и категориями. Подходит для кассы и кухни.</p>
      </div>
      <div class="hero__chip">
        <span>{{ items.length }} позиций</span>
      </div>
    </section>

    <section class="glass panel panel--large" style="margin-bottom: 1.5rem;">
      <form @submit.prevent="submit" class="form-grid">
        <div class="form-group">
          <label class="form-label">Название</label>
          <input v-model="form.name" required placeholder="Название блюда" class="input" />
        </div>
        <div class="form-group">
          <label class="form-label">Цена</label>
          <div class="input-wrapper">
            <input v-model.number="form.price" required type="number" min="0" step="0.01" placeholder="0.00" class="input" />
            <span class="currency-symbol">₸</span>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Категория</label>
          <input v-model="form.category" placeholder="Напитки, Основное..." class="input" />
        </div>
        <div class="form-group">
          <label class="form-label">Описание</label>
          <input v-model="form.description" placeholder="Короткое описание..." class="input" />
        </div>
        <div class="form-group">
          <label class="form-label">Фото</label>
          <div class="file-upload-wrapper">
            <input ref="fileInput" type="file" @change="onFile" accept="image/*" class="file-input" />
            <button type="button" class="button button--secondary button--sm" @click="pickFile">
              <UiIcon name="image" :size="16" />
              <span>Выбрать фото</span>
            </button>
            <div v-if="selectedFile" class="file-preview">
              <div class="file-preview__thumb">
                <img v-if="previewUrl" :src="previewUrl" alt="Превью" />
                <UiIcon v-else name="image" :size="20" class="placeholder-icon" />
              </div>
              <span class="file-preview__name">{{ selectedFile.name }}</span>
              <button type="button" class="file-preview__clear" title="Убрать фото" @click="clearFile">
                <UiIcon name="x" :size="14" />
              </button>
            </div>
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="button button--primary">
            <UiIcon name="plus-circle" :size="18" />
            <span>Создать блюдо</span>
          </button>
        </div>
      </form>
    </section>

    <div v-if="loading" class="list">
      <div v-for="n in 6" :key="n" class="skeleton" style="height: 9rem; border-radius: 24px;"></div>
    </div>

    <div v-else class="grid-cards grid-cards--3">
      <div v-for="item in items" :key="item.id" class="glass-hover panel item">
        <div class="menu-item-content">
          <div class="menu-item-image">
            <div class="menu-item-image__placeholder">
              <img v-if="item.image" :src="item.image" :alt="item.name" />
              <UiIcon v-else name="image" :size="24" class="placeholder-icon" />
            </div>
          </div>
          <div class="menu-item-info">
            <div class="menu-item-header">
              <div class="item__title">{{ item.name }}</div>
              <span class="availability-dot availability-dot--ok" v-if="item.available" title="В наличии"></span>
              <span class="availability-dot availability-dot--off" v-else title="Нет в наличии"></span>
              <div class="card-actions">
                <button type="button" class="icon-button" title="Редактировать" @click="openEdit(item)">
                  <UiIcon name="edit" :size="16" />
                </button>
                <button type="button" class="icon-button icon-button--danger" title="Удалить позицию" @click="confirmItem = item; showConfirm = true">
                  <UiIcon name="trash" :size="16" />
                </button>
              </div>
            </div>
            <div class="item__sub">{{ item.description || 'Описание отсутствует' }}</div>
            <div class="menu-item-footer">
              <span class="status-badge status-badge--neutral">{{ item.category || 'Без категории' }}</span>
              <div class="item__meta">{{ formatPrice(item.price) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AppModal v-model="showConfirm" title="Удалить позицию?">
      <p class="modal__text">
        Вы уверены, что хотите удалить «{{ confirmItem?.name }}» из меню? Это действие нельзя отменить.
      </p>
      <div class="modal__actions">
        <button type="button" class="button button--ghost" @click="showConfirm = false; confirmItem = null">Отмена</button>
        <button type="button" class="button button--danger" :disabled="deleting" @click="deleteItem">
          <UiIcon name="trash" :size="16" />
          <span>{{ deleting ? 'Удаление...' : 'Удалить' }}</span>
        </button>
      </div>
    </AppModal>

    <AppModal v-model="showEdit" title="Редактировать блюдо">
      <div class="modal__body">
        <div class="form-group">
          <label class="form-label">Название</label>
          <input v-model="editForm.name" required class="input" placeholder="Название блюда" />
        </div>
        <div class="form-grid form-grid--compact">
          <div class="form-group">
            <label class="form-label">Цена</label>
            <div class="input-wrapper">
              <input v-model.number="editForm.price" required type="number" min="0" step="0.01" class="input" placeholder="0.00" />
              <span class="currency-symbol">₸</span>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Категория</label>
            <input v-model="editForm.category" class="input" placeholder="Напитки, Основное..." />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Описание</label>
          <input v-model="editForm.description" class="input" placeholder="Короткое описание..." />
        </div>
        <div class="form-group">
          <label class="form-label">Фото</label>
          <div class="file-upload-wrapper">
            <input ref="editFileInput" type="file" @change="onEditFile" accept="image/*" class="file-input" />
            <div class="file-preview" v-if="editPreviewUrl">
              <div class="file-preview__thumb">
                <img :src="editPreviewUrl" alt="Превью" />
              </div>
              <span class="file-preview__name">Новое фото</span>
              <button type="button" class="file-preview__clear" title="Убрать новое фото" @click="clearEditFile">
                <UiIcon name="x" :size="14" />
              </button>
            </div>
            <button type="button" class="button button--secondary button--sm" @click="editFileInput?.click()">
              <UiIcon name="image" :size="16" />
              <span>{{ editPreviewUrl ? 'Заменить фото' : 'Выбрать фото' }}</span>
            </button>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Доступность</label>
          <button
            type="button"
            class="status-toggle"
            :class="{ 'status-toggle--on': editForm.available }"
            role="switch"
            :aria-checked="editForm.available"
            @click="editForm.available = !editForm.available"
          >
            <span class="status-toggle__track">
              <span class="status-toggle__thumb"></span>
            </span>
            <span class="status-toggle__label">{{ editForm.available ? 'В наличии' : 'Нет в наличии' }}</span>
          </button>
        </div>
      </div>
      <div class="modal__actions">
        <button type="button" class="button button--ghost" @click="showEdit = false; closeEdit()">Отмена</button>
        <button type="button" class="button button--primary" :disabled="editSaving" @click="saveEdit">
          <UiIcon name="check" :size="16" />
          <span>{{ editSaving ? 'Сохранение...' : 'Сохранить' }}</span>
        </button>
      </div>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'
import AppModal from '../components/AppModal.vue'

interface MenuItem {
  id: number
  name: string
  price: number
  category?: string
  description?: string
  image?: string
  available: boolean
}

const items = ref<MenuItem[]>([])
const loading = ref(true)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const confirmItem = ref<MenuItem | null>(null)
const showConfirm = ref(false)
const deleting = ref(false)
const editingItem = ref<MenuItem | null>(null)
const showEdit = ref(false)
const editSaving = ref(false)
const editFileInput = ref<HTMLInputElement | null>(null)
const editSelectedFile = ref<File | null>(null)
const editPreviewUrl = ref('')
const editForm = ref({
  name: '',
  price: 0,
  category: '',
  description: '',
  available: true
})

const form = ref({
  name: '',
  price: 0,
  category: '',
  description: ''
})

const formatPrice = (price: number): string => {
  return price.toLocaleString('ru-RU') + ' ₸'
}

function pickFile() {
  fileInput.value?.click()
}

function onFile(e: Event) {
  const t = e.target as HTMLInputElement
  if (t.files && t.files[0]) {
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    selectedFile.value = t.files[0]
    previewUrl.value = URL.createObjectURL(t.files[0])
  }
}

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  selectedFile.value = null
  previewUrl.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function loadMenu() {
  loading.value = true
  try {
    const r = await api.get<MenuItem[]>('/menu/')
    items.value = r.data
    localStorage.setItem('menu_cache', JSON.stringify(items.value))
  } catch (e) {
    console.error('Failed to load menu:', e)
    const cached = localStorage.getItem('menu_cache')
    if (cached) {
      try { items.value = JSON.parse(cached) } catch { /* ignore */ }
    }
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.value.name || !form.value.price) {
    alert('Пожалуйста, заполните обязательные поля')
    return
  }
  try {
    const fd = new FormData()
    fd.append('name', form.value.name)
    fd.append('price', String(form.value.price))
    if (form.value.category) fd.append('category', form.value.category)
    if (form.value.description) fd.append('description', form.value.description)
    if (selectedFile.value) fd.append('image', selectedFile.value)
    await api.post('/menu/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    form.value = { name: '', price: 0, category: '', description: '' }
    clearFile()
    await loadMenu()
  } catch (e) {
    console.error('Failed to create menu item:', e)
    alert('Ошибка при создании блюда')
  }
}

async function deleteItem() {
  const item = confirmItem.value
  if (!item) return
  deleting.value = true
  try {
    await api.delete(`/menu/${item.id}`)
    items.value = items.value.filter((i) => i.id !== item.id)
    localStorage.setItem('menu_cache', JSON.stringify(items.value))
    confirmItem.value = null
    showConfirm.value = false
  } catch (e) {
    console.error('Failed to delete menu item:', e)
    alert('Не удалось удалить позицию')
  } finally {
    deleting.value = false
  }
}

function openEdit(item: MenuItem) {
  editingItem.value = item
  editForm.value = { name: item.name, price: item.price, category: item.category || '', description: item.description || '', available: item.available }
  clearEditFile()
  showEdit.value = true
}

function closeEdit() {
  editingItem.value = null
  editSaving.value = false
  clearEditFile()
  showEdit.value = false
}

function onEditFile(e: Event) {
  const t = e.target as HTMLInputElement
  if (t.files && t.files[0]) {
    if (editPreviewUrl.value) URL.revokeObjectURL(editPreviewUrl.value)
    editSelectedFile.value = t.files[0]
    editPreviewUrl.value = URL.createObjectURL(t.files[0])
  }
}

function clearEditFile() {
  if (editPreviewUrl.value) URL.revokeObjectURL(editPreviewUrl.value)
  editSelectedFile.value = null
  editPreviewUrl.value = ''
  if (editFileInput.value) editFileInput.value.value = ''
}

async function saveEdit() {
  const item = editingItem.value
  if (!item) return
  if (!editForm.value.name || !editForm.value.price) {
    alert('Пожалуйста, заполните обязательные поля')
    return
  }
  editSaving.value = true
  try {
    const fd = new FormData()
    fd.append('name', editForm.value.name)
    fd.append('price', String(editForm.value.price))
    if (editForm.value.category) fd.append('category', editForm.value.category)
    if (editForm.value.description) fd.append('description', editForm.value.description)
    fd.append('available', String(editForm.value.available))
    if (editSelectedFile.value) fd.append('image', editSelectedFile.value)
    await api.put(`/menu/${item.id}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    closeEdit()
    await loadMenu()
  } catch (e) {
    console.error('Failed to update menu item:', e)
    alert('Ошибка при сохранении изменений')
  } finally {
    editSaving.value = false
  }
}

function onDocKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (showConfirm.value) { showConfirm.value = false; confirmItem.value = null }
  if (showEdit.value) closeEdit()
}

onMounted(() => {
  loadMenu()
  document.addEventListener('keydown', onDocKeydown)
})

onUnmounted(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  if (editPreviewUrl.value) URL.revokeObjectURL(editPreviewUrl.value)
  document.removeEventListener('keydown', onDocKeydown)
})
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.25rem;
}

@media (max-width: 720px) {
  .form-grid { grid-template-columns: 1fr; }
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.currency-symbol {
  position: absolute;
  right: 1rem;
  color: var(--muted);
  font-weight: 600;
  pointer-events: none;
}

.file-upload-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.file-input { display: none; }

.file-preview {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.75rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.file-preview__thumb {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--overlay-06);
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-preview__thumb img { width: 100%; height: 100%; object-fit: cover; }

.file-preview__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-control);
}

.file-preview__clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.85rem;
  height: 1.85rem;
  padding: 0;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--overlay-04);
  color: var(--text-control);
  flex-shrink: 0;
  transition: background 0.16s ease, color 0.16s ease;
}

.file-preview__clear:hover {
  background: rgba(239, 68, 68, 0.14);
  color: var(--danger-soft);
}

.menu-item-content {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
}

.menu-item-image {
  width: 7rem;
  height: 7rem;
  flex-shrink: 0;
}

.menu-item-image__placeholder {
  width: 100%;
  height: 100%;
  border-radius: 20px;
  overflow: hidden;
  background: var(--surface);
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-item-image__placeholder img { width: 100%; height: 100%; object-fit: cover; }
.placeholder-icon { color: var(--muted); }

.menu-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.glass-hover.panel.item {
  overflow: hidden;
}

.menu-item-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
}

.menu-item-header .item__title {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.1rem;
  height: 2.1rem;
  padding: 0;
  flex-shrink: 0;
  border-radius: 10px;
  cursor: pointer;
  background: var(--overlay-04);
  border: 1px solid var(--border);
  color: var(--text-control);
  transition: background 0.16s ease, color 0.16s ease, border-color 0.16s ease;
}

.icon-button:hover {
  background: var(--overlay-09);
  color: var(--text-strong);
  border-color: var(--overlay-12);
}

.icon-button--danger:hover {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.35);
  color: var(--danger-soft);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.button--danger {
  color: #fff;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 10px 26px rgba(239, 68, 68, 0.28);
}

.button--danger:hover {
  background: linear-gradient(135deg, #f54545, #e11d1d);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22), 0 14px 30px rgba(239, 68, 68, 0.35);
}

.button--danger:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.7rem;
  white-space: nowrap;
}

.availability-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.availability-dot--ok {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.18);
}

.availability-dot--off {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.18);
}

.menu-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.8rem;
}

@media (max-width: 720px) {
  .menu-item-content { flex-direction: column; }
  .menu-item-image { width: 100%; height: 10rem; }
  .menu-item-footer { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
  .menu-item-footer > div:last-child { order: -1; }
}

/* ===== Availability toggle ===== */
.status-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font: inherit;
}

.status-toggle__track {
  position: relative;
  width: 3rem;
  height: 1.7rem;
  border-radius: 999px;
  background: var(--overlay-12);
  border: 1px solid var(--border);
  transition: background 0.2s ease, border-color 0.2s ease;
  flex-shrink: 0;
}

.status-toggle__thumb {
  position: absolute;
  top: 50%;
  left: 0.2rem;
  width: 1.3rem;
  height: 1.3rem;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  transform: translateY(-50%);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), background 0.2s ease;
}

.status-toggle--on .status-toggle__track {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border-color: transparent;
}

.status-toggle--on .status-toggle__thumb {
  transform: translateY(-50%) translateX(1.2rem);
}

.status-toggle__label {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-control);
}
</style>