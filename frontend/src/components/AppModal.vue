<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-backdrop" @click.self="$emit('update:modelValue', false)">
        <div class="modal" role="dialog" aria-modal="true">
          <div class="modal__header">
            <h3 class="modal__title"><slot name="title">{{ title }}</slot></h3>
            <button type="button" class="modal__close" title="Закрыть" @click="$emit('update:modelValue', false)">
              <UiIcon name="x" :size="16" />
            </button>
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import UiIcon from './UiIcon.vue'

withDefaults(defineProps<{
  modelValue: boolean
  title?: string
}>(), {
  title: ''
})

defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  background: var(--overlay-60);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
}

.modal {
  width: min(460px, 100%);
  padding: 1.4rem;
  background: var(--surface-strong);
  -webkit-backdrop-filter: blur(24px);
  backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-radius: 22px;
  box-shadow: var(--shadow-soft);
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.modal__title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 800;
}

.modal__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  border-radius: 10px;
  cursor: pointer;
  background: var(--overlay-04);
  border: 1px solid var(--border);
  color: var(--text-control);
  transition: background 0.16s ease, color 0.16s ease;
}

.modal__close:hover {
  background: var(--overlay-09);
  color: var(--text-strong);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.22s ease;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: translateY(14px) scale(0.97);
}
</style>