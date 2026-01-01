import api from '@/axios'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string  // 前端使用的字段，可选
  phone_number?: string  // 后端使用的字段，可选
  avatar?: string  // 后端使用的字段，可选
}

// 后端登录/注册响应数据格式
interface LoginResponseData {
  access_token: string
  token_type: string
  user_id: number
  username: string
}

interface RegisterResponseData {
  user_id: number
  username: string
  phone_number: string | null
  avatar: string | null
  access_token: string
  token_type: string
}

// 后端用户信息响应数据格式
interface UserInfoData {
  id: number
  username: string
  phone_number: string | null
  avatar: string | null
  is_online: number
  created_at: string | null
}

export interface AuthResponse {
  token: string
  user: {
    id: string
    username: string
    email?: string
  }
}

// 认证相关 API
export const authApi = {
  // 登录
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<LoginResponseData>('/auth/login_json', {
      username: data.username,
      password: data.password
    })
    
    const responseData = response.data
    
    return {
      token: responseData.access_token,
      user: {
        id: String(responseData.user_id),
        username: responseData.username
      }
    }
  },

  // 注册
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    // 构建请求体，只发送后端需要的字段
    const requestBody: {
      username: string
      password: string
      phone_number?: string
      avatar?: string
    } = {
      username: data.username,
      password: data.password
    }
    
    // 如果提供了phone_number，则使用phone_number；否则如果提供了email，可以将email作为phone_number（可选）
    if (data.phone_number) {
      requestBody.phone_number = data.phone_number
    }
    
    if (data.avatar) {
      requestBody.avatar = data.avatar
    }
    
    const response = await api.post<RegisterResponseData>('/auth/register', requestBody)
    
    const responseData = response.data
    
    return {
      token: responseData.access_token,
      user: {
        id: String(responseData.user_id),
        username: responseData.username
      }
    }
  },

  // 获取当前用户信息
  getCurrentUser: async (): Promise<AuthResponse['user']> => {
    const response = await api.get<UserInfoData>('/auth/me')
    
    const responseData = response.data
    
    return {
      id: String(responseData.id),
      username: responseData.username
    }
  }
}

