<template>
  <div
    v-if="displayActive"
    class="tech-loader"
    :class="[
      `tech-loader--${variant}`,
      `tech-loader--${size}`,
      `tech-loader--${mode}`,
      { 'is-finishing': finishing }
    ]"
    role="status"
    aria-live="polite"
    :aria-busy="active ? 'true' : 'false'"
  >
    <div v-if="variant === 'overlay'" class="tech-loader__backdrop" aria-hidden="true"></div>
    <div class="tech-loader__card">
      <div class="tech-loader__visual" aria-hidden="true">
        <div v-if="mode === 'ring'" class="holo-ring">
          <div class="holo-ring__core"></div>
          <div class="holo-ring__pulse"></div>
          <div class="holo-ring__spark"></div>
        </div>
        <div v-else-if="mode === 'scan'" class="scan-bar">
          <div class="scan-bar__grid"></div>
          <div class="scan-bar__line"></div>
          <div class="scan-bar__pulse"></div>
        </div>
        <div v-else class="tech-skeleton">
          <span class="tech-skeleton__line"></span>
          <span class="tech-skeleton__line"></span>
          <span class="tech-skeleton__line tech-skeleton__line--short"></span>
        </div>
      </div>

      <div v-if="hasText" class="tech-loader__text">
        <slot>{{ text }}</slot>
      </div>

      <div v-if="showProgress" class="tech-loader__progress" aria-hidden="true">
        <div class="tech-loader__bar" :style="{ width: `${progress}%` }"></div>
      </div>

      <span class="sr-only">{{ ariaText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useSlots, watch } from 'vue'

type Variant = 'overlay' | 'inline' | 'button'
type Size = 'sm' | 'md' | 'lg'
type Mode = 'ring' | 'scan' | 'skeleton'

const props = withDefaults(defineProps<{
  variant: Variant
  size: Size
  text?: string
  showProgress?: boolean
  active: boolean
  mode: Mode
}>(), {
  variant: 'inline',
  size: 'md',
  text: 'Loading...',
  showProgress: false,
  active: false,
  mode: 'ring'
})

const slots = useSlots()
const displayActive = ref(false)
const finishing = ref(false)
const progress = ref(0)
const hasText = computed(() => Boolean(slots.default || props.text))
const ariaText = computed(() => props.text || 'Loading...')

let progressTimer: number | undefined

const clearProgress = () => {
  if (progressTimer) {
    window.clearInterval(progressTimer)
    progressTimer = undefined
  }
}

const startProgress = () => {
  if (!props.showProgress || typeof window === 'undefined') return
  clearProgress()
  let current = 0
  progress.value = 0
  progressTimer = window.setInterval(() => {
    if (!props.active) return
    const increment = Math.random() * 4 + 1.2
    current = Math.min(90, current + increment)
    progress.value = Math.round(current)
    if (current >= 90) {
      clearProgress()
    }
  }, 180)
}

const finishAndHide = () => {
  if (!props.showProgress) {
    displayActive.value = false
    return
  }
  finishing.value = true
  progress.value = 100
  window.setTimeout(() => {
    finishing.value = false
    displayActive.value = false
    progress.value = 0
  }, 200)
}

watch(
  () => props.active,
  (active) => {
    if (active) {
      displayActive.value = true
      finishing.value = false
      startProgress()
    } else {
      clearProgress()
      finishAndHide()
    }
  },
  { immediate: true }
)

watch(
  () => props.showProgress,
  (show) => {
    if (props.active && show) {
      startProgress()
      return
    }
    if (!show) {
      clearProgress()
      progress.value = 0
    }
  }
)

onBeforeUnmount(() => {
  clearProgress()
})
</script>

<style scoped>
.tech-loader {
  --bg: rgba(10, 16, 28, 0.78);
  --panel: rgba(12, 18, 30, 0.7);
  --primary: #5bd4ff;
  --accent: #8b7bff;
  --glow: 0 0 18px rgba(91, 212, 255, 0.35);
  --radius: 14px;
  --text: #e6eef8;
  --muted: rgba(230, 238, 248, 0.65);
  --grid: rgba(148, 163, 184, 0.12);
  --loader-size: 28px;
  --loader-gap: 10px;
  --text-size: 13px;
  --progress-height: 5px;

  position: relative;
  color: var(--text);
  font-family: inherit;
}

.tech-loader--sm {
  --loader-size: 20px;
  --loader-gap: 8px;
  --text-size: 12px;
  --progress-height: 4px;
}

.tech-loader--md {
  --loader-size: 28px;
  --loader-gap: 10px;
  --text-size: 13px;
  --progress-height: 5px;
}

.tech-loader--lg {
  --loader-size: 100px;
  --loader-gap: 20px;
  --text-size: 20px;
  --progress-height: 10px;
}

.tech-loader--overlay {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  z-index: 9999;
}

.tech-loader__backdrop {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 20%, rgba(91, 212, 255, 0.18), transparent 55%),
    radial-gradient(circle at 80% 30%, rgba(139, 123, 255, 0.16), transparent 50%),
    linear-gradient(180deg, rgba(5, 10, 18, 0.76), rgba(10, 14, 24, 0.9));
}

.tech-loader__backdrop::before,
.tech-loader__backdrop::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.tech-loader__backdrop::before {
  background-image: linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.55;
}

