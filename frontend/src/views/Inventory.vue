<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="inventory" :size="16" />
          <span>Управление складом</span>
        </div>
        <h1 class="hero__title">Склад</h1>
        <p class="hero__lead">Остатки, поступления и низкие запасы ингредиентов в одном месте.</p>
      </div>
      <div class="hero__chip">
        <span>{{ ingredients.length }} позиций</span>
      </div>
    </section>

    <section class="glass panel panel--large" style="margin-bottom: 1.5rem;">
      <form @submit.prevent="createIngredient" class="form-grid">
        <div class="form-group">
          <label class="form-label">Название</label>
          <input 
            v-model="newIng.name" 
            placeholder="Название ингредиента" 
            class="input"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Количество</label>
          <div class="input-wrapper">
            <input 
              v-model.number="newIng.quantity" 
              type="number" 
              min="0" 
              step="0.01"
              placeholder="0.00" 
              class="input"
            />
            <span class="currency-symbol">шт</span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Единица измерения</label>
          <input 
            v-model="newIng.unit" 
            placeholder="кг, л, шт..." 
            class="input"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Минимальный запас</label>
          <div class="input-wrapper">
            <input 
              v-model.number="newIng.threshold" 
              type="number" 
              min="0" 
              step="0.01"
              placeholder="0.00" 
              class="input"
            />
            <span class="currency-symbol">шт</span>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="button button--primary">
            <UiIcon name="plus-circle" :size="18" />
            <span>Добавить ингредиент</span>
          </button>
        </div>
      </form>
    </section>

    <div v-if="loading" class="list">
      <div v-for="n in 6" :key="n" class="skeleton" style="height: 4rem; border-radius: 24px;"></div>
    </div>

    <div v-else class="list">
      <div 
        v-for="ing in ingredients" 
        :key="ing.id" 
        class="glass-hover panel item"
        :class="{ 'low-stock': ing.quantity <= ing.threshold }"
        style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;"
      >
        <div class="ingredient-info">
          <div class="item__title">
            <UiIcon 
              v-if="ing.quantity <= ing.threshold" 
              name="alert-circle" 
              :size="16" 
              class="danger" 
            />
            {{ ing.name }}
          </div>
          <div class="item__sub">
            <span :class="{
              'danger': ing.quantity <= ing.threshold,
              'success': ing.quantity > ing.threshold
            }">
              {{ ing.quantity }} {{ ing.unit }}
            </span>
            <span class="muted"> · Минимум: {{ ing.threshold }} {{ ing.unit }}</span>
          </div>
        </div>

        <div class="ingredient-controls">
          <div class="control-group">
            <button 
              class="button button--ghost button--sm" 
              @click="adjust(ing.id, -1)"
              title="Уменьшить"
            >
              <UiIcon name="minus" :size="14" />
            </button>
            <button 
              class="button button--ghost button--sm" 
              @click="adjust(ing.id, 1)"
              title="Увеличить"
            >
              <UiIcon name="plus" :size="14" />
            </button>
          </div>

          <span 
            class="status-badge" 
            :class="{
              'status-badge--danger': ing.quantity <= ing.threshold,
              'status-badge--success': ing.quantity > ing.threshold
            }"
          >
            <span class="status-dot"></span>
            {{ ing.quantity <= ing.threshold ? 'Низкий запас' : 'В наличии' }}
          </span>

          <button class="button button--secondary button--sm" title="Редактировать" @click="openEdit(ing)">
            <UiIcon name="settings" :size="14" />
          </button>
          <button class="button button--secondary button--sm button--danger-ghost" title="Удалить" @click="confirmIng = ing; showConfirm = true">
            <UiIcon name="trash" :size="14" />
          </button>
        </div>
      </div>
    </div>

    <AppModal v-model="showConfirm" title="Удалить ингредиент?">
      <p class="modal__text">
        Вы уверены, что хотите удалить «{{ confirmIng?.name }}» со склада? Это действие нельзя отменить.
      </p>
      <div class="modal__actions">
        <button type="button" class="button button--ghost" @click="showConfirm = false; confirmIng = null">Отмена</button>
        <button type="button" class="button button--danger" :disabled="deletingIng" @click="deleteIngredient">
          <UiIcon name="trash" :size="16" />
          <span>{{ deletingIng ? 'Удаление...' : 'Удалить' }}</span>
        </button>
      </div>
    </AppModal>

    <AppModal v-model="showEdit" title="Редактировать ингредиент">
      <div class="modal__body">
        <div class="form-group">
          <label class="form-label">Название</label>
          <input v-model="editForm.name" class="input" placeholder="Название ингредиента" />
        </div>

        <div class="form-grid form-grid--compact">
          <div class="form-group">
            <label class="form-label">Количество</label>
            <div class="input-wrapper">
              <input v-model.number="editForm.quantity" type="number" min="0" step="0.01" class="input" />
              <span class="currency-symbol">шт</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Единица</label>
            <input v-model="editForm.unit" class="input" placeholder="кг, л, шт..." />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Минимальный запас</label>
          <div class="input-wrapper">
            <input v-model.number="editForm.threshold" type="number" min="0" step="0.01" class="input" />
            <span class="currency-symbol">шт</span>
          </div>
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

