<template>
  <div class="page">
    <section class="hero">
      <div>
        <div class="hero__eyebrow">
          <UiIcon name="settings" :size="16" />
          <span>Настройки профиля</span>
        </div>
        <h1 class="hero__title">Настройки и профиль</h1>
        <p class="hero__lead">Редактирование данных сотрудника.</p>
      </div>
      <div class="hero__chip">
        <UiIcon name="log-out" :size="14" />
        <span>Профиль</span>
      </div>
    </section>

    <section class="content-grid">
      <article class="glass panel panel--large">
        <h2 class="section-heading">
          <UiIcon name="user" :size="20" />
          <span>Личные данные</span>
        </h2>

        <form class="settings-form" @submit.prevent="saveProfile">
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">Имя и фамилия</label>
              <input v-model="profile.full_name" class="input" placeholder="Иван Петров" />
            </div>

            <div class="form-group">
              <label class="form-label">Аватар</label>
              <input v-model="profile.avatar" class="input" placeholder="URL изображения" />
            </div>
          </div>

          <div class="toolbar" style="margin-top: 1.5rem;">
            <button type="submit" class="button button--primary">
              <UiIcon name="check-circle" :size="18" />
              <span>Сохранить профиль</span>
            </button>
            <button type="button" class="button button--secondary" @click="resetProfile">
              <UiIcon name="refresh-cw" :size="18" />
              <span>Сбросить</span>
            </button>
          </div>
        </form>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import api from '../api'
import UiIcon from '../components/UiIcon.vue'

const profile = reactive({
  full_name: '',
  avatar: ''
})

async function loadProfile() {
  try {
    const response = await api.get('/profile/me')
    const data = response.data
    profile.full_name = data.full_name || ''
    profile.avatar = data.avatar || ''
  } catch (e) {
    console.error('Failed to load profile:', e)
  }
}

async function saveProfile() {
  try {
    await api.put('/profile/me', { ...profile })
  } catch (e) {
    console.error('Failed to save profile:', e)
    alert('Ошибка при сохранении профиля')
  }
}

function resetProfile() {
  profile.full_name = ''
  profile.avatar = ''
}

onMounted(() => {
  loadProfile()
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
</style>