.tech-loader__backdrop::after {
  background-image: radial-gradient(rgba(255, 255, 255, 0.25) 1px, transparent 0);
  background-size: 3px 3px;
  opacity: 0.05;
  mix-blend-mode: soft-light;
}

.tech-loader__card {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: var(--loader-gap);
  padding: 16px 20px;
  border-radius: var(--radius);
  background: var(--panel);
  border: 1px solid rgba(91, 212, 255, 0.25);
  box-shadow: var(--glow);
  backdrop-filter: blur(10px);
  z-index: 1;
  min-width: 180px;
}

.tech-loader--inline .tech-loader__card {
  padding: 12px 14px;
  min-width: unset;
}

.tech-loader--button {
  height: 100%;
  display: inline-flex;
  align-items: center;
}

.tech-loader--button .tech-loader__card {
  padding: 0 12px;
  min-width: unset;
  height: 100%;
  background: transparent;
  border: none;
  box-shadow: none;
  backdrop-filter: none;
}

.tech-loader__visual {
  display: grid;
  place-items: center;
}

.tech-loader__text {
  font-size: var(--text-size);
  color: var(--muted);
  letter-spacing: 0.3px;
}

.tech-loader__progress {
  width: 100%;
  height: var(--progress-height);
  border-radius: 999px;
  background: rgba(91, 212, 255, 0.12);
  overflow: hidden;
  position: relative;
}

.tech-loader__bar {
  height: 100%;
  width: 0%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(91, 212, 255, 0.9), rgba(139, 123, 255, 0.85));
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(91, 212, 255, 0.4);
}

.tech-loader--button .tech-loader__progress {
  width: 120px;
}

.holo-ring {
  width: var(--loader-size);
  height: var(--loader-size);
  border-radius: 50%;
  position: relative;
  background: conic-gradient(from 0deg, rgba(91, 212, 255, 0), rgba(91, 212, 255, 0.8), rgba(139, 123, 255, 0.9), rgba(91, 212, 255, 0));
  -webkit-mask: radial-gradient(circle, transparent 58%, #000 59%);
  mask: radial-gradient(circle, transparent 58%, #000 59%);
  animation: ring-spin 1.6s linear infinite;
}

.holo-ring__core {
  position: absolute;
  inset: 4px;
  border-radius: 50%;
  border: 1px solid rgba(91, 212, 255, 0.2);
  background: radial-gradient(circle, rgba(91, 212, 255, 0.15), transparent 70%);
}

.holo-ring__pulse {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 1px solid rgba(139, 123, 255, 0.2);
  animation: ring-pulse 2.2s ease-in-out infinite;
}

.holo-ring__spark {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(91, 212, 255, 0.55);
  animation: ring-spark 1.8s ease-in-out infinite;
}

.scan-bar {
  width: min(220px, 60vw);
  height: calc(var(--loader-size) * 0.7);
  position: relative;
  border-radius: 12px;
  border: 1px solid rgba(91, 212, 255, 0.2);
  background: rgba(10, 16, 28, 0.45);
  overflow: hidden;
}

.scan-bar__grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 18px 18px;
  opacity: 0.5;
}

.scan-bar__line {
  position: absolute;
  inset: 0;
  height: 3px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(90deg, transparent, rgba(91, 212, 255, 0.9), transparent);
  animation: scan-sweep 1.6s ease-in-out infinite;
}

.scan-bar__pulse {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 50%, rgba(91, 212, 255, 0.2), transparent 45%);
  animation: scan-pulse 2.2s ease-in-out infinite;
}

.tech-skeleton {
  display: grid;
  gap: 6px;
  width: min(220px, 60vw);
}

.tech-skeleton__line {
  height: 12px;
  border-radius: 8px;
  background: rgba(91, 212, 255, 0.12);
  position: relative;
  overflow: hidden;
}

.tech-skeleton__line::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(91, 212, 255, 0.35), transparent);
  transform: translateX(-100%);
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
}

.tech-skeleton__line--short {
  width: 70%;
}

.tech-loader.is-finishing .tech-loader__card::after {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: rgba(91, 212, 255, 0.18);
  animation: finish-flash 0.2s ease-out;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@keyframes ring-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes ring-pulse {
  0%,
  100% {
    opacity: 0.4;
    transform: scale(0.9);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

@keyframes ring-spark {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.9;
  }
}

@keyframes scan-sweep {
  0% {
    transform: translateX(-70%) translateY(-50%);
    opacity: 0.4;
  }
  50% {
    transform: translateX(0%) translateY(-50%);
    opacity: 1;
  }
  100% {
    transform: translateX(70%) translateY(-50%);
    opacity: 0.4;
  }
}

@keyframes scan-pulse {
  0%,
  100% {
    opacity: 0.2;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes skeleton-shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes finish-flash {
  0% {
    opacity: 0;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .holo-ring,
  .holo-ring__pulse,
  .holo-ring__spark,
  .scan-bar__line,
  .scan-bar__pulse,
  .tech-skeleton__line::after {
    animation: none !important;
  }

  .holo-ring {
    background: radial-gradient(circle, rgba(91, 212, 255, 0.5), rgba(91, 212, 255, 0.2));
  }

  .scan-bar__line {
    opacity: 0.6;
  }

  .tech-loader__bar {
    transition: none;
  }
}
</style>
