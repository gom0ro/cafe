<template>
  <div :class="['skeleton', classes]">
    <div class="w-full h-full"></div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ classes?: string }>(), {
  classes: 'h-6'
})
const classes = props.classes
</script>
