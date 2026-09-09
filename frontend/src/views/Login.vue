<template>
  <div class="login-screen">
    <div class="login-card">
      <div class="login-header">
        <div class="login-brand">
          <div class="login-brand__icon">
            <UiIcon name="shield" :size="32" />
          </div>
          <div class="login-brand__text">
            <h1 class="login-brand__title">Cafe Management</h1>
            <p class="login-brand__subtitle">Staff Portal</p>
          </div>
        </div>
        <div class="login-form-header">
          <h2 class="login-form__title">Войти в систему</h2>
          <p class="login-form__subtitle">Введите учетные данные для доступа к системе</p>
        </div>
      </div>

      <div class="login-form-wrapper">
        <form class="login-form" @submit.prevent="login">
          <div class="form-group">
            <label class="form-label" for="email">Email</label>
            <div class="input-wrapper">
              <UiIcon name="user" :size="18" class="input-icon" />
              <input
                id="email"
                v-model="email"
                class="input input--leading-icon"
                type="email"
                placeholder="admin@cafe.test"
                required
                autocomplete="email"
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="password">Пароль</label>
            <div class="input-wrapper">
              <UiIcon name="shield" :size="18" class="input-icon" />
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="input input--leading-icon input--trailing-btn"
                required
                autocomplete="current-password"
              />
              <button
                type="button"
                class="password-toggle"
                :title="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <UiIcon :name="showPassword ? 'eye-off' : 'eye'" :size="18" />
              </button>
            </div>
          </div>

          <div class="form-actions-row">
            <label class="checkbox-group">
              <input v-model="rememberMe" type="checkbox" />
              <span class="checkbox-label">Запомнить меня</span>
            </label>
          </div>

          <button
            type="submit"
            class="button login-submit-btn"
            :disabled="loading"
          >
            <span v-if="loading" class="button-content">
              <UiIcon name="refresh-cw" :size="18" class="spinner" />
              <span>Вход в систему...</span>
            </span>
            <span v-else class="button-content">
              <span>Войти в систему</span>
              <UiIcon name="log-out" :size="18" class="arrow-icon" />
            </span>
          </button>

          <transition name="fade">
            <p v-if="error" class="login-error">
              <UiIcon name="alert-circle" :size="18" />
              <span>{{ error }}</span>
            </p>
          </transition>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAppStore } from '../stores'
import UiIcon from '../components/UiIcon.vue'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(true)
const loading = ref(false)
const error = ref('')

const router = useRouter()
const route = useRoute()
const store = useAppStore()

async function login() {
  loading.value = true
  error.value = ''

  try {
    const form = new URLSearchParams()
    form.append('username', email.value)
    form.append('password', password.value)

    const response = await api.post('/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    store.setToken(response.data.access_token, rememberMe.value)

    const [me, profileResponse] = await Promise.all([
      api.get('/auth/me'),
      api.get('/profile/me')
    ])

    store.setUser({
      id: me.data.id,
      email: me.data.email,
      full_name: profileResponse.data.full_name || me.data.full_name || me.data.email,
      role: me.data.role,
      avatar: profileResponse.data.avatar || ''
    })

    if (profileResponse.data.dashboard_preferences) {
      store.setDashboardPreferences(profileResponse.data.dashboard_preferences)
    }

    if (profileResponse.data.socials) {
      store.setSocialLinks(profileResponse.data.socials)
    }

    const roleRedirects: Record<string, string> = {
      admin: '/',
      cashier: '/floor',
      waiter: '/floor',
      chef: '/kitchen'
    }

    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : roleRedirects[me.data.role] || '/'

    await router.push(redirect)
  } catch (err) {
    error.value = 'Неверный email или пароль'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-screen {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  box-sizing: border-box;
  background: radial-gradient(circle at 50% 50%, rgba(34, 197, 94, 0.06) 0%, transparent 60%);
}

.login-card {
  width: min(100%, 420px);
  margin: 0 auto;
  flex-shrink: 0;
  background: var(--surface-strong);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-radius: 36px;
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.3),
    0 30px 70px var(--shadow),
    inset 0 1px 0 var(--overlay-07);
  padding: 3rem 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  text-align: center;
}

.login-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.login-brand__icon {
  width: 4.5rem;
  height: 4.5rem;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--forest-dark), var(--forest-mid));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow:
    0 10px 25px rgba(34, 197, 94, 0.28),
    inset 0 1px 1px rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.login-brand__icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: -50%;
  width: 200%;
  height: 100%;
  background: linear-gradient(
    to right,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.3) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  transform: skewX(-25deg);
  animation: shine 6s infinite ease-in-out;
}

