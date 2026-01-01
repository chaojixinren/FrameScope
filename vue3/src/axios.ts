import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 Bearer token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    if (userStore.token && config.headers) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 后端响应格式接口
interface BackendResponse<T = any> {
  code: number
  msg: string
  data: T
}

// 响应拦截器 - 处理后端响应格式和错误
api.interceptors.response.use(
  (response: AxiosResponse<BackendResponse>) => {
    const { code, msg, data } = response.data
    
    // 如果code不为0，说明是业务错误，抛出错误
    if (code !== 0) {
      const error = new Error(msg || '请求失败')
      ;(error as any).code = code
      return Promise.reject(error)
    }
    
    // 将后端的data字段提取到response.data，保持axios响应结构
    response.data = data as any
    return response
  },
  (error) => {
    // 处理HTTP错误
    if (error.response?.status === 401) {
      // Token 过期或无效，清除登录状态
      const userStore = useUserStore()
      userStore.logout()
      // 可以在这里跳转到登录页
      window.location.href = '/login'
    }
    
    // 如果后端返回了错误信息，使用后端的错误信息
    if (error.response?.data?.msg) {
      error.message = error.response.data.msg
    }
    
    return Promise.reject(error)
  }
)

export default api




