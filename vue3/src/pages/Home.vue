<template>
  <div class="home-container">
    <div class="home-content">
      <div class="welcome-section">
        <h1 class="welcome-title">FrameScope——帧析云鉴系统</h1>
        <p class="welcome-subtitle">
          输入您的问题，系统将自动搜索相关视频并进行分析，为您提供多角度的总结和答案
        </p>
      </div>

      <!-- 创建新任务区域 -->
      <div class="task-form-section">
        <div class="form-card">
          <h2 class="form-title">创建新任务</h2>

          <div class="form-group">
            <label for="question-input">您的问题</label>
            <textarea
              id="question-input"
              v-model="form.question"
              class="textarea"
              placeholder="例如：iPhone 15 和 iPhone 14 有什么区别？哪个更值得买？"
              rows="4"
            ></textarea>
            <div class="form-hint">
              输入您想了解的问题，系统将自动搜索相关视频并进行分析
            </div>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <button
            class="btn btn-primary submit-btn"
            :disabled="loading || !canSubmit"
            @click="handleCreateTask"
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
import { useConversationStore } from '@/stores/conversation'
import { useTaskStore } from '@/stores/task'
import type { Task } from '@/stores/task'
import { multiVideoApi } from '@/api/multi_video'

const router = useRouter()
const conversationStore = useConversationStore()
const taskStore = useTaskStore()

const form = ref({
  question: ''
})

const loading = ref(false)
const error = ref('')

const canSubmit = computed(() => {
  return !loading.value && form.value.question.trim().length > 0
})

// 生成模拟任务结果
const generateMockTaskResult = (_question: string) => {
  // 参数保留用于未来根据问题生成个性化结果
  return {
    commonDescriptions: [
      '产品外观设计简洁现代',
      '性能表现稳定可靠',
      '价格定位在中高端市场',
      '用户体验整体良好'
    ],
    contradictions: [
      {
        topic: '电池续航',
        points: [
          { video: '视频1', view: '续航可达10小时，完全满足日常使用' },
          { video: '视频2', view: '续航仅为6小时，重度使用需要频繁充电' }
        ]
      },
      {
        topic: '性价比',
        points: [
          { video: '视频1', view: '性价比很高，值得购买' },
          { video: '视频2', view: '价格偏高，性价比一般' }
        ]
      }
    ],
    uniqueFeatures: [
      {
        video: '视频1',
        features: ['强调了快充功能', '提到了特殊材质', '重点介绍了拍照功能']
      },
      {
        video: '视频2',
        features: ['重点关注了性价比', '提到了竞品对比', '详细分析了游戏性能']
      },
      {
        video: '视频3',
        features: ['强调了系统流畅度', '提到了生态联动', '详细介绍了屏幕显示效果']
      }
    ]
  }
}

const handleCreateTask = async () => {
  if (!canSubmit.value) return

  loading.value = true
  error.value = ''

  try {
    const questionText = form.value.question.trim()
    
    // 创建新对话
    const conversation = await conversationStore.createConversation()
    
    // 使用example目录下的默认视频ID列表
    const defaultVideoIds = ['BV1Dk4y1X71E', 'BV1JD4y1z7vc', 'BV1KL411N7KV', 'BV1m94y1E72S']
    
    // 调用后端API：使用example_video接口进行分析
    const response = await multiVideoApi.queryExample({
      question: questionText,
      video_ids: defaultVideoIds,
      conversation_id: conversation.id
    })
    
    // 生成任务对象
    const taskId = `task_${Date.now()}`
    const task: Task = {
      id: taskId,
      title: questionText,
      videoUrls: defaultVideoIds.map(id => `https://www.bilibili.com/video/${id}`),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'completed',
      result: generateMockTaskResult(questionText),
      questions: [{
        id: `qa_${Date.now()}`,
        question: questionText,
        answer: response.answer,
        createdAt: new Date().toISOString()
      }]
    }
    
    // 添加到任务列表
    taskStore.addTask(task)
    taskStore.saveTasks()
    
    // 跳转到任务详情页，传递 conversationId 和初始问题
    router.push({
      name: 'Task',
      params: { id: taskId },
      query: { 
        conversationId: conversation.id,
        question: questionText
      }
    })
  } catch (err: any) {
    error.value = err.message || '创建任务失败，请稍后重试'
    console.error('创建任务失败:', err)
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

.messages-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-item.user {
  align-items: flex-end;
}

.message-item.assistant {
  align-items: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
}

.message-item.user .message-content {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.message-item.user .message-text {
  color: white;
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(ul), .message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.message-item.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.textarea {
  width: 100%;
  padding: 12px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  resize: vertical;
  min-height: 100px;
}

.textarea:focus {
  outline: none;
  border-color: var(--accent-blue);
}
</style>

