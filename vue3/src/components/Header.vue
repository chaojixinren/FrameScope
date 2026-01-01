<template>
  <header class="app-header">
    <div class="app-header__inner">
      <div class="app-brand">
        <div class="brand-mark" aria-hidden="true">◈</div>
        <div class="brand-text">
          <div class="brand-title">FrameScope</div>
          <div class="brand-subtitle">Future Tech Video Console</div>
        </div>
      </div>

      <div class="app-actions">
        <button
          type="button"
          class="btn btn--ghost icon-btn"
          @click="toggleTheme"
          :aria-pressed="themeStore.theme === 'dark'"
          :title="themeStore.theme === 'light' ? '切换到深色模式' : '切换到浅色模式'"
        >
          <svg
            v-if="themeStore.theme === 'light'"
            width="18"
            height="18"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
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
            width="18"
            height="18"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
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

        <div v-if="userStore.isAuthenticated" class="user-chip">
          <span class="user-name">{{ userStore.user?.username || '用户' }}</span>
          <button
            type="button"
            class="btn btn--ghost icon-btn"
            @click="handleLogout"
            title="退出登录"
            aria-label="退出登录"
          >
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
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
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--shell-bg);
  border-bottom: 1px solid var(--shell-border);
  backdrop-filter: blur(16px);
}

.app-header__inner {
  height: 64px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.app-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 18px;
  color: var(--primary);
  background: linear-gradient(135deg, rgba(91, 212, 255, 0.18), rgba(139, 123, 255, 0.18));
  border: 1px solid rgba(91, 212, 255, 0.4);
  box-shadow: var(--glow-1);
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.brand-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.brand-subtitle {
  font-size: 12px;
  color: var(--text-tertiary);
  letter-spacing: 0.4px;
  text-transform: uppercase;
}

.app-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.icon-btn {
  width: 38px;
  height: 38px;
  padding: 0;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 12px;
  border-left: 1px solid var(--shell-border);
}

.user-name {
  font-size: 13px;
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .app-header__inner {
    height: auto;
    padding: var(--space-2) var(--space-3);
    flex-direction: column;
    align-items: flex-start;
  }

  .app-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
