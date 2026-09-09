<template>
  <div ref="rootRef" class="ui-select">
    <label v-if="label" class="form-label">{{ label }}</label>

    <button
      type="button"
      class="ui-select__trigger"
      :class="{ 'ui-select__trigger--open': open }"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
    >
      <span class="ui-select__value" :class="{ 'ui-select__value--placeholder': !selected }">
        {{ selected?.label || placeholder }}
      </span>
      <span class="ui-select__chevron" aria-hidden="true">
        <span class="ui-select__chevron-inner" :class="{ 'ui-select__chevron--open': open }"></span>
      </span>
    </button>

    <Transition name="ui-select-dropdown">
      <div v-if="open" class="ui-select__menu" role="listbox">
        <button
          v-for="opt in options"
          :key="String(opt.value)"
          type="button"
          class="ui-select__option"
          :class="{ 'ui-select__option--selected': opt.value === modelValue }"
          role="option"
          :aria-selected="opt.value === modelValue"
          @click="choose(opt)"
        >
          <span>{{ opt.label }}</span>
          <UiIcon v-if="opt.value === modelValue" name="check" :size="16" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import UiIcon from './UiIcon.vue'

export interface SelectOption {
  value: unknown
  label: string
}

const props = withDefaults(
  defineProps<{
    modelValue: unknown
    options: SelectOption[]
    label?: string
    placeholder?: string
    disabled?: boolean
  }>(),
  { label: '', placeholder: 'Выберите…', disabled: false }
)

const emit = defineEmits<{ (e: 'update:modelValue', value: unknown): void }>()

const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)

const selected = computed(() => props.options.find((o) => o.value === props.modelValue))

function toggle() {
  if (props.disabled) return
  open.value = !open.value
}

function choose(opt: SelectOption) {
  emit('update:modelValue', opt.value)
  open.value = false
}

function onOutsideClick(event: Event) {
  if (rootRef.value && !rootRef.value.contains(event.target as Node)) {
    open.value = false
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') open.value = false
}

onMounted(() => {
  document.addEventListener('click', onOutsideClick)
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', onOutsideClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.ui-select {
  position: relative;
}

.ui-select__trigger {
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

.ui-select__trigger:hover {
  background: var(--control-bg-hover);
  border-color: var(--control-border-hover);
}

.ui-select__trigger:focus-visible,
.ui-select__trigger--open {
  border-color: var(--forest-mid);
  box-shadow:
    0 0 0 5px rgba(34, 197, 94, 0.13),
    0 0 0 1.5px rgba(34, 197, 94, 0.8),
    inset 0 1px 0 var(--overlay-05);
}

.ui-select__value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ui-select__value--placeholder {
  color: var(--placeholder);
}

.ui-select__chevron {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 1.1rem;
  height: 1.1rem;
}

.ui-select__chevron-inner {
  width: 0.6rem;
  height: 0.6rem;
  border-right: 2px solid var(--control-arrow);
  border-bottom: 2px solid var(--control-arrow);
  transform: rotate(45deg) translateY(-2px);
  transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.ui-select__chevron--open {
  transform: rotate(225deg) translateY(0);
}

.ui-select__menu {
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

.ui-select__option {
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

.ui-select__option:hover {
  background: var(--overlay-06);
  color: var(--text-strong);
}

.ui-select__option--selected,
.ui-select__option--selected:hover {
  color: var(--accent);
}

.ui-select-dropdown-enter-active,
.ui-select-dropdown-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top center;
}

.ui-select-dropdown-enter-from,
.ui-select-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>