<template>
  <header class="header">
    <div class="header-content">
      <div class="header-left">
        <h1 class="app-title">视频内容理解</h1>
      </div>
      <div class="header-right">
        <!-- 主题切换 -->
        <button
          class="header-btn"
          @click="toggleTheme"
          :title="themeStore.theme === 'light' ? '切换到深色模式' : '切换到浅色模式'"
        >
          <svg
            v-if="themeStore.theme === 'light'"
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
          >
            <path
              d="M10 3V1M10 19V17M17 10H19M1 10H3M15.657 15.657L17.071 17.071M2.929 2.929L4.343 4.343M15.657 4.343L17.071 2.929M2.929 17.071L4.343 15.657M14 10C14 12.2091 12.2091 14 10 14C7.79086 14 6 12.2091 6 10C6 7.79086 7.79086 6 10 6C12.2091 6 14 7.79086 14 10Z"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
          <svg
            v-else
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
          >
            <path
              d="M10 3C11.3807 3 12.5 4.11929 12.5 5.5C12.5 6.88071 11.3807 8 10 8C8.61929 8 7.5 6.88071 7.5 5.5C7.5 4.11929 8.61929 3 10 3Z"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
            <path
              d="M10 1V3M10 17V19M3 10H1M19 10H17M4.34315 4.34315L5.75736 5.75736M14.2426 14.2426L15.6569 15.6569M4.34315 15.6569L5.75736 14.2426M14.2426 5.75736L15.6569 4.34315"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </button>

        <!-- 用户信息 -->
        <div class="user-menu" v-if="userStore.isAuthenticated">
          <div class="user-info">
            <span class="username">{{ userStore.user?.username || '用户' }}</span>
          </div>
          <button class="header-btn logout-btn" @click="handleLogout" title="退出登录">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M7 17L12 12L7 7M12 12H2"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const themeStore = useThemeStore()
const userStore = useUserStore()
const router = useRouter()

const toggleTheme = () => {
  themeStore.toggleTheme()
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  height: 60px;
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.header-btn:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid var(--border-light);
}

.user-info {
  display: flex;
  align-items: center;
}

.username {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.logout-btn {
  margin-left: 4px;
}
</style>

