<template>
  <div class="task-detail-page">
    <section class="page-shell">
      <div class="page-shell__main">
        <div class="page-kicker">任务中心</div>
        <h1 class="page-title">{{ conversationStore.currentConversation?.title || '新对话' }}</h1>
        <p class="page-subtitle">
          {{
            conversationStore.currentConversation
              ? formatDate(conversationStore.currentConversation.created_at)
              : '等待问题输入后创建对话'
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
          删除对话
        </button>
      </div>
    </section>

    <div class="panel toolbar">
      <div class="panel__bd toolbar__content">
        <div class="toolbar-group">
          <label for="message-search">对话检索</label>
          <input
            id="message-search"
            v-model="searchQuery"
            class="input"
            placeholder="输入关键词（仅本地筛选）"
          />
        </div>
        <div class="toolbar-meta">
          <div class="meta-item">
            <span class="meta-label">状态</span>
            <span
              class="tag status-tag"
              :data-state="sendingQuestion ? 'processing' : firstAnswer ? 'completed' : 'idle'"
            >
              {{ sendingQuestion ? '分析中' : firstAnswer ? '已完成' : '待提问' }}
            </span>
          </div>
          <div class="meta-item">
            <span class="meta-label">视频数</span>
            <span class="badge">{{ currentVideos.length || selectedVideoCount }} 个</span>
          </div>
        </div>
        <button type="button" class="btn btn--primary" @click="focusComposer">快速提问</button>
      </div>
    </div>

    <div v-if="errorMessage" class="panel error-panel">
      <div class="panel__bd error-state">
        <div class="error-icon" aria-hidden="true">?</div>
        <div>
          <div class="error-title">操作失败</div>
          <div class="error-desc">{{ errorMessage }}</div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="panel loading-panel">
      <div class="panel__bd loading-state" role="status" aria-live="polite">
        <div class="loading-orbit" aria-hidden="true"></div>
        <div class="loading-text">正在加载对话...</div>
        <div class="skeleton skeleton-line"></div>
        <div class="skeleton skeleton-block"></div>
        <div class="skeleton skeleton-block"></div>
      </div>
    </div>

    <div v-else class="content-grid">
      <aside class="content-left">
        <div class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">对话概览</h2>
              <p class="panel-subtitle">当前任务的关键信息概览。</p>
            </div>
            <span class="badge">Console</span>
          </div>
          <div class="panel__bd meta-list">
            <div class="meta-row">
              <span class="meta-label">创建时间</span>
              <span class="meta-value">
                {{
                  conversationStore.currentConversation
                    ? formatDate(conversationStore.currentConversation.created_at)
                    : '?'
                }}
              </span>
            </div>
            <div class="meta-row">
              <span class="meta-label">当前状态</span>
              <span class="meta-value">
                {{ sendingQuestion ? '分析中' : firstAnswer ? '已完成' : '待提问' }}
              </span>
            </div>
            <div class="meta-row">
              <span class="meta-label">视频数量</span>
              <span class="meta-value">{{ currentVideos.length || selectedVideoCount }} 个</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">对话 ID</span>
              <span class="meta-value">#{{ conversationId || '?' }}</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">视频列表</h2>
              <p class="panel-subtitle">本次分析使用的视频集合。</p>
            </div>
          </div>
          <div class="panel__bd">
            <div v-if="searchingVideos" class="empty-inline">
              <div class="loading-orbit" aria-hidden="true"></div>
              <div>正在获取视频列表...</div>
            </div>
            <div v-else-if="currentVideos.length > 0" class="video-list">
              <a
                v-for="(video, index) in currentVideos"
                :key="video.url || `video-${index}`"
                class="video-item"
                :href="video.url"
                target="_blank"
                rel="noopener"
              >
                <span class="video-index">{{ index + 1 }}</span>
                <div class="video-main">
                  <div class="video-title">{{ video.title || video.url }}</div>
                  <div class="video-desc">{{ video.description || '暂无简介' }}</div>
                  <div class="video-link">{{ video.url }}</div>
                </div>
              </a>
            </div>
            <div v-else class="empty-inline">
              <div class="empty-icon" aria-hidden="true">?</div>
              <div>尚未获取视频列表</div>
            </div>
          </div>
        </div>
      </aside>

      <section class="content-right">
        <div class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">分析结果</h2>
              <p class="panel-subtitle">任务执行与内容摘要。</p>
            </div>
            <span class="tag">Analysis</span>
          </div>
          <div class="panel__bd">
            <div v-if="sendingQuestion && messages.length === 0" class="task-steps">
              <div class="task-step">
                <div class="step-status" :class="searchingVideos ? 'loading' : 'completed'">
                  <div v-if="searchingVideos" class="loading-spinner-small"></div>
                  <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="step-content">
                  <div class="step-title">
                    {{ searchingVideos ? '正在获取视频链接...' : '已获取视频链接' }}
                  </div>
                  <div v-if="currentVideos.length > 0" class="video-list-inline">
                    <span v-for="(video, index) in currentVideos" :key="video.url || `video-${index}`" class="video-chip">
                      视频 {{ index + 1 }} · {{ video.title || video.url }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="task-step">
                <div class="step-status loading">
                  <div class="loading-spinner-small"></div>
                </div>
                <div class="step-content">
                  <div class="step-title">{{ searchingVideos ? '等待视频检索完成' : '正在生成分析结果...' }}</div>
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
                  <div class="step-title">已获取视频链接</div>
                </div>
              </div>

              <div class="task-step" v-if="currentVideos.length > 0">
                <div class="step-status completed">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M13.5 4L6 11.5L2.5 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </div>
                <div class="step-content">
                  <div class="step-title">已识别相关视频</div>
                  <div class="video-list-inline">
                    <span v-for="(video, index) in currentVideos" :key="video.url || `video-${index}`" class="video-chip">
                      视频 {{ index + 1 }} · {{ video.title || video.url }}
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
                  <div class="step-title">完成内容解析与摘要输出</div>
                </div>
              </div>

              <div class="analysis-result markdown" v-html="formatAnswer(firstAnswer.content)"></div>
              <div class="task-result-time">{{ formatTime(firstAnswer.created_at) }}</div>
            </div>

            <div v-else class="empty-state">
              <div class="empty-icon" aria-hidden="true">?</div>
              <div class="empty-title">暂未生成结果</div>
              <div class="empty-desc">提交问题后将自动拉取视频并生成分析。</div>
              <button type="button" class="btn btn--ghost" @click="focusComposer">立即提问</button>
            </div>
          </div>
        </div>

        <div v-if="hasFollowupConversation" class="panel">
          <div class="panel__hd">
            <div>
              <h2 class="panel-title">对话记录</h2>
              <p class="panel-subtitle">后续提问与 AI 回答。</p>
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
                    <div class="typing-indicator" aria-label="正在生成回答">
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
                {{ conversationId && (firstAnswer || hasFollowupConversation) ? '继续对话' : '开始对话' }}
              </h2>
              <p class="panel-subtitle">基于结果继续追问，获得更深入的分析。</p>
            </div>
          </div>
          <div class="panel__bd">
            <div class="qa-input-area">
              <div v-if="!conversationId || messages.length === 0" class="video-count-selector">
                <label for="video-count-input" class="video-count-label">分析视频数量</label>
                <input
                  id="video-count-input"
                  v-model.number="selectedVideoCount"
                  type="number"
                  class="input video-count-input"
                  min="1"
                  max="20"
                  placeholder="请输入视频数量（1-20）"
                  aria-describedby="video-count-hint"
                />
                <span id="video-count-hint" class="video-count-hint">
                  系统将搜索并分析指定数量的相关视频（建议 3-10 个）
                </span>
              </div>

              <div class="qa-input-container">
                <label class="sr-only" for="question-textarea">输入问题</label>
                <textarea
                  id="question-textarea"
                  ref="composerRef"
                  v-model="questionInput"
                  class="textarea qa-textarea"
                  placeholder="请输入你的问题，例如：索尼A7M4相机怎么样？"
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
import { multiVideoApi, type MultiVideoResponse, type VideoInfo } from '@/api/multi_video'
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
// 当前任务的视频信息列表
const currentVideos = ref<VideoInfo[]>([])
const searchingVideos = ref(false)
// 选择的视频数量（默认5个，可以从URL参数中获取）
const selectedVideoCount = ref<number>(5)

const errorMessage = ref('')
const searchQuery = ref('')
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
    let prefetchedVideos: VideoInfo[] | undefined
    let prefetchedQuery: string | undefined
    
    if (isFirstAnswer) {
      // 第一次回答：先执行 video_search，优先返回视频列表给前端渲染
      currentVideos.value = []
      const maxVideosToUse = selectedVideoCount.value || 5
      console.log('发送API请求，视频数量:', maxVideosToUse, '提取的URL数量:', extractedUrls.length)
      
      searchingVideos.value = true
      try {
        const searchResult = await multiVideoApi.searchVideos({
          question: cleanedQuestion || currentInput,
          max_videos: maxVideosToUse,
          video_urls: extractedUrls.length > 0 ? extractedUrls : undefined
        })
        prefetchedVideos = searchResult.video_urls || []
        prefetchedQuery = searchResult.search_query
        currentVideos.value = prefetchedVideos
      } catch (error) {
        console.error('视频搜索失败:', error)
      } finally {
        searchingVideos.value = false
      }
      
      // 使用预取的视频结果继续完整分析流程，避免重复搜索
      response = await multiVideoApi.query({
        question: cleanedQuestion || currentInput, // 如果清理后为空，使用原始文本
        conversation_id: targetConversationId,
        max_videos: maxVideosToUse,
        video_urls: extractedUrls.length > 0 ? extractedUrls : undefined,
        prefetched_videos: prefetchedVideos && prefetchedVideos.length > 0 ? prefetchedVideos : undefined,
        search_query: prefetchedQuery
      })
    } else {
      // 后续对话：使用 multi_video 接口（根据上下文进行正常对话）
      response = await multiVideoApi.query({
        question: cleanedQuestion || currentInput, // 如果清理后为空，使用原始文本
        conversation_id: targetConversationId,
        video_urls: extractedUrls.length > 0 ? extractedUrls : undefined
      })
    }

    if (response.video_urls && response.video_urls.length > 0 && currentVideos.value.length === 0) {
      currentVideos.value = response.video_urls
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
  display: grid;
  grid-template-columns: 1.4fr 1fr auto;
  gap: var(--space-3);
  align-items: end;
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
  justify-items: start;
}

.loading-orbit {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--border-light);
  border-top-color: var(--primary);
  box-shadow: var(--glow-1);
  animation: spin 0.9s linear infinite;
}

.loading-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

.skeleton-line {
  height: 12px;
}

.skeleton-block {
  height: 96px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.4fr);
  gap: var(--space-4);
}

.content-left,
.content-right {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
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
  align-items: flex-start;
  gap: 12px;
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

.video-main {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.video-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
}

.video-desc {
  font-size: 12px;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-link {
  font-size: 11px;
  color: var(--text-tertiary);
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
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  .content-grid {
    grid-template-columns: 1fr;
  }

  .toolbar__content {
    grid-template-columns: 1fr;
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