@keyframes shine {
  0% { left: -100%; }
  35% { left: 100%; }
  100% { left: 100%; }
}

.login-brand__title {
  font-size: 1.85rem;
  font-weight: 850;
  color: var(--text-strong);
  letter-spacing: -0.03em;
  line-height: 1.1;
  margin: 0;
}

.login-brand__subtitle {
  font-size: 0.8rem;
  color: var(--forest-light);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin: 0.25rem 0 0;
}

.login-form-header {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.login-form__title {
  font-size: 1.25rem;
  font-weight: 750;
  color: var(--text-strong);
  margin: 0;
  letter-spacing: -0.01em;
}

.login-form__subtitle {
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.4;
  margin: 0;
}

.login-form-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.82rem;
  font-weight: 650;
  color: var(--text-control);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1.25rem;
  color: var(--muted);
  pointer-events: none;
  transition: color 0.25s ease;
  z-index: 1;
}

.input--leading-icon {
  padding-left: 3.25rem;
}

.input:focus + .input-icon,
.input-wrapper:focus-within .input-icon {
  color: var(--text);
}

.input--trailing-btn {
  padding-right: 3.25rem;
}

.password-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  transition: color 0.2s ease, background 0.2s ease;
  z-index: 1;
}

.password-toggle:hover {
  color: var(--text);
  background: var(--overlay-06);
}

.form-actions-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.25rem;
}

.checkbox-group {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-group input[type="checkbox"] {
  width: 1.1rem;
  height: 1.1rem;
  cursor: pointer;
  accent-color: var(--forest-dark);
  border: 1.5px solid var(--neutral-light);
  border-radius: 4px;
  transition: all 0.2s;
}

.checkbox-label {
  font-size: 0.85rem;
  color: var(--text-control);
  font-weight: 550;
}

.login-submit-btn {
  width: 100%;
  padding: 1rem 1.5rem;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 700;
  border: none;
  color: white;
  background: linear-gradient(135deg, var(--forest-dark) 0%, var(--forest-mid) 100%);
  cursor: pointer;
  box-shadow:
    0 4px 12px rgba(34, 197, 94, 0.24),
    0 12px 24px rgba(0, 0, 0, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.login-submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--forest-mid) 0%, var(--forest-light) 100%);
  box-shadow:
    0 6px 16px rgba(34, 197, 94, 0.3),
    0 16px 32px rgba(0, 0, 0, 0.4);
  transform: translateY(-1px);
}

.login-submit-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow:
    0 2px 6px rgba(34, 197, 94, 0.2),
    0 4px 12px rgba(0, 0, 0, 0.3);
}

.login-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
}

.spinner {
  animation: spin 1s linear infinite;
}

.arrow-icon {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-submit-btn:hover .arrow-icon {
  transform: translateX(4px);
}

.login-error {
  padding: 0.85rem 1.25rem;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 14px;
  color: var(--danger-soft);
  font-size: 0.85rem;
  font-weight: 550;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  animation: shake 0.4s ease-in-out;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

@media (max-width: 480px) {
  .login-card {
    padding: 2.25rem 1.5rem;
    border-radius: 28px;
    gap: 1.5rem;
  }

  .login-brand__title {
    font-size: 1.6rem;
  }
}
</style>