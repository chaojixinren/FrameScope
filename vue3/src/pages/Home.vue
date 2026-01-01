<template>
  <div class="home-container">
    <div class="home-content">
      <div class="welcome-section">
        <h1 class="welcome-title">FrameScope——帧析云鉴系统</h1>
        <p class="welcome-subtitle">
          创建分析任务，系统将自动获取多个相关视频并进行分析，提取共同描述、矛盾点和独特特征
        </p>
      </div>

      <div class="task-form-section">
        <div class="form-card">
          <h2 class="form-title">创建新任务</h2>

          <div class="form-group">
            <label for="task-title">任务名称</label>
            <input
              id="task-title"
              v-model="form.title"
              type="text"
              class="input"
              placeholder="例如：iPhone 15 评测对比分析"
            />
            <div class="form-hint">
              任务名称用于标识和管理分析任务
            </div>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <button
            class="btn btn-primary submit-btn"
            :disabled="loading || !canSubmit"
            @click="handleSubmit"
          >
            {{ loading ? '创建中...' : '创建任务' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import { taskApi } from '@/api/task'

const router = useRouter()
const taskStore = useTaskStore()

const form = ref({
  title: ''
})

const loading = ref(false)
const error = ref('')

const canSubmit = computed(() => {
  return !loading.value && form.value.title.trim().length > 0
})

const handleSubmit = async () => {
  if (!canSubmit.value) return

  loading.value = true
  error.value = ''

  try {
    const task = await taskApi.createTask({
      title: form.value.title.trim() || `任务 ${new Date().toLocaleString()}`
    })

    taskStore.addTask(task)
    taskStore.saveTasks()

    // 跳转到任务详情页并开始分析
    router.push({ name: 'Task', params: { id: task.id } })
    
    // 开始分析（后端会自动获取视频并分析）
    const analyzedTask = await taskApi.analyzeTask(task.id)
    taskStore.updateTask(task.id, analyzedTask)
  } catch (err: any) {
    error.value = err.message || '创建任务失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 24px;
}

.home-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.welcome-section {
  text-align: center;
  padding: 40px 0;
}

.welcome-title {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.welcome-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
}

.task-form-section {
  width: 100%;
}

.form-card {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 32px;
  box-shadow: var(--shadow-sm);
}

.form-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.form-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 6px;
}

.error-message {
  padding: 12px;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: #ef4444;
  font-size: 14px;
  margin-bottom: 16px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
}
</style>

