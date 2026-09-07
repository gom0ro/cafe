<template>
  <div class="particles-layer" aria-hidden="true">
    <canvas ref="canvas" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const canvas = ref<HTMLCanvasElement | null>(null)
let raf = 0
let removeResize: (() => void) | null = null

function resize(c: HTMLCanvasElement) {
  const dpr = window.devicePixelRatio || 1
  c.width = c.clientWidth * dpr
  c.height = c.clientHeight * dpr
}

onMounted(() => {
  if (!canvas.value) return
  const ctx = canvas.value.getContext('2d')!
  resize(canvas.value)

  const onResize = () => {
    if (canvas.value) resize(canvas.value)
  }
  window.addEventListener('resize', onResize)
  removeResize = () => window.removeEventListener('resize', onResize)

  const particles = Array.from({ length: 30 }).map(() => ({
    x: Math.random() * canvas.value!.width,
    y: Math.random() * canvas.value!.height,
    r: Math.random() * 2 + 0.5,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5
  }))

  function draw() {
    if (!canvas.value) return
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
    ctx.globalAlpha = 0.8
    const isLight = document.documentElement.getAttribute('data-theme') === 'light'
    ctx.fillStyle = isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)'
    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      if (p.x < 0) p.x = canvas.value.width
      if (p.x > canvas.value.width) p.x = 0
      if (p.y < 0) p.y = canvas.value.height
      if (p.y > canvas.value.height) p.y = 0
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
    }
    raf = requestAnimationFrame(draw)
  }
  raf = requestAnimationFrame(draw)
})

onUnmounted(() => {
  removeResize?.()
  cancelAnimationFrame(raf)
})
</script>

<style scoped>
.particles-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
