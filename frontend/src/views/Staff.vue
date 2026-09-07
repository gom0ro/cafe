<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="users" :size="16" />
          <span>Управление командой</span>
        </div>
        <h1 class="hero__title">Персонал</h1>
        <p class="hero__lead">Управление аккаунтами, ролями и базовой структурой команды кафе.</p>
      </div>
      <div class="hero__chip">
        <span>{{ users.length }} сотрудников</span>
      </div>
    </section>

    <section class="glass panel panel--large" style="margin-bottom: 1.5rem;">
      <form @submit.prevent="createUser" class="form-grid">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input 
            v-model="form.email" 
            type="email" 
            placeholder="email@example.com" 
            class="input"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Пароль</label>
          <input 
            v-model="form.password" 
            type="password" 
            placeholder="••••••••" 
            class="input"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Роль</label>
          <div ref="roleDropdownRef" class="role-select">
            <button
              type="button"
              class="role-select__trigger"
              :aria-expanded="roleOpen"
              aria-haspopup="listbox"
              @click="toggleRoleDropdown"
            >
              <span class="role-select__value">{{ getRoleName(form.role) }}</span>
              <span class="role-select__chevron" aria-hidden="true">
                <span class="role-select__chevron-inner" :class="{ 'role-select__chevron--open': roleOpen }"></span>
              </span>
            </button>

            <Transition name="role-dropdown">
              <div v-if="roleOpen" class="role-select__menu" role="listbox" :aria-expanded="roleOpen">
                <button
                  v-for="opt in roleOptions"
                  :key="opt.value"
                  type="button"
                  class="role-select__option"
                  :class="{ 'role-select__option--selected': opt.value === form.role }"
                  role="option"
                  :aria-selected="opt.value === form.role"
                  @click="selectRole(opt.value)"
                >
                  <span>{{ opt.label }}</span>
                  <UiIcon v-if="opt.value === form.role" name="check" :size="16" />
                </button>
              </div>
            </Transition>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="button button--primary">
            <UiIcon name="plus-circle" :size="18" />
            <span>Создать сотрудника</span>
          </button>
        </div>
      </form>
    </section>

    <div v-if="loading" class="list">
      <div v-for="n in 4" :key="n" class="skeleton" style="height: 5rem; border-radius: 24px;"></div>
    </div>

    <div v-else class="list">
      <div v-for="user in users" :key="user.id" class="glass-hover panel item" style="display: flex; align-items: center; justify-content: space-between;">
        <div class="user-info">
          <div class="user-avatar">
            <span>{{ getInitials(user.full_name || user.email) }}</span>
          </div>
          <div>
            <div class="item__title">{{ user.full_name || user.email }}</div>
            <div class="item__sub">{{ getRoleName(user.role) }}</div>
          </div>
        </div>
        <div class="user-actions">
          <span class="status-badge" :class="user.is_active ? 'status-badge--success' : 'status-badge--danger'">
            <span class="status-dot"></span>
            <span>{{ user.is_active ? 'Активен' : 'Отключён' }}</span>
          </span>
          <div class="button-group">
            <button class="button button--secondary button--sm" title="Редактировать" @click="openEdit(user)">
              <UiIcon name="edit" :size="14" />
            </button>
            <button class="button button--secondary button--sm button--danger-ghost" title="Удалить сотрудника" @click="confirmUser = user; showConfirm = true">
              <UiIcon name="trash" :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <AppModal v-model="showConfirm" title="Удалить сотрудника?">
      <p class="modal__text">
        Вы уверены, что хотите удалить «{{ confirmUser?.full_name || confirmUser?.email }}»?
        История его заказов сохранится, но смена и профиль будут удалены.
      </p>
      <div class="modal__actions">
        <button type="button" class="button button--ghost" @click="showConfirm = false; confirmUser = null">Отмена</button>
        <button type="button" class="button button--danger" :disabled="deletingUser" @click="deleteUser">
          <UiIcon name="trash" :size="16" />
          <span>{{ deletingUser ? 'Удаление...' : 'Удалить' }}</span>
        </button>
      </div>
    </AppModal>

    <AppModal v-model="showEdit" title="Редактировать сотрудника">
      <div class="modal__body">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input
            v-model="editForm.email"
            type="email"
            placeholder="email@example.com"
            class="input"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">Роль</label>
          <div ref="editRoleDropdownRef" class="role-select">
            <button
              type="button"
              class="role-select__trigger"
              :aria-expanded="editRoleOpen"
              aria-haspopup="listbox"
              @click="toggleEditRoleDropdown"
            >
              <span class="role-select__value">{{ getRoleName(editForm.role) }}</span>
              <span class="role-select__chevron" aria-hidden="true">
                <span class="role-select__chevron-inner" :class="{ 'role-select__chevron--open': editRoleOpen }"></span>
              </span>
            </button>

            <Transition name="role-dropdown">
              <div v-if="editRoleOpen" class="role-select__menu" role="listbox">
                <button
                  v-for="opt in roleOptions"
                  :key="opt.value"
                  type="button"
                  class="role-select__option"
                  :class="{ 'role-select__option--selected': opt.value === editForm.role }"
                  role="option"
                  :aria-selected="opt.value === editForm.role"
                  @click="selectEditRole(opt.value)"
                >
                  <span>{{ opt.label }}</span>
                  <UiIcon v-if="opt.value === editForm.role" name="check" :size="16" />
                </button>
              </div>
            </Transition>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Статус</label>
          <button
            type="button"
            class="status-toggle"
            :class="{ 'status-toggle--on': editForm.is_active }"
            role="switch"
            :aria-checked="editForm.is_active"
            @click="editForm.is_active = !editForm.is_active"
          >
            <span class="status-toggle__track">
              <span class="status-toggle__thumb"></span>
            </span>
            <span class="status-toggle__label">{{ editForm.is_active ? 'Активен' : 'Отключён' }}</span>
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

