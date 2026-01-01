<template>
  <div class="main-layout">
    <Sidebar />
    <div class="layout-right">
      <Header />
      <main class="main-content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import Header from '@/components/Header.vue'
import { useThemeStore } from '@/stores/theme'
import { useTaskStore } from '@/stores/task'

const themeStore = useThemeStore()
const taskStore = useTaskStore()

onMounted(() => {
  themeStore.initTheme()
  themeStore.watchSystemTheme()
  taskStore.loadTasks()
  taskStore.watchTasks()
})
</script>

<style scoped>
.main-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.layout-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--bg-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}
</style>

