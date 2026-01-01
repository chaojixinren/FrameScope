<template>
  <div class="auth-page">
    <div class="panel auth-card">
      <div class="panel__hd auth-header">
        <div class="auth-mark" aria-hidden="true">⟁</div>
        <div>
          <h1 class="auth-title">注册账户</h1>
          <p class="auth-subtitle">创建新账户开始体验</p>
        </div>
      </div>

      <div class="panel__bd">
        <form @submit.prevent="handleRegister" class="auth-form" :aria-busy="loading">
          <div class="form-group">
            <label for="username">账号</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="input"
              placeholder="请输入账号"
              autocomplete="username"
              required
              :aria-invalid="!!error"
              :aria-describedby="error ? 'register-error' : undefined"
            />
          </div>

          <div class="form-group">
            <label for="email">邮箱（可选）</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="input"
              placeholder="请输入邮箱"
              autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label for="password">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="input"
              placeholder="请输入密码"
              autocomplete="new-password"
              required
              :aria-invalid="!!error"
              :aria-describedby="error ? 'register-error' : undefined"
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              class="input"
              placeholder="请再次输入密码"
              autocomplete="new-password"
              required
              :aria-invalid="!!error"
              :aria-describedby="error ? 'register-error' : undefined"
            />
          </div>

          <div v-if="error" id="register-error" class="alert alert--danger" role="alert">
            {{ error }}
          </div>

          <button
            type="submit"
            class="btn btn--primary auth-submit"
            :class="{ 'is-loading': loading }"
            :disabled="loading"
          >
            <span v-if="loading" class="btn__spinner" aria-hidden="true"></span>
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>

        <div class="auth-footer">
          <span class="text-secondary">已有账号？</span>
          <router-link to="/login" class="link">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')

const handleRegister = async () => {
  if (loading.value) return

  if (form.value.password !== form.value.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }

  if (form.value.password.length < 6) {
    error.value = '密码长度至少为 6 位'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const { confirmPassword, ...registerData } = form.value
    const response = await authApi.register(registerData)
    userStore.setToken(response.token)
    userStore.setUser(response.user)

    router.push('/')
  } catch (err: any) {
    error.value = err.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--space-4);
}

.auth-card {
  width: min(440px, 100%);
}

.auth-header {
  gap: 16px;
}

.auth-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  font-size: 18px;
  color: var(--primary);
  background: linear-gradient(135deg, rgba(91, 212, 255, 0.18), rgba(139, 123, 255, 0.18));
  border: 1px solid rgba(91, 212, 255, 0.4);
}

.auth-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
}

.auth-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

.auth-form {
  display: flex;
  flex-direction: column;
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

.auth-submit {
  width: 100%;
  justify-content: center;
}

.auth-footer {
  margin-top: var(--space-3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
}

.link {
  color: var(--primary);
}
</style>