interface User {
  id: number
  email: string
  full_name?: string
  role: string
  is_active: boolean
}

const users = ref<User[]>([])
const loading = ref(true)

const form = ref({
  email: '',
  password: '',
  role: 'waiter'
})

const roleNames: Record<string, string> = {
  admin: 'Администратор',
  cashier: 'Кассир',
  waiter: 'Официант',
  chef: 'Повар'
}

const roleOptions = [
  { value: 'waiter', label: 'Официант' },
  { value: 'cashier', label: 'Кассир' },
  { value: 'chef', label: 'Повар' },
  { value: 'admin', label: 'Администратор' }
]

const roleDropdownRef = ref<HTMLElement | null>(null)
const roleOpen = ref(false)

const editRoleDropdownRef = ref<HTMLElement | null>(null)
const editRoleOpen = ref(false)

const editingUser = ref<User | null>(null)
const showEdit = ref(false)
const editSaving = ref(false)
const confirmUser = ref<User | null>(null)
const showConfirm = ref(false)
const deletingUser = ref(false)
const editForm = ref({
  email: '',
  role: 'waiter',
  is_active: true
})

const getRoleName = (role: string): string => {
  return roleNames[role] || role
}

function toggleRoleDropdown() {
  roleOpen.value = !roleOpen.value
}

function selectRole(value: string) {
  form.value.role = value
  roleOpen.value = false
}

function toggleEditRoleDropdown() {
  editRoleOpen.value = !editRoleOpen.value
}

function selectEditRole(value: string) {
  editForm.value.role = value
  editRoleOpen.value = false
}

function openEdit(user: User) {
  editingUser.value = user
  editForm.value = {
    email: user.email,
    role: user.role,
    is_active: user.is_active
  }
  editRoleOpen.value = false
  showEdit.value = true
}

function closeEdit() {
  editingUser.value = null
  editSaving.value = false
  editRoleOpen.value = false
  showEdit.value = false
}

async function saveEdit() {
  const user = editingUser.value
  if (!user) return
  if (!editForm.value.email) {
    alert('Email не может быть пустым')
    return
  }

  editSaving.value = true
  try {
    await api.put(`/staff/${user.id}`, {
      email: editForm.value.email,
      role: editForm.value.role,
      is_active: editForm.value.is_active
    })
    closeEdit()
    await loadUsers()
  } catch (e) {
    console.error('Failed to update user:', e)
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    alert(typeof detail === 'string' ? detail : 'Ошибка при сохранении изменений')
  } finally {
    editSaving.value = false
  }
}

async function deleteUser() {
  const user = confirmUser.value
  if (!user) return
  deletingUser.value = true
  try {
    await api.delete(`/staff/${user.id}`)
    users.value = users.value.filter((u) => u.id !== user.id)
confirmUser.value = null
    showConfirm.value = false
  } catch (e) {
    console.error('Failed to delete user:', e)
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    alert(typeof detail === 'string' ? detail : 'Не удалось удалить сотрудника')
  } finally {
    deletingUser.value = false
  }
}

