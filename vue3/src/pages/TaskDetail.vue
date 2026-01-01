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

      <!-- 第一次回答（任务结果） -->
      <div v-if="firstAnswer || (sendingQuestion && messages.length === 0)" class="section task-result-section">
        <div class="task-result-content">
          <!-- 加载中状态 -->
          <div v-if="sendingQuestion && messages.length === 0" class="task-steps">
            <div class="task-step">
              <div class="step-status loading">
                <div class="loading-spinner-small"></div>
              </div>
              <div class="step-content">
                <div class="step-title">正在获取视频连接......</div>
              </div>
            </div>
          </div>
          
          <!-- 已完成状态 -->
          <div v-else-if="firstAnswer" class="task-steps">
            <!-- 步骤1: 获取视频连接 -->
            <div class="task-step">
              <div class="step-status completed">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="step-content">
                <div class="step-title">正在获取视频连接......</div>
              </div>
            </div>
            
            <!-- 步骤2: 已获取视频列表 -->
            <div class="task-step" v-if="currentVideoIds.length > 0">
              <div class="step-status completed">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="step-content">
                <div class="step-title">已获取到对应视频：</div>
                <div class="video-list-container">
                  <div 
                    v-for="(videoId, index) in currentVideoIds" 
                    :key="videoId" 
                    class="video-item"
                  >
                    视频{{ index + 1 }}：<a :href="`https://www.bilibili.com/video/${videoId}`" target="_blank" class="video-link">{{ videoId }}</a>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 步骤3: 下载并分析 -->
            <div class="task-step">
              <div class="step-status completed">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="step-content">
                <div class="step-title">正在下载并分析视频内容(完成后可点击"视频xx"的标题进入内容展示)......</div>
              </div>
            </div>
            
            <!-- 步骤4: 分析结果 -->
            <div class="task-step">
              <div class="step-status completed">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="step-content">
                <div class="step-title">已完成视频内容分析：</div>
                <div class="analysis-result">
                  <div class="result-content" v-html="formatAnswer(firstAnswer.content)"></div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="firstAnswer" class="task-result-time">{{ formatTime(firstAnswer.created_at) }}</div>
        </div>
      </div>

      <!-- 后续对话消息列表（显示在"继续对话"上方） -->
      <div v-if="hasFollowupConversation" class="messages-list">
        <div
          v-for="(msg, index) in followupMessages"
          :key="`msg-${msg.id || index}-${msg.created_at}`"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-content">
            <div class="message-text" v-html="formatAnswer(msg.content)"></div>
            <div class="message-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
        
        <!-- 发送中状态（后续对话时显示） -->
        <div v-if="sendingQuestion && messages.length > 0" class="message-item assistant">
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

      <!-- AI问答区域（对话形式） -->
      <div class="section qa-section">
        <h2 class="section-title">{{ conversationId && (firstAnswer || hasFollowupConversation) ? '继续对话' : '开始新对话' }}</h2>
        <p class="section-description">基于视频内容理解，您可以提问，AI将为您提供深入的分析和解答</p>

        <!-- 问题输入区 -->
        <div class="qa-input-area">
          <!-- 视频数量选择（仅在第一次提问时显示） -->
          <div v-if="!conversationId || messages.length === 0" class="video-count-selector">
            <label for="video-count-input" class="video-count-label">分析视频数量：</label>
            <input
              id="video-count-input"
              v-model.number="selectedVideoCount"
              type="number"
              class="video-count-input"
              min="1"
              max="20"
              placeholder="请输入视频数量（1-20）"
            />
            <span class="video-count-hint">系统将搜索并分析指定数量的相关视频（建议3-10个）</span>
          </div>
          
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
import { multiVideoApi, type MultiVideoResponse } from '@/api/multi_video'
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

// 第一次回答（第一条AI消息，作为任务结果）
const firstAnswer = computed(() => {
  if (messages.value.length >= 2) {
    const firstUserMsg = messages.value[0]
    const firstAssistantMsg = messages.value[1]
    // 确保第一条是用户消息，第二条是AI消息
    if (firstUserMsg && firstAssistantMsg && firstUserMsg.role === 'user' && firstAssistantMsg.role === 'assistant') {
      return firstAssistantMsg
    }
  }
  return null
})

// 后续对话消息（从第三条消息开始）
const followupMessages = computed(() => {
  // 如果有第一次回答，则从第三条消息开始是后续对话
  if (firstAnswer.value && messages.value.length > 2) {
    return messages.value.slice(2)
  }
  return []
})

// 是否有后续对话
const hasFollowupConversation = computed(() => followupMessages.value.length > 0)

