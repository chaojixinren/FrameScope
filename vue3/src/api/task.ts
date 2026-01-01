import api from './index'
import type { Task } from '@/stores/task'

export interface CreateTaskRequest {
  title: string
}

// 模拟 API - 实际开发时需要替换
export const taskApi = {
  // 创建任务
  createTask: async (data: CreateTaskRequest): Promise<Task> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.post<Task>('/tasks', data)
    // return response.data

    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const mockTask: Task = {
      id: 'task_' + Date.now(),
      title: data.title,
      videoUrls: [], // 后端会自动获取视频列表
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'pending'
    }
    return mockTask
  },

  // 获取任务列表
  getTasks: async (): Promise<Task[]> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.get<Task[]>('/tasks')
    // return response.data

    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 300))
    return []
  },

  // 获取任务详情
  getTask: async (taskId: string): Promise<Task> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.get<Task>(`/tasks/${taskId}`)
    // return response.data

    // 模拟响应
    await new Promise(resolve => setTimeout(resolve, 300))
    throw new Error('任务不存在')
  },

  // 开始分析任务
  analyzeTask: async (taskId: string): Promise<Task> => {
    // TODO: 替换为真实 API 调用
    // const response = await api.post<Task>(`/tasks/${taskId}/analyze`)
    // return response.data

    // 模拟响应 - 延迟模拟分析过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const mockTask: Task = {
      id: taskId,
      title: '示例任务',
      videoUrls: ['https://example.com/video1', 'https://example.com/video2'],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'completed',
      result: {
        commonDescriptions: [
          '产品外观设计简洁',
          '性能表现良好',
          '价格相对合理'
        ],
        contradictions: [
          {
            topic: '电池续航',
            points: [
              { video: '视频1', view: '续航可达10小时' },
              { video: '视频2', view: '续航仅为6小时，不够用' }
            ]
          }
        ],
        uniqueFeatures: [
          {
            video: '视频1',
            features: ['强调了快充功能', '提到了特殊材质']
          },
          {
            video: '视频2',
            features: ['重点关注了性价比', '提到了竞品对比']
          }
        ]
      }
    }
    return mockTask
  }
}

