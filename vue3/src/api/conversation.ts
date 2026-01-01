import api from '@/axios'

// 对话相关接口类型定义
export interface Conversation {
  id: number
  user_id: number
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

export interface ConversationsResponse {
  conversations: Conversation[]
  total: number
  limit: number
  offset: number
}

// 对话相关 API
export const conversationApi = {
  // 获取对话列表
  getConversations: async (limit: number = 50, offset: number = 0): Promise<ConversationsResponse> => {
    const response = await api.get<ConversationsResponse>('/conversations', {
      params: { limit, offset }
    })
    return response.data
  },

  // 获取对话详情（包含消息列表）
  getConversation: async (conversationId: number): Promise<ConversationDetail> => {
    const response = await api.get<ConversationDetail>(`/conversations/${conversationId}`)
    return response.data
  },

  // 创建新对话
  createConversation: async (title?: string): Promise<Conversation> => {
    const response = await api.post<Conversation>('/conversations', {
      title: title || ''
    })
    return response.data
  },

  // 更新对话标题
  updateConversationTitle: async (conversationId: number, title: string): Promise<void> => {
    await api.put(`/conversations/${conversationId}/title`, { title })
  },

  // 删除对话
  deleteConversation: async (conversationId: number): Promise<void> => {
    await api.delete(`/conversations/${conversationId}`)
  }
}