const loading = ref(false)
const questionInput = ref('')
const sendingQuestion = ref(false)
const deletingConversation = ref(false)
// 当前任务的视频ID列表
const currentVideoIds = ref<string[]>([])
// 选择的视频数量（默认5个，可以从URL参数中获取）
const selectedVideoCount = ref<number>(5)

// 自动滚动到底部（使用主页面滚动条）
const scrollToBottom = () => {
  nextTick(() => {
    // 滚动到页面底部
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    })
  })
}

// 监听消息变化，自动滚动到底部（只在后续对话时滚动）
watch(followupMessages, () => {
  if (hasFollowupConversation.value) {
    scrollToBottom()
  }
}, { deep: true })

// 监听第一次回答，滚动到底部
watch(firstAnswer, () => {
  if (firstAnswer.value) {
    scrollToBottom()
  }
})

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
    let html = marked.parse(answer) as string
    
    // 解析后，清理表格单元格中的 "---" 文本内容
    // 这是因为 LLM 可能将空单元格写成 "---"（表格分隔符），导致显示问题
    if (typeof document !== 'undefined') {
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = html
      
      // 查找所有表格单元格（不包括表头）
      const cells = tempDiv.querySelectorAll('td')
      cells.forEach((cell) => {
        const text = cell.textContent || ''
        // 如果单元格内容只有 "---" 或类似的分隔符（至少2个连字符），清空它
        if (text.trim().match(/^-{2,}$/)) {
          cell.textContent = ''
          // 添加一个非断行空格，确保单元格仍然可见
          cell.innerHTML = '&nbsp;'
        }
      })
      
      html = tempDiv.innerHTML
    }
    
    // 处理图片URL：将后端的绝对URL转换为可访问的相对路径
    // 后端生成的URL格式可能有问题：http://127.0.0.1:8000:8483/static/screenshots/xxx.jpg（两个端口）
    // 正常格式：http://localhost:8483/static/screenshots/xxx.jpg
    // 提取路径部分，使用相对路径（/static/screenshots/xxx.jpg）
    // 通过Vite代理将/static请求转发到后端服务器
    html = html.replace(
      /src=["'](https?:\/\/[^"']*\/static\/screenshots\/[^"']+)["']/gi,
      (match: string, url: string) => {
        // 直接使用正则表达式提取路径部分，避免URL解析错误
        // 这样可以处理格式错误的URL（如包含两个端口号的情况）
        const pathMatch = url.match(/\/static\/screenshots\/[^"'\s]+/)
        if (pathMatch) {
          return `src="${pathMatch[0]}"`
        }
        // 如果提取失败，返回原始URL
        return match
      }
    )
    
    // 处理"查看原片"链接前的图片：隐藏图片并在悬浮时显示缩略图
    // 使用 DOM 方法来更准确地处理
    if (typeof document !== 'undefined') {
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = html
      
      // 查找所有包含"查看原片"的链接
      const viewLinks = tempDiv.querySelectorAll('a')
      viewLinks.forEach((link) => {
        if (link.textContent && link.textContent.includes('查看原片')) {
          // 向前查找最近的图片（可能在同一个父元素或前一个兄弟元素中）
          let image: HTMLImageElement | null = null
          
          // 首先在同一个父元素中查找前面的图片
          const parent = link.parentElement
          if (parent) {
            const allElements = Array.from(parent.childNodes)
            const linkIndex = allElements.indexOf(link)
            
            // 在链接之前查找图片
            for (let i = linkIndex - 1; i >= 0; i--) {
              const element = allElements[i]
              if (element && element.nodeType === Node.ELEMENT_NODE) {
                const img = (element as Element).querySelector('img')
                if (img) {
                  image = img
                  break
                }
                // 如果元素本身就是 img
                if ((element as Element).tagName === 'IMG') {
                  image = element as HTMLImageElement
                  break
                }
              }
            }
          }
          
          // 如果没有在同级找到，查找前一个兄弟元素
          if (!image) {
            let prevSibling = link.parentElement?.previousElementSibling
            while (prevSibling && !image) {
              image = prevSibling.querySelector('img')
              if (!image && prevSibling.tagName === 'IMG') {
                image = prevSibling as HTMLImageElement
              }
              prevSibling = prevSibling.previousElementSibling
            }
          }
          
          // 如果找到了图片，处理它
          if (image) {
            const imgSrc = image.getAttribute('src') || ''
            // 提取相对路径
            const pathMatch = imgSrc.match(/\/static\/screenshots\/[^"'\s]+/)
            const imagePath = pathMatch ? pathMatch[0] : imgSrc
            
            // 隐藏图片
            image.style.display = 'none'
            image.classList.add('hidden-original-image')
            image.setAttribute('data-original-src', imagePath)
            
            // 给链接添加类、data 属性和内联样式（用于悬浮显示缩略图）
            link.classList.add('hover-image-link')
            link.setAttribute('data-image-src', imagePath)
            // 使用 CSS 变量来设置背景图片（通过内联样式）
            link.style.setProperty('--hover-image-url', `url('${imagePath}')`)
          }
        }
      })
      
      html = tempDiv.innerHTML
    }
    
    return html
  } catch (error) {
    console.error('Markdown解析失败:', error)
    // 如果解析失败，返回原始文本（转义HTML以防止XSS）
    return answer.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}


const canSendQuestion = computed(() => {
  const questionValid = questionInput.value.trim().length > 0
  const videoCountValid = selectedVideoCount.value >= 1 && selectedVideoCount.value <= 20
  return questionValid && videoCountValid && !sendingQuestion.value
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

// 从文本中提取视频URL（支持Bilibili、YouTube、抖音等）
const extractVideoUrls = (text: string): { urls: string[], cleanedText: string } => {
  // 匹配各种视频URL格式
  // 使用更通用的正则表达式，匹配完整的URL（包括查询参数），直到遇到空格或文本结束
  const urlPatterns = [
    // Bilibili 完整URL（支持查询参数和路径）
    /https?:\/\/(www\.)?bilibili\.com\/video\/[a-zA-Z0-9]+[^\s]*/g,
    // Bilibili 短链接
    /https?:\/\/b23\.tv\/[a-zA-Z0-9]+[^\s]*/g,
    // YouTube
    /https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[a-zA-Z0-9_-]+[^\s]*/g,
    // 抖音
    /https?:\/\/(www\.)?douyin\.com\/video\/[0-9]+[^\s]*/g,
  ]
  
  const foundUrls: string[] = []
  let cleanedText = text
  
  // 提取所有匹配的URL
  urlPatterns.forEach(pattern => {
    let match
    while ((match = pattern.exec(text)) !== null) {
      const url = match[0]
      // 清理URL（移除末尾的标点符号，但保留查询参数）
      // 只移除URL末尾的标点符号（不在查询参数中的）
      let cleanUrl = url.trim()
      // 如果URL末尾有标点符号（且不在查询参数中），移除它
      if (cleanUrl.match(/[.,;:!?]$/) && !cleanUrl.includes('?')) {
        cleanUrl = cleanUrl.replace(/[.,;:!?]+$/, '')
      } else if (cleanUrl.match(/[.,;:!?]$/)) {
        // 如果URL包含查询参数，检查标点是否在查询参数之后
        const queryIndex = cleanUrl.indexOf('?')
        if (queryIndex !== -1) {
          const beforeQuery = cleanUrl.substring(0, queryIndex)
          const afterQuery = cleanUrl.substring(queryIndex)
          // 只移除查询参数之后的标点
          const cleanedAfterQuery = afterQuery.replace(/[.,;:!?]+$/, '')
          cleanUrl = beforeQuery + cleanedAfterQuery
        }
      }
      
      if (cleanUrl && !foundUrls.includes(cleanUrl)) {
        foundUrls.push(cleanUrl)
        // 从文本中移除URL（使用原始URL进行替换）
        cleanedText = cleanedText.replace(url, '').trim()
      }
    }
    // 重置正则表达式的lastIndex
    pattern.lastIndex = 0
  })
  
  // 清理多余的空格
  cleanedText = cleanedText.replace(/\s+/g, ' ').trim()
  
  return { urls: foundUrls, cleanedText }
}

const sendQuestion = async () => {
  if (!canSendQuestion.value) return

  const questionText = questionInput.value.trim()
  if (!questionText) return

  sendingQuestion.value = true
  const currentInput = questionText
  questionInput.value = ''

  // 记录发送前的消息数量，用于错误回滚
  const messageCountBeforeSend = messages.value.length

  try {
    let targetConversationId = conversationId.value

    // 判断是否是第一次回答（消息数量为0时是第一次）
    const isFirstAnswer = messages.value.length === 0

    // 提取问题中的视频URL
    const { urls: extractedUrls, cleanedText: cleanedQuestion } = extractVideoUrls(currentInput)
    
    if (extractedUrls.length > 0) {
      console.log('从问题中提取到视频URL:', extractedUrls)
      console.log('清理后的问题:', cleanedQuestion)
    }

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

    // 不再在前端预先添加消息，等待后端保存后统一加载
    // 第一次回答不显示用户消息，但会保存到后端
    // 后续对话的用户消息也会由后端保存，然后通过 loadConversation 统一加载

    let response: MultiVideoResponse
    
    if (isFirstAnswer) {
      // 第一次回答：使用 multi_video 接口（自动搜索相关视频）
      const maxVideosToUse = selectedVideoCount.value || 5
      console.log('发送API请求，视频数量:', maxVideosToUse, '提取的URL数量:', extractedUrls.length)
      
      // 使用清理后的问题文本，并传递提取的URL
      response = await multiVideoApi.query({
        question: cleanedQuestion || currentInput, // 如果清理后为空，使用原始文本
        conversation_id: targetConversationId,
        max_videos: maxVideosToUse,
        video_urls: extractedUrls.length > 0 ? extractedUrls : undefined
      })
    } else {
      // 后续对话：使用 multi_video 接口（根据上下文进行正常对话）
      response = await multiVideoApi.query({
        question: cleanedQuestion || currentInput, // 如果清理后为空，使用原始文本
        conversation_id: targetConversationId,
        video_urls: extractedUrls.length > 0 ? extractedUrls : undefined
      })
    }

    // 后端已经保存了用户消息和助手回复，直接重新加载对话即可
    // 注意：loadConversation会从后端加载所有消息（包括第一次的用户消息），
    // 但我们的显示逻辑会通过firstAnswer和followupMessages来区分显示
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
    
    // 移除刚才添加的消息（回滚乐观更新）
    // 恢复到发送前的消息数量
    while (conversationStore.currentMessages.length > messageCountBeforeSend) {
      conversationStore.currentMessages.pop()
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
  // 首先读取URL参数中的maxVideos（如果存在），在任何其他操作之前设置
  const initialMaxVideos = route.query.maxVideos as string | undefined
  if (initialMaxVideos) {
    const maxVideosNum = parseInt(initialMaxVideos)
    if (!isNaN(maxVideosNum) && maxVideosNum >= 1 && maxVideosNum <= 20) {
      selectedVideoCount.value = maxVideosNum
      console.log('从URL参数读取视频数量:', maxVideosNum)
    }
  }
  
  // 如果有conversationId，加载对话详情
  if (conversationId.value) {
    loading.value = true
    try {
      await conversationStore.loadConversation(conversationId.value)
      // 如果加载了对话且有第一次回答，但没有视频ID列表，使用默认的video_ids
      // 这样可以确保从已有对话加载时也能显示视频列表
      if (firstAnswer.value && currentVideoIds.value.length === 0) {
        currentVideoIds.value = ['BV1Dk4y1X71E', 'BV1JD4y1z7vc', 'BV1KL411N7KV', 'BV1m94y1E72S']
      }
      // 加载后滚动到底部
      scrollToBottom()
      
      // 检查是否有初始问题需要自动发送（新建任务时传递的 question 参数）
      const initialQuestion = route.query.question as string | undefined
      
      if (initialQuestion && conversationStore.currentMessages.length === 0) {
        // 如果对话中没有消息，自动发送初始问题
        questionInput.value = initialQuestion
        // 等待一下确保 UI 更新，然后自动发送
        await nextTick()
        console.log('发送问题，使用视频数量:', selectedVideoCount.value)
        await sendQuestion()
        // 发送后清除 URL 中的 question 和 maxVideos 参数，避免刷新页面时重复发送
        router.replace({
          path: route.path,
          query: { ...route.query, question: undefined, maxVideos: undefined }
        })
      }
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

/* 任务结果区域样式 */
.task-result-section {
  margin-bottom: 40px;
}

.task-result-content {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 32px;
}

/* 任务步骤样式 */
.task-steps {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.task-step {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.step-status {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.step-status.loading {
  border: 2px solid var(--border-light);
  border-top-color: var(--accent-blue);
  animation: spin 1s linear infinite;
}

.step-status.completed {
  background-color: var(--accent-blue);
  color: white;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.video-list-container {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.video-item {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
}

.video-link {
  color: var(--accent-blue);
  text-decoration: none;
  word-break: break-all;
}

.video-link:hover {
  text-decoration: underline;
}

.analysis-result {
  margin-top: 12px;
}

.result-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
}

.result-content :deep(p) {
  margin: 0.75em 0;
  line-height: 1.8;
}

.result-content :deep(p:first-child) {
  margin-top: 0;
}

.result-content :deep(p:last-child) {
  margin-bottom: 0;
}

.result-content :deep(ul),
.result-content :deep(ol) {
  margin: 0.75em 0;
  padding-left: 1.5em;
}

.result-content :deep(li) {
  margin: 0.25em 0;
  line-height: 1.8;
}

.result-content :deep(h1),
.result-content :deep(h2),
.result-content :deep(h3),
.result-content :deep(h4),
.result-content :deep(h5),
.result-content :deep(h6) {
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.4;
}

.result-content :deep(h1) {
  font-size: 1.5em;
  border-bottom: 2px solid var(--border-light);
  padding-bottom: 0.5em;
}

.result-content :deep(h2) {
  font-size: 1.3em;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 0.3em;
}

.result-content :deep(h3) {
  font-size: 1.1em;
}

.result-content :deep(code) {
  background-color: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
  color: var(--accent-blue);
}

.result-content :deep(pre) {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 0.75em 0;
}

.result-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: var(--text-primary);
}

.result-content :deep(blockquote) {
  margin: 0.75em 0;
  padding-left: 1em;
  border-left: 3px solid var(--accent-blue);
  color: var(--text-secondary);
  font-style: italic;
}

.result-content :deep(a) {
  color: var(--accent-blue);
  text-decoration: none;
}

.result-content :deep(a:hover) {
  text-decoration: underline;
}

/* 隐藏"查看原片"前的图片 */
.result-content :deep(.hidden-original-image) {
  display: none !important;
}

/* "查看原片"链接悬浮显示缩略图 */
.result-content :deep(.hover-image-link) {
  position: relative;
}

.result-content :deep(.hover-image-link::after) {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  width: 280px;
  height: 158px;
  background-image: var(--hover-image-url);
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 1000;
}

.result-content :deep(.hover-image-link:hover::after) {
  opacity: 1;
  transform: translateX(-50%) translateY(-12px);
}

.result-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-light);
  margin: 1.5em 0;
}

.result-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75em 0;
}

.result-content :deep(th),
.result-content :deep(td) {
  border: 1px solid var(--border-light);
  padding: 8px 12px;
  text-align: left;
}

.result-content :deep(th) {
  background-color: var(--bg-tertiary);
  font-weight: 600;
}

.result-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 0.75em 0;
}

.loading-spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-light);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.task-result-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.task-result-text :deep(p) {
  margin: 0.75em 0;
  line-height: 1.8;
}

.task-result-text :deep(p:first-child) {
  margin-top: 0;
}

.task-result-text :deep(p:last-child) {
  margin-bottom: 0;
}

.task-result-text :deep(ul),
.task-result-text :deep(ol) {
  margin: 0.75em 0;
  padding-left: 1.5em;
}

.task-result-text :deep(li) {
  margin: 0.25em 0;
  line-height: 1.8;
}

.task-result-text :deep(h1),
.task-result-text :deep(h2),
.task-result-text :deep(h3),
.task-result-text :deep(h4),
.task-result-text :deep(h5),
.task-result-text :deep(h6) {
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.4;
}

.task-result-text :deep(code) {
  background-color: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
  color: var(--accent-blue);
}

.task-result-text :deep(pre) {
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 0.75em 0;
}

.task-result-text :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: var(--text-primary);
}

.task-result-time {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.task-result-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.task-result-loading .loading-text {
  color: var(--text-secondary);
  font-size: 15px;
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
  margin-bottom: 40px;
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

/* 隐藏"查看原片"前的图片（消息列表区域） */
.message-text :deep(.hidden-original-image) {
  display: none !important;
}

/* "查看原片"链接悬浮显示缩略图（消息列表区域） */
.message-text :deep(.hover-image-link) {
  position: relative;
}

.message-text :deep(.hover-image-link::after) {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  width: 280px;
  height: 158px;
  background-image: var(--hover-image-url);
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 1000;
}

.message-text :deep(.hover-image-link:hover::after) {
  opacity: 1;
  transform: translateX(-50%) translateY(-12px);
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
  margin-bottom: 40px;
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

.video-count-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
}

.video-count-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
}

.video-count-input {
  padding: 6px 12px;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: all 0.2s ease;
  min-width: 120px;
  width: 150px;
}

.video-count-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--accent-blue-light);
}

.video-count-input:hover {
  border-color: var(--border-medium);
}

.video-count-input::-webkit-inner-spin-button,
.video-count-input::-webkit-outer-spin-button {
  opacity: 1;
  cursor: pointer;
}

.video-count-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: auto;
}

@media (max-width: 768px) {
  .video-count-selector {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .video-count-hint {
    width: 100%;
    margin-left: 0;
  }
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