interface Ingredient {
  id: number
  name: string
  unit: string
  quantity: number
  threshold: number
}

const ingredients = ref<Ingredient[]>([])
const loading = ref(true)

const newIng = ref({
  name: '',
  unit: 'шт',
  quantity: 0,
  threshold: 0
})

const editingIng = ref<Ingredient | null>(null)
const showEdit = ref(false)
const editSaving = ref(false)
const editForm = ref({
  name: '',
  unit: 'шт',
  quantity: 0,
  threshold: 0
})

const confirmIng = ref<Ingredient | null>(null)
const showConfirm = ref(false)
const deletingIng = ref(false)

async function loadIngredients() {
  loading.value = true
  try {
    const r = await api.get<Ingredient[]>('/inventory/')
    ingredients.value = r.data
  } catch (e) {
    console.error('Failed to load ingredients:', e)
    ingredients.value = []
  } finally {
    loading.value = false
  }
}

async function createIngredient() {
  if (!newIng.value.name) {
    alert('Пожалуйста, укажите название ингредиента')
    return
  }

  try {
    await api.post('/inventory/', {
      name: newIng.value.name,
      unit: newIng.value.unit,
      quantity: newIng.value.quantity,
      threshold: newIng.value.threshold
    })

    newIng.value = { name: '', unit: 'шт', quantity: 0, threshold: 0 }
    await loadIngredients()
  } catch (e) {
    console.error('Failed to create ingredient:', e)
    alert('Ошибка при добавлении ингредиента')
  }
}

async function adjust(id: number, delta: number) {
  try {
    await api.patch(`/inventory/${id}/adjust`, null, { 
      params: { delta } 
    })
    await loadIngredients()
  } catch (e) {
    console.error('Failed to adjust quantity:', e)
    alert('Ошибка при изменении количества')
  }
}

function openEdit(ing: Ingredient) {
  editingIng.value = ing
  editForm.value = {
    name: ing.name,
    unit: ing.unit,
    quantity: ing.quantity,
    threshold: ing.threshold
  }
  showEdit.value = true
}

function closeEdit() {
  editingIng.value = null
  editSaving.value = false
  showEdit.value = false
}

async function saveEdit() {
  const ing = editingIng.value
  if (!ing) return
  editSaving.value = true
  try {
    await api.put(`/inventory/${ing.id}`, {
      name: editForm.value.name,
      unit: editForm.value.unit,
      quantity: editForm.value.quantity,
      threshold: editForm.value.threshold
    })
    closeEdit()
    await loadIngredients()
  } catch (e) {
    console.error('Failed to update ingredient:', e)
    alert('Ошибка при сохранении изменений')
  } finally {
    editSaving.value = false
  }
}

async function deleteIngredient() {
  const ing = confirmIng.value
  if (!ing) return
  deletingIng.value = true
  try {
    await api.delete(`/inventory/${ing.id}`)
    ingredients.value = ingredients.value.filter((i) => i.id !== ing.id)
confirmIng.value = null
    showConfirm.value = false
  } catch (e) {
    console.error('Failed to delete ingredient:', e)
    alert('Не удалось удалить ингредиент')
  } finally {
    deletingIng.value = false
  }
}

function onDocKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape') return
  if (showConfirm.value) {
    showConfirm.value = false
    confirmIng.value = null
  }
  if (showEdit.value) closeEdit()
}

onMounted(() => {
  loadIngredients()
  document.addEventListener('keydown', onDocKeydown)
})

onUnmounted(() => {
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
  .form-grid {
    grid-template-columns: 1fr;
  }
}

.ingredient-info {
  flex: 1;
  min-width: 0;
}

.ingredient-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  gap: 0.35rem;
}

.low-stock {
  border-left: 3px solid var(--olive-bright);
}

.button--danger-ghost:hover {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.35);
  color: var(--danger-soft);
}

.button--danger {
  color: #fff;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 10px 26px rgba(239, 68, 68, 0.28);
}

.button--danger:hover {
  background: linear-gradient(135deg, #f54545, #e11d1d);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    0 14px 30px rgba(239, 68, 68, 0.35);
}

.button--danger:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 640px) {
  .ingredient-controls {
    flex-direction: column;
    align-items: flex-end;
  }
}
</style>
