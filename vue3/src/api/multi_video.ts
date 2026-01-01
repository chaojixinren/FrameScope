import api from '@/axios'

export interface MultiVideoRequest {
  question: string
  session_id?: string
  conversation_id?: number
  model_name?: string
  provider_id?: string
}

export interface MultiVideoResponse {
  success: boolean
  answer: string
  metadata?: {
    total_videos?: number
    processing_time?: number
    conversation_id?: number
  }
}

export const multiVideoApi = {
  // 发送多视频查询请求
  query: async (data: MultiVideoRequest): Promise<MultiVideoResponse> => {
    const response = await api.post<MultiVideoResponse>('/multi_video', data)
    return response.data
  }
}

