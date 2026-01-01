<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }" aria-label="对话导航">
    <div class="sidebar-header">
      <button
        type="button"
        class="btn btn--ghost icon-btn sidebar-toggle"
        @click="toggleCollapse"
        :aria-pressed="isCollapsed"
        :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <svg
          v-if="!isCollapsed"
          width="18"
          height="18"
          viewBox="0 0 20 20"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M6 4L14 10L6 16V4Z"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
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
            d="M14 4L6 10L14 16V4Z"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <div v-if="!isCollapsed" class="sidebar-title">
        <div class="sidebar-title__main">对话历史</div>
        <div class="sidebar-title__sub">Conversation Timeline</div>
      </div>
    </div>

    <div v-if="!isCollapsed" class="sidebar-content">
      <div class="sidebar-section">
        <div class="sidebar-section__title">
          <span>最近对话</span>
          <span class="badge">{{ conversations.length }}</span>
        </div>

        <div v-if="loading && conversations.length === 0" class="task-skeleton">
          <div class="skeleton skeleton-item"></div>
          <div class="skeleton skeleton-item"></div>
          <div class="skeleton skeleton-item"></div>
        </div>

        <div v-else class="task-list" role="list">
          <button
            v-for="conversation in conversations"
            :key="conversation.id"
            type="button"
            class="task-item"
            :class="{ active: currentConversation?.id === conversation.id }"
            :aria-current="currentConversation?.id === conversation.id ? 'page' : undefined"
            @click="selectConversation(conversation)"
          >
            <div class="task-item__top">
              <span class="task-title">{{ conversation.title || '未命名对话' }}</span>
              <span v-if="conversation.message_count" class="tag">
                {{ conversation.message_count }} 条
              </span>
            </div>
            <div class="task-meta">{{ formatDate(conversation.updated_at) }}</div>
          </button>
        </div>

        <div v-if="!loading && conversations.length === 0" class="panel empty-panel">
          <div class="panel__bd empty-state">
            <div class="empty-icon" aria-hidden="true">⎔</div>
            <div class="empty-title">暂无对话</div>
            <div class="empty-desc">创建一个新对话开始分析</div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import type { Conversation } from '@/api/conversation'
import { useRouter } from 'vue-router'

const router = useRouter()
const conversationStore = useConversationStore()

const isCollapsed = ref(false)

const conversations = computed(() => conversationStore.conversations)
const currentConversation = computed(() => conversationStore.currentConversation)
const loading = computed(() => conversationStore.loading)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const selectConversation = (conversation: Conversation) => {
  conversationStore.setCurrentConversation(conversation)
  router.push({
    name: 'Task',
    params: { id: `conversation_${conversation.id}` },
    query: { conversationId: conversation.id }
  })
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    })
  }
}

onMounted(async () => {
  try {
    await conversationStore.loadConversations()
  } catch (error) {
    console.error('加载对话列表失败:', error)
  }
})
</script>

<style scoped>
.sidebar {
  width: 280px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--shell-bg);
  border-right: 1px solid var(--shell-border);
  backdrop-filter: blur(18px);
  transition: width 0.2s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: var(--space-3);
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--shell-border);
}

.sidebar-title__main {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.sidebar-title__sub {
  font-size: 11px;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.icon-btn {
  width: 36px;
  height: 36px;
  padding: 0;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar-section__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: var(--space-2);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  text-align: left;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  border: 1px solid transparent;
  color: var(--text-primary);
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.task-item:hover {
  transform: translateY(-1px);
  border-color: rgba(91, 212, 255, 0.35);
  box-shadow: var(--glow-1);
}

.task-item.active {
  border-color: rgba(91, 212, 255, 0.7);
  background: var(--surface-strong);
}

.task-item__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.task-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.task-skeleton {
  display: grid;
  gap: 8px;
}

.skeleton-item {
  height: 52px;
}

.empty-panel {
  margin-top: var(--space-2);
}

.empty-state {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-icon {
  font-size: 24px;
  color: var(--primary);
}

.empty-title {
  font-size: 14px;
  font-weight: 600;
}

.empty-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

@media (max-width: 1024px) {
  .sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--shell-border);
  }

  .sidebar.collapsed {
    width: 100%;
  }

  .sidebar-content {
    max-height: 40vh;
  }
}
</style>
