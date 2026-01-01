<template>
  <div class="main-layout">
    <Sidebar />
    <div class="layout-right">
      <Header />
      <main class="main-content">
        <div
          ref="contentWrapper"
          class="content-wrapper"
          :class="{ 'is-scrolled': isScrolled }"
          @scroll="handleScroll"
        >
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, nextTick, ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import Header from '@/components/Header.vue'
import { useThemeStore } from '@/stores/theme'
import { useTaskStore } from '@/stores/task'

const themeStore = useThemeStore()
const taskStore = useTaskStore()

const contentWrapper = ref<HTMLElement | null>(null)
const isScrolled = ref(false)

const handleScroll = (event?: Event) => {
  const target = event ? (event.target as HTMLElement) : contentWrapper.value
  if (!target) return
  isScrolled.value = target.scrollTop > 0
}

onMounted(() => {
  themeStore.initTheme()
  themeStore.watchSystemTheme()
  taskStore.loadTasks()
  taskStore.watchTasks()
  nextTick(() => handleScroll())
})
</script>

<style scoped>
.main-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: transparent;
}

.layout-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-5);
  transition: box-shadow 0.2s ease;
}

.content-wrapper.is-scrolled {
  box-shadow: inset 0 14px 16px -16px rgba(0, 0, 0, 0.7);
}

@media (max-width: 1200px) {
  .content-wrapper {
    padding: var(--space-4);
  }
}

@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
  }

  .layout-right {
    order: 1;
  }

  :deep(.sidebar) {
    order: 2;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: var(--space-3);
  }
}

@media (max-width: 480px) {
  .content-wrapper {
    padding: var(--space-2);
  }
}
</style>