function onDocClick(event: MouseEvent) {
  if (roleDropdownRef.value && !roleDropdownRef.value.contains(event.target as Node)) {
    roleOpen.value = false
  }
  if (editRoleDropdownRef.value && !editRoleDropdownRef.value.contains(event.target as Node)) {
    editRoleOpen.value = false
  }
}

function onDocKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    roleOpen.value = false
    editRoleOpen.value = false
    if (showEdit.value) closeEdit()
    if (showConfirm.value) {
      showConfirm.value = false
      confirmUser.value = null
    }
  }
}

const getInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '??'
  const first = parts[0][0] ?? '?'
  const second = parts[1]?.[0] ?? ''
  return (first + second).toUpperCase()
}

async function loadUsers() {
  loading.value = true
  try {
    const r = await api.get<User[]>('/staff/')
    users.value = r.data
  } catch (e) {
    console.error('Failed to load users:', e)
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!form.value.email || !form.value.password) {
    alert('Пожалуйста, заполните все обязательные поля')
    return
  }

  try {
    await api.post('/staff/', {
      email: form.value.email,
      password: form.value.password,
      role: form.value.role
    })

    form.value = { email: '', password: '', role: 'waiter' }
    await loadUsers()
  } catch (e) {
    console.error('Failed to create user:', e)
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    alert(typeof detail === 'string' ? detail : 'Ошибка при создании сотрудника')
  }
}

onMounted(() => {
  loadUsers()
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onDocKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
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

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 3rem;
  height: 3rem;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--forest-dark), var(--olive-bright));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.button-group {
  display: flex;
  gap: 0.4rem;
}

@media (max-width: 480px) {
  .user-actions {
    flex-direction: column;
    align-items: flex-end;
  }
}

/* ===== Custom Role Dropdown ===== */
.role-select {
  position: relative;
}

.role-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
  min-height: 3.25rem;
  padding: 0.95rem 1.25rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text);
  text-align: left;
  cursor: pointer;
  background: var(--control-bg);
  border: 1px solid var(--control-border);
  border-radius: 16px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  box-shadow:
    inset 0 1px 0 var(--overlay-04),
    0 10px 26px rgba(0, 0, 0, 0.18);
  transition: border-color 0.25s ease, box-shadow 0.35s ease, background 0.3s ease;
}

.role-select__trigger:hover {
  background: var(--control-bg-hover);
  border-color: var(--control-border-hover);
}

.role-select__trigger:focus-visible {
  border-color: var(--forest-mid);
  box-shadow:
    0 0 0 5px rgba(34, 197, 94, 0.13),
    0 0 0 1.5px rgba(34, 197, 94, 0.8),
    inset 0 1px 0 var(--overlay-05);
}

.role-select__trigger[aria-expanded='true'] {
  background: var(--control-bg-focus);
  border-color: var(--forest-mid);
  box-shadow:
    0 0 0 5px rgba(34, 197, 94, 0.13),
    0 0 0 1.5px rgba(34, 197, 94, 0.8),
    inset 0 1px 0 var(--overlay-05);
}

.role-select__value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-select__chevron {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 1.1rem;
  height: 1.1rem;
}

.role-select__chevron-inner {
  width: 0.6rem;
  height: 0.6rem;
  border-right: 2px solid var(--control-arrow);
  border-bottom: 2px solid var(--control-arrow);
  transform: rotate(45deg) translateY(-2px);
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.role-select__chevron--open {
  transform: rotate(225deg) translateY(0);
}

.role-select__menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  z-index: 100;
  min-width: 100%;
  padding: 0.35rem;
  background: var(--surface-strong);
  -webkit-backdrop-filter: blur(24px);
  backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow-soft);
  transform-origin: top center;
}

.role-select__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
  padding: 0.7rem 0.9rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-control);
  text-align: left;
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 10px;
  outline: none;
  transition: background 0.16s ease, color 0.16s ease;
}

.role-select__option:hover {
  background: var(--overlay-06);
  color: var(--text-strong);
}

.role-select__option--selected {
  color: var(--accent);
}

.role-select__option--selected:hover {
  color: var(--accent);
}

.role-dropdown-enter-active,
.role-dropdown-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top center;
}

.role-dropdown-enter-from,
.role-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

/* ===== Status toggle ===== */
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

/* ===== Edit modal ===== */
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

.button--danger-ghost:hover {
  background: rgba(239, 68, 68, 0.14);
  border-color: rgba(239, 68, 68, 0.35);
  color: var(--danger-soft);
}

@media (max-width: 480px) {
  .user-actions {
    flex-direction: column;
    align-items: flex-end;
  }
}
</style>
