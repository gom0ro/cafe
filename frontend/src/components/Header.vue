<template>
  <header class="app-topbar">
    <div class="brand">
      <div class="brand__mark">CF</div>
      <div class="brand__text">
        <div class="brand__title">Cafe Management</div>
        <div class="brand__subtitle">Premium POS & operations</div>
      </div>
    </div>
    <nav class="nav">
      <router-link to="/" class="nav-link">Dashboard</router-link>
      <router-link to="/pos" class="nav-link">Касса</router-link>
      <router-link to="/menu" class="nav-link">Меню</router-link>
      <router-link to="/staff" class="nav-link">Персонал</router-link>
      <router-link to="/inventory" class="nav-link">Склад</router-link>
      <router-link to="/analytics" class="nav-link">Аналитика</router-link>
    </nav>
  </header>
</template>

<script setup lang="ts"></script>

<style scoped></style>
