<template>
  <div class="task-detail-container">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载中...</p>
    </div>

    <div v-else class="task-content">
      <!-- 对话头部信息 -->
      <div v-if="conversationStore.currentConversation" class="task-header">
        <div class="task-header-content">
          <h1 class="task-title">{{ conversationStore.currentConversation.title || '新对话' }}</h1>
          <div class="task-meta-info">
            <span class="task-date">{{ formatDate(conversationStore.currentConversation.created_at) }}</span>
          </div>
        </div>
        <div class="task-header-actions">
          <button
            v-if="conversationId"
            class="delete-btn"
            @click="handleDeleteConversation"
            :disabled="deletingConversation"
            title="删除对话"
          >
            <svg
              v-if="!deletingConversation"
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
            >
              <path
                d="M5 5L15 15M15 5L5 15"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <div v-else class="delete-loading-spinner"></div>
          </button>
        </div>
      </div>

      <!-- AI问答区域（对话形式） -->
      <div class="section qa-section">
        <h2 class="section-title">{{ conversationId ? '继续对话' : '开始新对话' }}</h2>
        <p class="section-description">基于视频内容理解，您可以提问，AI将为您提供深入的分析和解答</p>
        
        <!-- 对话消息列表 -->
        <div v-if="messages.length > 0" class="messages-list" ref="messagesListRef">
          <div
            v-for="(msg, index) in messages"
            :key="`msg-${msg.id || index}-${msg.created_at}`"
            class="message-item"
            :class="msg.role"
          >
            <div class="message-content">
              <div class="message-text" v-html="formatAnswer(msg.content)"></div>
              <div class="message-time">{{ formatTime(msg.created_at) }}</div>
            </div>
          </div>
          
          <!-- 发送中状态 -->
          <div v-if="sendingQuestion" class="message-item assistant">
            <div class="message-content">
              <div class="message-text">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="!sendingQuestion" class="empty-messages">
          <p class="text-secondary">还没有消息，开始提问吧！</p>
        </div>

        <!-- 问题输入区 -->
        <div class="qa-input-area">
          <div class="qa-input-container">
            <textarea
              v-model="questionInput"
              class="qa-textarea"
              placeholder="请输入您的问题，例如：索尼A7M4相机怎么样？"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConversationStore } from '@/stores/conversation'
import type { Message } from '@/api/conversation'
import { multiVideoApi } from '@/api/multi_video'
import { marked } from 'marked'

// 配置marked选项
marked.setOptions({
  breaks: true, // 支持GFM换行（单个换行符也会换行）
  gfm: true, // 启用GitHub Flavored Markdown
})

const route = useRoute()
const router = useRouter()
const conversationStore = useConversationStore()

const conversationId = computed(() => {
  const id = route.query.conversationId
  return id ? parseInt(String(id)) : null
})

// 对话消息列表
const messages = computed(() => conversationStore.currentMessages)
const loading = ref(false)
const questionInput = ref('')
const sendingQuestion = ref(false)
const deletingConversation = ref(false)
const messagesListRef = ref<HTMLElement | null>(null)

// 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesListRef.value) {
      messagesListRef.value.scrollTop = messagesListRef.value.scrollHeight
    }
  })
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

