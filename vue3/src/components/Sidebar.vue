<template>
  <aside
    class="sidebar"
    :class="{ collapsed: isCollapsed }"
  >
    <div class="sidebar-header">
      <button
        v-if="!isCollapsed"
        class="sidebar-toggle"
        @click="toggleCollapse"
        title="收起"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M6 4L14 10L6 16V4Z"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <button
        v-else
        class="sidebar-toggle"
        @click="toggleCollapse"
        title="展开"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path
            d="M14 4L6 10L14 16V4Z"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </button>
      <h2 v-if="!isCollapsed" class="sidebar-title">对话历史</h2>
    </div>

    <div v-if="!isCollapsed" class="sidebar-content">
      <button
        class="new-task-btn"
        @click="createNewConversation"
        :disabled="loading"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M8 3V13M3 8H13"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          />
        </svg>
        {{ loading ? '加载中...' : '新建对话' }}
      </button>

      <div class="task-list">
        <div
          v-for="conversation in conversations"
          :key="conversation.id"
          class="task-item"
          :class="{ active: currentConversation?.id === conversation.id }"
          @click="selectConversation(conversation)"
        >
          <div class="task-item-header">
            <span class="task-title">{{ conversation.title || '未命名对话' }}</span>
            <span v-if="conversation.message_count" class="task-status completed">
              {{ conversation.message_count }}条
            </span>
          </div>
          <div class="task-meta">
            {{ formatDate(conversation.updated_at) }}
          </div>
        </div>

        <div v-if="!loading && conversations.length === 0" class="empty-state">
          <p class="text-secondary">暂无对话</p>
          <p class="text-tertiary">点击"新建对话"开始</p>
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

const createNewConversation = () => {
  router.push({ name: 'Home' })
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

// 组件挂载时加载对话列表
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
  width: 260px;
  height: 100vh;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle {
  width: 32px;
  height: 32px;
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

.sidebar-toggle:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.new-task-btn {
  width: 100%;
  padding: 10px 14px;
  background-color: var(--accent-blue);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.new-task-btn:hover {
  background-color: var(--accent-blue-hover);
}

.task-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-item {
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.task-item:hover {
  background-color: var(--hover-bg);
}

.task-item.active {
  background-color: var(--bg-primary);
  border-color: var(--border-light);
}

.task-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 4px;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.task-status.pending {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.task-status.processing {
  background-color: var(--accent-blue-light);
  color: var(--accent-blue);
}

.task-status.completed {
  background-color: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.task-status.error {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.task-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

.empty-state {
  padding: 32px 16px;
  text-align: center;
}

.empty-state p {
  font-size: 14px;
  margin: 4px 0;
}
</style>

