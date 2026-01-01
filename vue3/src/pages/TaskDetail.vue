<template>
  <div class="task-detail-page">
    <section class="page-shell">
      <div class="page-shell__main">
        <div class="page-kicker">任务</div>
        <h1 class="page-title">{{ conversationStore.currentConversation?.title || '未命名任务' }}</h1>
        <p class="page-subtitle">
          {{
            conversationStore.currentConversation
              ? formatDate(conversationStore.currentConversation.created_at)
              : '暂无创建时间'
          }}
        </p>
      </div>
      <div class="page-shell__actions">
        <button
          v-if="conversationId"
          type="button"
          class="btn btn--danger"
          :class="{ 'is-loading': deletingConversation }"
          :disabled="deletingConversation"
          @click="handleDeleteConversation"
        >
          <span v-if="deletingConversation" class="btn__spinner" aria-hidden="true"></span>
          删除
        </button>
      </div>
    </section>

    

    <div v-if="errorMessage" class="panel error-panel">
      <div class="panel__bd error-state">
        <div class="error-icon" aria-hidden="true">⚠</div>
        <div>
          <div class="error-title">出错了</div>
          <div class="error-desc">{{ errorMessage }}</div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="panel loading-panel">
      <div class="panel__bd loading-state">
        <div class="skeleton skeleton-line"></div>
        <div class="skeleton skeleton-block"></div>
        <div class="skeleton skeleton-block"></div>
      </div>
    </div>

    <div v-else class="content-single">
      <section class="content-main">
        <!-- 视频链接卡片 -->
        <div class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">相关视频</h2>
              <p class="panel-subtitle">本次分析涉及的视频</p>
            </div>
          </div>
          <div class="panel__bd">
            <div v-if="currentVideoIds.length > 0" class="video-list">
              <a
                v-for="(videoId, index) in currentVideoIds"
                :key="videoId"
                class="video-item"
                :href="`https://www.bilibili.com/video/${videoId}`"
                target="_blank"
                rel="noopener"
              >
                <span class="video-index">{{ index + 1 }}</span>
                <span class="video-id">{{ videoId }}</span>
              </a>
            </div>
            <div v-else class="empty-inline">
              <div class="empty-icon" aria-hidden="true">📹</div>
              <div>暂无视频</div>
            </div>
          </div>
        </div>

        <!-- 分析结果卡片 -->
        <div class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">分析结果</h2>
              <p class="panel-subtitle">AI分析的结果展示</p>
            </div>
            <span class="tag">Analysis</span>
          </div>
          <div class="panel__bd">
            <div v-if="sendingQuestion && messages.length === 0" class="task-steps">
              <div class="task-step">
                <div class="step-status loading">
                  <div class="loading-spinner-small"></div>
                </div>
                <div class="step-content">
                  <div class="step-title">正在分析中...</div>
                </div>
              </div>
            </div>

            <div v-else-if="firstAnswer" class="task-steps">
              <div class="task-step">
                <div class="step-status completed">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="step-content">
                  <div class="step-title">问题已提交</div>
                </div>
              </div>

              <div class="task-step" v-if="currentVideoIds.length > 0">
                <div class="step-status completed">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="step-content">
                  <div class="step-title">视频已选择</div>
                  <div class="video-list-inline">
                    <span v-for="(videoId, index) in currentVideoIds" :key="videoId" class="video-chip">
                      视频 {{ index + 1 }}：{{ videoId }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="task-step">
                <div class="step-status completed">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="step-content">
                  <div class="step-title">分析结果已生成</div>
                </div>
              </div>

              <div class="analysis-result markdown" v-html="formatAnswer(firstAnswer.content)"></div>
              <div class="task-result-time">{{ formatTime(firstAnswer.created_at) }}</div>
            </div>

            <div v-else class="empty-state">
              <div class="empty-icon" aria-hidden="true">💭</div>
              <div class="empty-title">暂无结果</div>
              <div class="empty-desc">输入问题开始分析视频内容</div>
              <button type="button" class="btn btn--ghost" @click="focusComposer">开始提问</button>
            </div>
          </div>
        </div>

        <!-- 后续评论 -->
        <div v-if="hasFollowupConversation" class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">后续对话</h2>
              <p class="panel-subtitle">与 AI 继续交流</p>
            </div>
          </div>
          <div class="panel__bd">
            <div class="messages-list">
              <div
                v-for="(msg, index) in followupMessages"
                :key="`msg-${msg.id || index}-${msg.created_at}`"
                class="message-item"
                :class="msg.role"
              >
                <div class="message-content">
                  <div class="message-text markdown" v-html="formatAnswer(msg.content)"></div>
                  <div class="message-time">{{ formatTime(msg.created_at) }}</div>
                </div>
              </div>

              <div v-if="sendingQuestion && messages.length > 0" class="message-item assistant">
                <div class="message-content">
                  <div class="message-text">
                    <div class="typing-indicator" aria-label="正在输入">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">
                {{ conversationId && (firstAnswer || hasFollowupConversation) ? '继续提问' : '提问' }}
              </h2>
              <p class="panel-subtitle">输入您的问题，AI将为您分析</p>
            </div>
          </div>
          <div class="panel__bd">
            <div class="qa-input-area">
              <div v-if="!conversationId || messages.length === 0" class="video-count-selector">
                <label for="video-count-input" class="video-count-label">视频数量</label>
                <input
                  id="video-count-input"
                  v-model.number="selectedVideoCount"
                  type="number"
                  class="input video-count-input"
                  min="1"
                  max="20"
                  placeholder="请输入1-20之间的数字"
                  aria-describedby="video-count-hint"
                />
                <span id="video-count-hint" class="video-count-hint">
                  建议选择3-10个视频以获得最佳效果
                </span>
              </div>

              <div class="qa-input-container">
                <label class="sr-only" for="question-textarea">问题</label>
                <textarea
                  id="question-textarea"
                  ref="composerRef"
                  v-model="questionInput"
                  class="textarea qa-textarea"
                  placeholder="例如：请分析A7M4相机的优缺点"
                  rows="3"
                  @keydown.enter.prevent="handleEnterKey"
                  aria-describedby="qa-hint"
                ></textarea>
                <button
                  type="button"
                  class="btn btn--primary qa-send-btn"
                  :class="{ 'is-loading': sendingQuestion }"
                  :disabled="!canSendQuestion || sendingQuestion"
                  @click="sendQuestion"
                >
                  <svg
                    v-if="!sendingQuestion"
                    width="18"
                    height="18"
                    viewBox="0 0 20 20"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <span v-else class="btn__spinner" aria-hidden="true"></span>
                </button>
              </div>
              <div id="qa-hint" class="qa-hint">按 Enter 发送，Shift + Enter 换行</div>
            </div>
          </div>
        </div>
      </section>
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

const errorMessage = ref('')
const composerRef = ref<HTMLTextAreaElement | null>(null)

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

const focusComposer = () => {
  composerRef.value?.focus()
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
  errorMessage.value = ''
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
    const errorText = error?.response?.data?.detail || error?.message || '发送问题失败，请稍后重试'
    errorMessage.value = errorText
    alert(errorText)
    
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
    const errorText = error?.response?.data?.msg || error?.message || '删除对话失败，请稍后重试'
    errorMessage.value = errorText
    alert(errorText)
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
.task-detail-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.page-shell {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.page-shell__main {
  max-width: 720px;
}

.page-shell__actions .btn--danger {
  color: #dc2626;
  font-weight: 500;
}

/* 浅色模式下使用更深的红色以确保对比度 */
@media (prefers-color-scheme: light) {
  .page-shell__actions .btn--danger {
    color: #991b1b;
  }
  
  .page-shell__actions .btn--danger:hover {
    color: #7f1d1d;
  }
  
  .page-shell__actions .btn--danger:disabled {
    color: #991b1b;
    opacity: 0.6;
  }
}

.page-kicker {
  font-size: 12px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.page-title {
  margin: 0 0 6px;
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 600;
  color: var(--text-primary);
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: var(--lh-relaxed);
}

.toolbar__content {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  justify-content: flex-end;
}

.toolbar-group {
  display: grid;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.toolbar-meta {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
  align-items: center;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-tertiary);
}

.status-tag[data-state='processing'] {
  background: rgba(245, 200, 106, 0.16);
  border-color: rgba(245, 200, 106, 0.5);
  color: #f5c76a;
}

.status-tag[data-state='completed'] {
  background: rgba(43, 212, 163, 0.16);
  border-color: rgba(43, 212, 163, 0.5);
  color: #a5f2d9;
}

.status-tag[data-state='idle'] {
  background: rgba(148, 163, 184, 0.16);
  border-color: rgba(148, 163, 184, 0.4);
  color: var(--text-tertiary);
}

.error-panel .error-state {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.error-icon {
  font-size: 20px;
  color: var(--warning);
}

.error-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.error-desc {
  font-size: 13px;
  color: var(--text-tertiary);
}

.loading-state {
  display: grid;
  gap: 12px;
}

.skeleton-line {
  height: 12px;
}

.skeleton-block {
  height: 96px;
}

.content-single {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 100%;
}

.content-main .panel,
.error-panel,
.loading-panel {
  margin-left: var(--space-4);
  margin-right: var(--space-4);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.panel-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--text-tertiary);
}

.meta-list {
  display: grid;
  gap: 10px;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: var(--surface-1);
}

.meta-value {
  font-size: 13px;
  color: var(--text-primary);
}

.video-list {
  display: grid;
  gap: 8px;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(91, 212, 255, 0.2);
  background: var(--surface-1);
  color: var(--text-primary);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.video-item:hover {
  transform: translateY(-1px);
  border-color: rgba(91, 212, 255, 0.5);
  box-shadow: var(--glow-1);
}

.video-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 11px;
  color: var(--primary);
  background: rgba(91, 212, 255, 0.16);
}

.video-id {
  font-size: 13px;
  word-break: break-all;
}

.empty-inline {
  display: grid;
  place-items: center;
  text-align: center;
  gap: 6px;
  padding: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.empty-state {
  display: grid;
  gap: 8px;
  text-align: center;
  padding: 24px 12px;
  color: var(--text-tertiary);
}

.empty-title {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
}

.empty-desc {
  font-size: 12px;
}

.task-steps {
  display: grid;
  gap: 14px;
}

.task-step {
  display: flex;
  gap: 12px;
}

.step-status {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(91, 212, 255, 0.14);
  color: var(--primary);
}

.step-status.loading {
  background: rgba(245, 200, 106, 0.14);
  color: #f5c76a;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 14px;
  color: var(--text-primary);
}

.video-list-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.video-chip {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(91, 212, 255, 0.12);
  border: 1px solid rgba(91, 212, 255, 0.3);
  color: var(--primary);
}

.analysis-result {
  margin-top: 16px;
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: var(--surface-2);
}

.task-result-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 12px;
}

.messages-list {
  display: grid;
  gap: 16px;
}

.message-item {
  display: flex;
}

.message-item.user {
  justify-content: flex-end;
}

.message-content {
  max-width: 78%;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--border-light);
  background: var(--surface-3);
}

.message-item.user .message-content {
  background: linear-gradient(135deg, rgba(91, 212, 255, 0.9), rgba(74, 125, 255, 0.85));
  color: var(--text-on-primary);
  border-color: transparent;
}

.message-time {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.message-item.user .message-time {
  color: var(--text-on-primary-muted);
}

.qa-input-area {
  display: grid;
  gap: 12px;
}

.video-count-selector {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  background: var(--surface-2);
}

.video-count-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.video-count-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.qa-input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.qa-textarea {
  min-height: 96px;
  resize: vertical;
}

.qa-send-btn {
  width: 44px;
  height: 44px;
  padding: 0;
}

.qa-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 6px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

.loading-spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(245, 200, 106, 0.3);
  border-top-color: rgba(245, 200, 106, 0.8);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.markdown :deep(p) {
  margin: 0.6em 0;
  line-height: 1.7;
}

.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3),
.markdown :deep(h4) {
  color: var(--text-primary);
  margin: 1em 0 0.4em;
  line-height: 1.4;
}

.markdown :deep(ul),
.markdown :deep(ol) {
  margin: 0.6em 0;
  padding-left: 1.4em;
}

.markdown :deep(li) {
  margin: 0.3em 0;
}

.markdown :deep(code) {
  background: var(--surface-code);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.9em;
  color: var(--primary-2);
}

.markdown :deep(pre) {
  background: var(--surface-code);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 12px;
  overflow-x: auto;
}

.markdown :deep(blockquote) {
  margin: 0.6em 0;
  padding-left: 1em;
  border-left: 3px solid rgba(91, 212, 255, 0.6);
  color: var(--text-secondary);
}

.markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0;
}

.markdown :deep(th),
.markdown :deep(td) {
  border: 1px solid var(--border-light);
  padding: 8px 10px;
  text-align: left;
}

.markdown :deep(th) {
  background: var(--surface-code);
  position: sticky;
  top: 0;
}

.markdown :deep(img) {
  max-width: 100%;
  border-radius: 6px;
}

.markdown :deep(a) {
  color: var(--primary);
  text-decoration: none;
}

.markdown :deep(a:hover) {
  text-decoration: underline;
}

.markdown :deep(.hidden-original-image) {
  display: none !important;
}

.markdown :deep(.hover-image-link) {
  position: relative;
}

.markdown :deep(.hover-image-link::after) {
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
  background-color: var(--surface-tooltip);
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 20;
}

.markdown :deep(.hover-image-link:hover::after) {
  opacity: 1;
  transform: translateX(-50%) translateY(-12px);
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

@media (max-width: 1024px) {
  .toolbar__content {
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .page-shell {
    flex-direction: column;
  }

  .page-shell__actions {
    width: 100%;
    justify-content: flex-start;
  }

  .message-content {
    max-width: 100%;
  }

  .qa-input-container {
    flex-direction: column;
    align-items: stretch;
  }

  .qa-send-btn {
    width: 100%;
  }
}
</style>
