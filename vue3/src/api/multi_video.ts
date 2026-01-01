import api from '@/axios'

export interface MultiVideoRequest {
  question: string
  session_id?: string
  conversation_id?: number
  model_name?: string
  provider_id?: string
}

export interface ExampleVideoRequest {
  question: string
  video_ids: string[]
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
  },

  // 发送示例视频查询请求（使用example目录下的视频）
  queryExample: async (data: ExampleVideoRequest): Promise<MultiVideoResponse> => {
    const response = await api.post<MultiVideoResponse>('/example_video', data)
    return response.data
  }
}

