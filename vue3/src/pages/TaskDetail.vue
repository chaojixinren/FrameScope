<template>
  <div class="task-detail-container">
    <div v-if="loading && !task" class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载中...</p>
    </div>

    <div v-else-if="task" class="task-content">
      <!-- 任务头部信息 -->
      <div class="task-header">
        <h1 class="task-title">{{ task.title }}</h1>
        <div class="task-meta-info">
          <span class="task-status" :class="task.status">
            {{ statusText[task.status] }}
          </span>
          <span class="task-date">{{ formatDate(task.createdAt) }}</span>
        </div>
      </div>

      <!-- 视频列表 -->
      <div class="section">
        <h2 class="section-title">视频列表</h2>
        <div class="video-list">
          <div
            v-for="(url, index) in task.videoUrls"
            :key="index"
            class="video-item"
          >
            <span class="video-index">{{ index + 1 }}</span>
            <a :href="url" target="_blank" class="video-link">{{ url }}</a>
          </div>
        </div>
      </div>

      <!-- 分析结果 -->
      <div v-if="task.status === 'processing'" class="processing-state">
        <div class="processing-indicator">
          <div class="pulse-dot"></div>
          <p>正在分析视频内容，请稍候...</p>
        </div>
      </div>

      <div v-else-if="task.status === 'completed' && task.result" class="analysis-results">
        <!-- 共同描述 -->
        <div class="section">
          <h2 class="section-title">共同描述</h2>
          <div class="content-box">
            <ul class="common-list">
              <li
                v-for="(desc, index) in task.result.commonDescriptions"
                :key="index"
                class="list-item"
              >
                {{ desc }}
              </li>
            </ul>
          </div>
        </div>

        <!-- 矛盾点 -->
        <div class="section">
          <h2 class="section-title">矛盾点</h2>
          <div class="contradictions-list">
            <div
              v-for="(contradiction, index) in task.result.contradictions"
              :key="index"
              class="contradiction-item"
            >
              <div class="contradiction-topic">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="2" />
                  <path d="M8 4V12M4 8H12" stroke="currentColor" stroke-width="2" />
                </svg>
                {{ contradiction.topic }}
              </div>
              <div class="contradiction-points">
                <div
                  v-for="(point, pIndex) in contradiction.points"
                  :key="pIndex"
                  class="contradiction-point"
                >
                  <span class="point-video">{{ point.video }}</span>
                  <span class="point-view">{{ point.view }}</span>
                </div>
              </div>
            </div>
            <div v-if="task.result.contradictions.length === 0" class="empty-state">
              <p class="text-secondary">未发现明显的矛盾观点</p>
            </div>
          </div>
        </div>

        <!-- 独特特征 -->
        <div class="section">
          <h2 class="section-title">独特特征</h2>
          <div class="unique-features-list">
            <div
              v-for="(feature, index) in task.result.uniqueFeatures"
              :key="index"
              class="unique-feature-item"
            >
              <div class="feature-header">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 2L10.5 6L15 7L12 10L12.5 15L8 12.5L3.5 15L4 10L1 7L5.5 6L8 2Z" fill="currentColor" />
                </svg>
                <span class="feature-video">{{ feature.video }}</span>
              </div>
              <ul class="feature-list">
                <li
                  v-for="(f, fIndex) in feature.features"
                  :key="fIndex"
                  class="feature-item"
                >
                  {{ f }}
                </li>
              </ul>
            </div>
            <div v-if="task.result.uniqueFeatures.length === 0" class="empty-state">
              <p class="text-secondary">未发现独特特征</p>
            </div>
          </div>
        </div>

        <!-- AI问答区域（对话形式） -->
        <div class="section qa-section">
          <h2 class="section-title">继续提问</h2>
          <p class="section-description">基于视频内容理解，您可以继续提问，AI将为您提供更深入的分析和解答</p>
          
          <!-- 对话消息列表（优先显示conversation的消息） -->
          <div v-if="messages.length > 0" class="messages-list">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="message-item"
              :class="msg.role"
            >
              <div class="message-content">
                <div class="message-text" v-html="formatAnswer(msg.content)"></div>
                <div class="message-time">{{ formatTime(msg.created_at) }}</div>
              </div>
            </div>
          </div>
          
          <!-- 兼容旧的问答历史列表（如果存在且没有conversation消息） -->
          <div v-else-if="questions && questions.length > 0" class="qa-list">
            <div
              v-for="qa in questions"
              :key="qa.id"
              class="qa-item"
            >
              <!-- 用户问题 -->
              <div class="qa-question">
                <div class="qa-avatar user-avatar">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path
                      d="M10 10C12.7614 10 15 7.76142 15 5C15 2.23858 12.7614 0 10 0C7.23858 0 5 2.23858 5 5C5 7.76142 7.23858 10 10 10Z"
                      fill="currentColor"
                    />
                    <path
                      d="M10 12C5.58172 12 2 14.6863 2 18V20H18V18C18 14.6863 14.4183 12 10 12Z"
                      fill="currentColor"
                    />
                  </svg>
                </div>
                <div class="qa-content">
                  <div class="qa-text">{{ qa.question }}</div>
                  <div class="qa-time">{{ formatTime(qa.createdAt) }}</div>
                </div>
              </div>
              
              <!-- AI回答 -->
              <div class="qa-answer">
                <div class="qa-avatar ai-avatar">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path
                      d="M10 2L12.5 7.5L18.5 8.5L14 12.5L15 18.5L10 15.5L5 18.5L6 12.5L1.5 8.5L7.5 7.5L10 2Z"
                      fill="currentColor"
                    />
                  </svg>
                </div>
                <div class="qa-content">
                  <div class="qa-text" v-html="formatAnswer(qa.answer)"></div>
                  <div class="qa-time">{{ formatTime(qa.createdAt) }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 问题输入区 -->
          <div class="qa-input-area">
            <div class="qa-input-container">
              <textarea
                v-model="questionInput"
                class="qa-textarea"
                placeholder="请输入您的问题，例如：这些视频中提到的最大争议点是什么？"
                rows="3"
                @keydown.enter.prevent="handleEnterKey"
              ></textarea>
              <button
                class="qa-send-btn"
                :disabled="!canSendQuestion || sendingQuestion"
                @click="sendQuestion"
              >
                <svg
                  v-if="!sendingQuestion"
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                >
                  <path
                    d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                <div v-else class="qa-loading-spinner"></div>
              </button>
            </div>
            <div class="qa-hint">
              <span class="text-tertiary">按 Enter 发送，Shift + Enter 换行</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="task.status === 'error'" class="error-state">
        <div class="error-message-box">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
            <path d="M12 8V12M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          </svg>
          <p>分析过程中出现错误，请稍后重试</p>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p class="text-secondary">任务不存在</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import { useConversationStore } from '@/stores/conversation'
import type { Task, QuestionAnswer } from '@/stores/task'
import type { Message } from '@/api/conversation'
import { marked } from 'marked'

// 配置marked选项
marked.setOptions({
  breaks: true, // 支持GFM换行（单个换行符也会换行）
  gfm: true, // 启用GitHub Flavored Markdown
})

const route = useRoute()
const taskStore = useTaskStore()
const conversationStore = useConversationStore()

const taskId = computed(() => route.params.id as string)
const conversationId = computed(() => {
  const id = route.query.conversationId
  return id ? parseInt(String(id)) : null
})

const task = computed(() => {
  const foundTask = taskStore.tasks.find(t => t.id === taskId.value)
  if (foundTask) {
    taskStore.setCurrentTask(foundTask)
  }
  return foundTask || null
})

// 对话消息列表
const messages = computed(() => conversationStore.currentMessages)
const questions = computed(() => task.value?.questions || [])
const loading = ref(false)
const questionInput = ref('')
const sendingQuestion = ref(false)

const statusText: Record<Task['status'], string> = {
  pending: '待处理',
  processing: '分析中',
  completed: '已完成',
  error: '错误'
}

const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (minutes < 1) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

const formatAnswer = (answer: string) => {
  // 使用marked解析Markdown格式
  if (!answer) return ''
  try {
    return marked.parse(answer)
  } catch (error) {
    console.error('Markdown解析失败:', error)
    // 如果解析失败，返回原始文本（转义HTML以防止XSS）
    return answer.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

const canSendQuestion = computed(() => {
  return questionInput.value.trim().length > 0 && !sendingQuestion.value
})

const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift + Enter 换行，不做处理
    return
  }
  // Enter 发送
  if (canSendQuestion.value) {
    sendQuestion()
  }
}

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

// 生成样例回答
const generateSampleAnswer = (question: string): string => {
  const questionLower = question.toLowerCase()
  
  // 根据问题关键词生成不同的样例回答
  if (questionLower.includes('争议') || questionLower.includes('矛盾') || questionLower.includes('分歧')) {
    return `根据视频内容分析，主要争议点集中在以下几个方面：

1. **性能表现评估**：不同博主对于产品性能的评价存在明显差异，部分博主认为性能表现优秀，而另一些博主则指出了在某些场景下的性能瓶颈。

2. **性价比观点**：关于性价比的看法存在较大分歧。一些博主从成本角度出发，认为产品具有较高的性价比；而另一些博主则从长期使用价值角度，提出了不同的观点。

3. **适用人群定位**：各博主对于产品的目标用户群体有不同的理解，这在某种程度上反映了产品定位的复杂性。

这些争议点反映了不同博主的评测角度和价值取向，建议根据您的具体需求进行综合判断。`
  } else if (questionLower.includes('优点') || questionLower.includes('优势') || questionLower.includes('亮点')) {
    return `根据多个视频的综合分析，该产品的主要优点包括：

1. **设计工艺**：大部分博主都认可产品在设计方面的用心，外观和质感都得到了较好的评价。

2. **核心功能**：产品的核心功能表现稳定，在主要使用场景下都能满足用户需求。

3. **用户体验**：多个博主提到产品在用户体验方面的优化，交互设计较为人性化。

需要注意的是，不同博主关注的优点侧重点可能不同，建议结合您的实际使用场景来评估这些优点的重要性。`
  } else if (questionLower.includes('缺点') || questionLower.includes('不足') || questionLower.includes('问题')) {
    return `通过对多个视频内容的分析，发现的主要缺点和不足有：

1. **功能局限**：部分博主指出产品在某些特定功能上存在不足，可能无法满足某些高级用户的需求。

2. **兼容性问题**：有博主提到产品在兼容性方面存在一些限制，可能会影响部分用户的使用体验。

3. **价格考量**：从性价比角度，部分博主认为产品价格相对较高，可能不太适合预算有限的用户。

这些缺点的严重程度因人而异，建议您根据自己的使用需求来判断这些缺点的影响。`
  } else if (questionLower.includes('推荐') || questionLower.includes('值得') || questionLower.includes('购买')) {
    return `基于多个视频的评测内容，对于是否推荐购买该产品，有以下几点建议：

**推荐购买的场景：**
- 如果您的主要使用需求与产品核心功能高度匹配
- 对产品质量和设计有较高要求
- 预算相对充足

**需要谨慎考虑的场景：**
- 有特定的功能需求，而产品可能无法完全满足
- 对性价比要求较高
- 需要与现有设备或系统有良好兼容性

综合来看，不同博主基于各自的评测标准给出了不同的建议。建议您根据自己的实际需求、使用场景和预算来做出决定。`
  } else if (questionLower.includes('对比') || questionLower.includes('比较') || questionLower.includes('区别')) {
    return `根据视频内容的对比分析，以下是主要的对比要点：

**共同点：**
- 多个博主都提到了产品在某些基础功能上的表现
- 在核心使用场景下的表现相对一致

**差异点：**
- 不同博主关注的评测维度不同，导致评价重点存在差异
- 对于产品细节的评价存在不同的看法

**总结：**
这些视频从不同角度提供了有价值的信息，建议您结合自己的需求来理解这些对比结果，选择最符合您情况的观点。`
  } else {
    return `根据您的问题，结合多个视频的内容分析，我可以为您提供以下解答：

通过对这些视频内容的综合分析，我发现不同博主从各自的角度提供了丰富的观点和信息。建议您：

1. **关注共同点**：多个博主都提到的观点通常具有较高的参考价值
2. **理解差异**：不同观点的存在反映了产品特性的多面性
3. **结合需求**：最重要的是结合您自己的实际使用需求来理解这些信息

如果您有更具体的问题，例如关于某个特定功能或使用场景的询问，我可以基于视频内容为您提供更详细的分析。`
  }
}

const sendQuestion = async () => {
  if (!canSendQuestion.value || !task.value) return

  const questionText = questionInput.value.trim()
  if (!questionText) return

  sendingQuestion.value = true
  const currentInput = questionText
  questionInput.value = ''

  try {
    // 如果有conversationId，使用对话模式
    if (conversationId.value) {
      // 添加用户消息
      const userMessage: Message = {
        id: Date.now(),
        role: 'user',
        content: currentInput,
        created_at: new Date().toISOString()
      }
      conversationStore.addMessage(userMessage)

      // 模拟延迟
      await new Promise(resolve => setTimeout(resolve, 1000))

      // 生成样例回答（暂时不连接后端，基于任务结果）
      const answer = generateSampleAnswer(currentInput)
      
      // 添加助手回复
      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: answer,
        created_at: new Date().toISOString()
      }
      conversationStore.addMessage(assistantMessage)

      // 刷新对话列表
      await conversationStore.refreshConversations()
    } else {
      // 没有conversationId，使用任务模式（原有逻辑）
      const answer = generateSampleAnswer(currentInput)
      
      const newQA: QuestionAnswer = {
        id: `qa_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        question: currentInput,
        answer: answer,
        createdAt: new Date().toISOString()
      }

      const currentQuestions = task.value.questions || []
      const updatedQuestions = [...currentQuestions, newQA]
      
      taskStore.updateTask(task.value.id, {
        questions: updatedQuestions
      })
    }
  } catch (error) {
    console.error('发送问题失败:', error)
    // 恢复输入
    questionInput.value = currentInput
  } finally {
    sendingQuestion.value = false
  }
}

onMounted(async () => {
  // 如果有conversationId，加载对话详情
  if (conversationId.value) {
    try {
      await conversationStore.loadConversation(conversationId.value)
    } catch (error) {
      console.error('加载对话失败:', error)
    }
  }

  // 如果任务不存在，创建模拟任务
  if (!task.value) {
    loading.value = true
    try {
      // 从路由参数获取问题，如果没有则使用默认值
      const question = (route.query.question as string) || '产品分析'
      
      // 创建模拟任务
      const mockTask: Task = {
        id: taskId.value,
        title: question,
        videoUrls: [
          'https://www.bilibili.com/video/BV1example1',
          'https://www.bilibili.com/video/BV1example2',
          'https://www.bilibili.com/video/BV1example3'
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'completed',
        result: generateMockTaskResult(question)
      }
      
      taskStore.addTask(mockTask)
      taskStore.setCurrentTask(mockTask)
      taskStore.saveTasks()
    } catch (error) {
      console.error('Failed to create mock task:', error)
    } finally {
      loading.value = false
    }
  } else {
    taskStore.setCurrentTask(task.value)
    
    // 如果任务状态是 pending，自动开始分析（模拟）
    if (task.value.status === 'pending') {
      loading.value = true
      try {
        // 模拟分析延迟
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        // 更新任务为已完成，并添加模拟结果
        const question = task.value.title || '产品分析'
        taskStore.updateTask(task.value.id, {
          status: 'completed',
          result: generateMockTaskResult(question)
        })
      } catch (error) {
        console.error('Failed to analyze task:', error)
        taskStore.updateTask(task.value.id, { status: 'error' })
      } finally {
        loading.value = false
      }
    }
  }
})
</script>

<style scoped>
.task-detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px;
}

.loading-state,
.processing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-light);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.pulse-dot {
  width: 12px;
  height: 12px;
  background-color: var(--accent-blue);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 16px;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 16px;
}

.task-header {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-light);
}

.task-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  line-height: 1.3;
}

.task-meta-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.task-status {
  font-size: 14px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
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

.task-date {
  font-size: 14px;
  color: var(--text-tertiary);
}

.section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.video-item:hover {
  border-color: var(--border-medium);
}

.video-index {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.video-link {
  flex: 1;
  color: var(--accent-blue);
  text-decoration: none;
  word-break: break-all;
  line-height: 1.5;
}

.video-link:hover {
  text-decoration: underline;
}

.content-box {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 20px;
}

.common-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-item {
  padding-left: 24px;
  position: relative;
  color: var(--text-primary);
  line-height: 1.6;
}

.list-item::before {
  content: '•';
  position: absolute;
  left: 8px;
  color: var(--accent-blue);
  font-weight: bold;
}

.contradictions-list,
.unique-features-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.contradiction-item,
.unique-feature-item {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.contradiction-item:hover,
.unique-feature-item:hover {
  border-color: var(--border-medium);
}

.contradiction-topic {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  color: #ef4444;
}

.contradiction-points {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.contradiction-point {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background-color: var(--bg-primary);
  border-left: 3px solid var(--border-medium);
  border-radius: 4px;
}

.point-video {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.point-view {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.feature-video {
  color: var(--accent-blue);
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-item {
  padding-left: 24px;
  position: relative;
  color: var(--text-primary);
  line-height: 1.6;
}

.feature-item::before {
  content: '→';
  position: absolute;
  left: 8px;
  color: var(--text-tertiary);
}

.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.error-message-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #ef4444;
  text-align: center;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-state p {
  font-size: 16px;
}

/* 问答区域样式 */
.qa-section {
  border-top: 2px solid var(--border-light);
  padding-top: 40px;
}

.section-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 24px;
  line-height: 1.6;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  max-height: 500px;
  overflow-y: auto;
  padding: 16px 0;
}

.messages-list .message-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.messages-list .message-item.user {
  align-items: flex-end;
}

.messages-list .message-item.assistant {
  align-items: flex-start;
}

.messages-list .message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
}

.messages-list .message-item.user .message-content {
  background-color: var(--accent-blue);
  color: white;
  border-color: var(--accent-blue);
}

.messages-list .message-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.messages-list .message-item.user .message-text {
  color: white;
}

.messages-list .message-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.messages-list .message-item.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 32px;
}

.qa-item {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.qa-question,
.qa-answer {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.qa-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.user-avatar {
  background-color: var(--accent-blue);
}

.ai-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.qa-content {
  flex: 1;
  min-width: 0;
}

.qa-text {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 12px 16px;
  color: var(--text-primary);
  line-height: 1.6;
  word-wrap: break-word;
}

.qa-text strong {
  font-weight: 600;
  color: var(--text-primary);
}

/* Markdown 渲染样式 */
.qa-text :deep(h1),
.qa-text :deep(h2),
.qa-text :deep(h3),
.qa-text :deep(h4),
.qa-text :deep(h5),
.qa-text :deep(h6) {
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.4;
}

.qa-text :deep(h1) {
  font-size: 1.5em;
  border-bottom: 2px solid var(--border-light);
  padding-bottom: 0.5em;
}

.qa-text :deep(h2) {
  font-size: 1.3em;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 0.3em;
}

.qa-text :deep(h3) {
  font-size: 1.1em;
}

.qa-text :deep(h4),
.qa-text :deep(h5),
.qa-text :deep(h6) {
  font-size: 1em;
}

.qa-text :deep(p) {
  margin: 0.75em 0;
  line-height: 1.6;
}

.qa-text :deep(ul),
.qa-text :deep(ol) {
  margin: 0.75em 0;
  padding-left: 1.5em;
}

.qa-text :deep(li) {
  margin: 0.25em 0;
  line-height: 1.6;
}

.qa-text :deep(ul) {
  list-style-type: disc;
}

.qa-text :deep(ol) {
  list-style-type: decimal;
}

.qa-text :deep(blockquote) {
  margin: 0.75em 0;
  padding-left: 1em;
  border-left: 3px solid var(--accent-blue);
  color: var(--text-secondary);
  font-style: italic;
}

.qa-text :deep(code) {
  background-color: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
  color: var(--accent-blue);
}

.qa-text :deep(pre) {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 0.75em 0;
}

.qa-text :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: var(--text-primary);
  font-size: 0.9em;
}

.qa-text :deep(a) {
  color: var(--accent-blue);
  text-decoration: none;
}

.qa-text :deep(a:hover) {
  text-decoration: underline;
}

.qa-text :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-light);
  margin: 1.5em 0;
}

.qa-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75em 0;
}

.qa-text :deep(th),
.qa-text :deep(td) {
  border: 1px solid var(--border-light);
  padding: 8px 12px;
  text-align: left;
}

.qa-text :deep(th) {
  background-color: var(--bg-tertiary);
  font-weight: 600;
}

.qa-text :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 0.75em 0;
}

.qa-text :deep(del) {
  text-decoration: line-through;
  opacity: 0.7;
}

.qa-question .qa-text {
  background-color: var(--bg-secondary);
}

.qa-answer .qa-text {
  background-color: var(--bg-primary);
  border-color: var(--border-light);
}

/* 对话模式样式 */
.conversation-content {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  max-height: 900px;
}

.conversation-header {
  padding: 24px 0;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 24px;
}

.conversation-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.conversation-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.conversation-date {
  font-size: 14px;
  color: var(--text-secondary);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
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

.empty-messages {
  padding: 60px 20px;
  text-align: center;
  color: var(--text-secondary);
}

.qa-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 6px;
  padding-left: 16px;
}

.qa-input-area {
  margin-top: 24px;
}

.qa-input-container {
  position: relative;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.qa-textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  transition: all 0.2s ease;
  outline: none;
}

.qa-textarea:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--accent-blue-light);
}

.qa-textarea::placeholder {
  color: var(--text-tertiary);
}

.qa-send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background-color: var(--accent-blue);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  outline: none;
}

.qa-send-btn:hover:not(:disabled) {
  background-color: var(--accent-blue-hover);
  transform: translateY(-1px);
}

.qa-send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.qa-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.qa-loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.qa-hint {
  margin-top: 8px;
  padding-left: 4px;
  font-size: 12px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .qa-question,
  .qa-answer {
    gap: 8px;
  }

  .qa-avatar {
    width: 28px;
    height: 28px;
  }

  .qa-avatar svg {
    width: 16px;
    height: 16px;
  }
}
</style>

