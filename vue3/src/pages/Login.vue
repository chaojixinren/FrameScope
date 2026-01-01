<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">视频内容理解</h1>
      <p class="login-subtitle">登录以继续</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">账号</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="input"
            placeholder="请输入账号"
            required
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
            required
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button
          type="submit"
          class="btn btn-primary login-btn"
          :disabled="loading"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <div class="login-footer">
        <span class="text-secondary">还没有账号？</span>
        <router-link to="/register" class="link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (loading.value) return

  loading.value = true
  error.value = ''

  try {
    const response = await authApi.login(form.value)
    userStore.setToken(response.token)
    userStore.setUser(response.user)

    // 重定向到原始页面或首页
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    error.value = err.message || '登录失败，请检查账号密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background-color: var(--bg-secondary);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 40px;
  box-shadow: var(--shadow-md);
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 32px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.error-message {
  padding: 12px;
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  color: #ef4444;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  margin-top: 8px;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.link {
  color: var(--accent-blue);
  font-weight: 500;
}
</style>

