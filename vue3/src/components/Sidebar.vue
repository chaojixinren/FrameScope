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
      <h2 v-if="!isCollapsed" class="sidebar-title">历史任务</h2>
    </div>

    <div v-if="!isCollapsed" class="sidebar-content">
      <button
        class="new-task-btn"
        @click="createNewTask"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M8 3V13M3 8H13"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          />
        </svg>
        新建任务
      </button>

      <div class="task-list">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="task-item"
          :class="{ active: currentTask?.id === task.id }"
          @click="selectTask(task)"
        >
          <div class="task-item-header">
            <span class="task-title">{{ task.title || '未命名任务' }}</span>
            <span class="task-status" :class="task.status">
              {{ statusText[task.status] }}
            </span>
          </div>
          <div class="task-meta">
            {{ formatDate(task.updatedAt) }}
          </div>
        </div>

        <div v-if="tasks.length === 0" class="empty-state">
          <p class="text-secondary">暂无任务</p>
          <p class="text-tertiary">点击"新建任务"开始分析</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTaskStore } from '@/stores/task'
import type { Task } from '@/stores/task'
import { useRouter } from 'vue-router'

const router = useRouter()
const taskStore = useTaskStore()

const isCollapsed = ref(false)

const tasks = computed(() => taskStore.tasks)
const currentTask = computed(() => taskStore.currentTask)

const statusText: Record<Task['status'], string> = {
  pending: '待处理',
  processing: '分析中',
  completed: '已完成',
  error: '错误'
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const createNewTask = () => {
  router.push({ name: 'Home' })
}

const selectTask = (task: Task) => {
  taskStore.setCurrentTask(task)
  router.push({ name: 'Task', params: { id: task.id } })
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

