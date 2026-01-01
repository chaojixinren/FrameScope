import api from '@/axios'

export interface VideoInfo {
  url: string
  platform?: string
  title?: string
  description?: string
  popularity_score?: number
}

export interface MultiVideoRequest {
  question: string
  session_id?: string
  conversation_id?: number
  model_name?: string
  provider_id?: string
  max_videos?: number  // 最大视频数量（可选，默认5）
  video_urls?: string[]  // 用户提供的视频URL列表（可选，如果提供则优先使用这些URL）
  prefetched_videos?: VideoInfo[]
  search_query?: string
}


export interface MultiVideoResponse {
  success: boolean
  answer: string
  metadata?: {
    total_videos?: number
    processing_time?: number
    conversation_id?: number
  }
  video_urls?: VideoInfo[]
  search_query?: string
}

export interface VideoSearchRequest {
  question: string
  max_videos?: number
  video_urls?: string[]
}

export interface VideoSearchResponse {
  video_urls: VideoInfo[]
  search_query?: string
}

export const multiVideoApi = {
  // 发送多视频查询请求
  query: async (data: MultiVideoRequest): Promise<MultiVideoResponse> => {
    console.log('发送API请求，数据:', JSON.stringify(data, null, 2))
    const response = await api.post<MultiVideoResponse>('/multi_video', data)
    return response.data
  },

  searchVideos: async (data: VideoSearchRequest): Promise<VideoSearchResponse> => {
    const response = await api.post<VideoSearchResponse>('/video_search', data)
    return response.data
  }
}

