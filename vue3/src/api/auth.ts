import api from './index'
import { useUserStore } from '@/stores/user'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export interface AuthResponse {
  token: string
  user: {
    id: string
    username: string
    email?: string
  }
}

// 模拟 API - 实际开发时需要替换
export const authApi = {
  // 登录
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.post<AuthResponse>('/auth/login', data)
    // return response.data

    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (data.username && data.password) {
      const mockResponse: AuthResponse = {
        token: 'mock_token_' + Date.now(),
        user: {
          id: '1',
          username: data.username,
          email: data.email
        }
      }
      return mockResponse
    } else {
      throw new Error('用户名或密码不能为空')
    }
  },

  // 注册
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.post<AuthResponse>('/auth/register', data)
    // return response.data

    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (data.username && data.password) {
      const mockResponse: AuthResponse = {
        token: 'mock_token_' + Date.now(),
        user: {
          id: String(Date.now()),
          username: data.username,
          email: data.email
        }
      }
      return mockResponse
    } else {
      throw new Error('用户名或密码不能为空')
    }
  },

  // 获取当前用户信息
  getCurrentUser: async (): Promise<AuthResponse['user']> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.get<AuthResponse['user']>('/auth/me')
    // return response.data

    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 300))
    const userStore = useUserStore()
    return userStore.user || {
      id: '1',
      username: 'user'
    }
  }
}