const formatDate = (dateString: string | null) => {
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

const formatTime = (dateString: string | null) => {
  if (!dateString) return '未知时间'
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

// 已移除模拟数据生成函数，改用实际 API

// 从视频URL中提取视频ID（B站BV号）
const extractVideoIds = (videoUrls: string[]): string[] => {
  const videoIds: string[] = []
  const bvPattern = /BV[0-9A-Za-z]+/g
  
  videoUrls.forEach(url => {
    const matches = url.match(bvPattern)
    if (matches) {
      videoIds.push(...matches)
    }
  })
  
  // 如果没有从URL中提取到，使用example目录中的默认视频ID列表
  if (videoIds.length === 0) {
    return ['BV1Dk4y1X71E', 'BV1JD4y1z7vc', 'BV1KL411N7KV', 'BV1m94y1E72S']
  }
  
  return [...new Set(videoIds)] // 去重
}

const sendQuestion = async () => {
  if (!canSendQuestion.value) return

  const questionText = questionInput.value.trim()
  if (!questionText) return

  sendingQuestion.value = true
  const currentInput = questionText
  questionInput.value = ''

  try {
    let targetConversationId = conversationId.value

    // 如果没有conversationId，先创建新对话
    if (!targetConversationId) {
      const newConversation = await conversationStore.createConversation()
      targetConversationId = newConversation.id
      
      // 更新 URL 以包含 conversationId
      router.replace({
        path: route.path,
        query: { ...route.query, conversationId: targetConversationId }
      })
    }

    // 添加用户消息到本地状态（乐观更新）
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: currentInput,
      created_at: new Date().toISOString()
    }
    conversationStore.addMessage(userMessage)

    // 调用后端 API
    const response = await multiVideoApi.query({
      question: currentInput,
      conversation_id: targetConversationId
    })

    // 添加助手回复
    const assistantMessage: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: response.answer,
      created_at: new Date().toISOString()
    }
    conversationStore.addMessage(assistantMessage)
    
    // 滚动到底部
    scrollToBottom()

    // 刷新对话列表和详情（确保数据同步，包括更新后的标题）
    await conversationStore.loadConversation(targetConversationId)
    await conversationStore.refreshConversations()
    
    // 再次滚动到底部（确保显示最新消息）
    scrollToBottom()
  } catch (error: any) {
    console.error('发送问题失败:', error)
    // 恢复输入
    questionInput.value = currentInput
    
    // 显示错误提示（可以后续添加 toast 组件）
    const errorMessage = error?.response?.data?.detail || error?.message || '发送问题失败，请稍后重试'
    alert(errorMessage)
    
    // 移除刚才添加的用户消息（回滚乐观更新）
    if (conversationStore.currentMessages.length > 0) {
      const lastMessage = conversationStore.currentMessages[conversationStore.currentMessages.length - 1]
      if (lastMessage && lastMessage.role === 'user' && lastMessage.content === currentInput) {
        conversationStore.currentMessages.pop()
      }
    }
  } finally {
    sendingQuestion.value = false
  }
}

// 删除对话
const handleDeleteConversation = async () => {
  if (!conversationId.value) return
  
  // 确认删除
  if (!confirm('确定要删除这个对话吗？删除后将无法恢复。')) {
    return
  }
  
  deletingConversation.value = true
  try {
    await conversationStore.deleteConversation(conversationId.value)
    
    // 删除成功后，跳转到首页或对话列表页
    router.push('/')
  } catch (error: any) {
    console.error('删除对话失败:', error)
    const errorMessage = error?.response?.data?.msg || error?.message || '删除对话失败，请稍后重试'
    alert(errorMessage)
  } finally {
    deletingConversation.value = false
  }
}

onMounted(async () => {
  // 如果有conversationId，加载对话详情
  if (conversationId.value) {
    loading.value = true
    try {
      await conversationStore.loadConversation(conversationId.value)
      // 加载后滚动到底部
      scrollToBottom()
    } catch (error) {
      console.error('加载对话失败:', error)
    } finally {
      loading.value = false
    }
  } else {
    // 如果没有 conversationId，尝试加载对话列表（用于显示历史对话）
    try {
      await conversationStore.loadConversations(10, 0)
    } catch (error) {
      console.error('加载对话列表失败:', error)
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
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.task-header-content {
  flex: 1;
  min-width: 0;
}

.task-header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
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

.delete-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  background-color: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  outline: none;
}

.delete-btn:hover:not(:disabled) {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.delete-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-light);
  border-top-color: var(--text-secondary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
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
  max-height: 600px;
  overflow-y: auto;
  padding: 16px 0;
  scroll-behavior: smooth;
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

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-secondary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
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

