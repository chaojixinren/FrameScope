<template>
  <div class="home-page">
    <section class="page-shell">
      <div class="page-shell__main">
        <h1 class="page-title">FrameScope — 帧析云鉴系统</h1>
        <p class="page-subtitle">
          输入问题后系统将自动检索相关视频并完成多视角分析，输出结构化结论与对比摘要。
        </p>
      </div>
      <div class="page-shell__actions">
        <span class="tag">Beta</span>
      </div>
    </section>

    <div class="content-grid">
      <section class="panel overview-panel">
        <div class="panel__hd">
          <div>
            <h2 class="panel-title">任务流程</h2>
            <p class="panel-subtitle">3 步完成视频内容理解与摘要。</p>
          </div>
        </div>
        <div class="panel__bd">
          <div class="flow-steps">
            <div class="flow-step">
              <div class="step-index">01</div>
              <div>
                <div class="step-title">提交问题</div>
                <div class="step-desc">输入你关注的主题或对比点。</div>
              </div>
            </div>
            <div class="flow-step">
              <div class="step-index">02</div>
              <div>
                <div class="step-title">智能检索</div>
                <div class="step-desc">自动匹配相关视频并生成分析任务。</div>
              </div>
            </div>
            <div class="flow-step">
              <div class="step-index">03</div>
              <div>
                <div class="step-title">结果输出</div>
                <div class="step-desc">获得结构化对比与关键结论。</div>
              </div>
            </div>
          </div>

          <div class="metric-grid">
            <div class="metric">
              <div class="metric__label">视频数量</div>
              <div class="metric__value">{{ form.maxVideos }}</div>
              <div class="metric__hint">建议 3-10 个</div>
            </div>
            <div class="metric">
              <div class="metric__label">问题字数</div>
              <div class="metric__value">{{ form.question.trim().length }}</div>
              <div class="metric__hint">清晰问题提升命中率</div>
            </div>
            <div class="metric">
              <div class="metric__label">当前状态</div>
              <div class="metric__value status" :data-state="canSubmit ? 'ready' : 'draft'">
                {{ canSubmit ? '可提交' : '待完善' }}
              </div>
              <div class="metric__hint">填写完整后即可创建</div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel form-panel">
        <div class="panel__hd">
          <div>
            <h2 class="panel-title">创建新任务</h2>
            <p class="panel-subtitle">支持对比评测、参数解析与多角度总结。</p>
          </div>
          <span class="badge">Console</span>
        </div>

        <div class="panel__bd">
          <div class="form-group">
            <label for="question-input">你的问题</label>
            <textarea
              id="question-input"
              v-model="form.question"
              class="textarea"
              placeholder="例如：iPhone 15 和 iPhone 14 的差异是什么？哪个更值得购买？"
              rows="4"
              aria-describedby="question-hint"
            ></textarea>
            <div id="question-hint" class="form-hint">
              输入你想了解的问题，系统将自动检索相关视频并进行分析。
            </div>
          </div>

          <div class="form-group">
            <label for="video-count-input">分析视频数量</label>
            <input
              id="video-count-input"
              v-model.number="form.maxVideos"
              type="number"
              class="input"
              min="1"
              max="20"
              placeholder="请输入视频数量（1-20）"
              aria-describedby="count-hint"
            />
            <div id="count-hint" class="form-hint">
              建议 3-10 个，默认 5 个，数量越多分析耗时越长。
            </div>
          </div>

          <div v-if="error" class="alert alert--danger" role="alert">
            {{ error }}
          </div>

          <button
            type="button"
            class="btn btn--primary submit-btn"
            :class="{ 'is-loading': loading }"
            :disabled="loading || !canSubmit"
            @click="handleCreateTask"
          >
            <span v-if="loading" class="btn__spinner" aria-hidden="true"></span>
            {{ loading ? '创建中...' : '创建任务' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useConversationStore } from '@/stores/conversation'
import { useTaskStore } from '@/stores/task'
import type { Task } from '@/stores/task'

const router = useRouter()
const conversationStore = useConversationStore()
const taskStore = useTaskStore()

const form = ref({
  question: '',
  maxVideos: 5
})

const loading = ref(false)
const error = ref('')

const canSubmit = computed(() => {
  const questionValid = form.value.question.trim().length > 0
  const videoCountValid = form.value.maxVideos >= 1 && form.value.maxVideos <= 20
  return !loading.value && questionValid && videoCountValid
})

const handleCreateTask = async () => {
  if (!canSubmit.value) return

  loading.value = true
  error.value = ''

  try {
    const questionText = form.value.question.trim()

    const conversation = await conversationStore.createConversation()

    const defaultVideoIds = ['BV1Dk4y1X71E', 'BV1JD4y1z7vc', 'BV1KL411N7KV', 'BV1m94y1E72S']

    const taskId = `task_${Date.now()}`
    const task: Task = {
      id: taskId,
      title: questionText,
      videoUrls: defaultVideoIds.map(id => `https://www.bilibili.com/video/${id}`),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'pending'
    }

    taskStore.addTask(task)
    taskStore.saveTasks()

    const maxVideos = form.value.maxVideos || 5
    console.log('Home页面：跳转到TaskDetail，视频数量:', maxVideos, 'form.value.maxVideos:', form.value.maxVideos)
    router.push({
      name: 'Task',
      params: { id: taskId },
      query: {
        conversationId: conversation.id,
        question: questionText,
        maxVideos: maxVideos.toString()
      }
    })
  } catch (err: any) {
    error.value = err.message || '创建任务失败，请稍后重试'
    console.error('创建任务失败:', err)
    loading.value = false
  }
}
</script>

<style scoped>
.home-page {
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

.page-title {
  margin: 0 0 8px;
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 600;
  color: var(--text-primary);
}

.page-subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: var(--lh-relaxed);
}

.page-shell__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: var(--space-4);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.panel-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

.overview-panel .panel__bd {
  display: grid;
  gap: var(--space-3);
}

.flow-steps {
  display: grid;
  gap: var(--space-2);
}

.flow-step {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(91, 212, 255, 0.2);
  background: var(--surface-1);
}

.step-index {
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.step-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-2);
}

.metric {
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  border: 1px solid var(--border-light);
}

.metric__label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.metric__value {
  font-size: 20px;
  font-weight: 600;
  margin: 6px 0 4px;
  color: var(--text-primary);
}

.metric__value.status {
  color: var(--primary);
}

.metric__value.status[data-state="draft"] {
  color: var(--text-tertiary);
}

.metric__hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-panel .panel__bd {
  display: grid;
  gap: var(--space-3);
}

.form-group {
  display: grid;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  color: var(--text-secondary);
}

.form-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.alert {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.alert--danger {
  background: rgba(255, 107, 107, 0.12);
  border: 1px solid rgba(255, 107, 107, 0.35);
  color: #ffd0d0;
}

.submit-btn {
  width: 100%;
  justify-content: center;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .page-shell {
    flex-direction: column;
  }

  .page-shell__actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
