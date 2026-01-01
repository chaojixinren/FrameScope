import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface QuestionAnswer {
  id: string
  question: string
  answer: string
  createdAt: string
}

export interface Task {
  id: string
  title: string
  videoUrls: string[]
  createdAt: string
  updatedAt: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  result?: {
    commonDescriptions: string[]
    contradictions: Array<{
      topic: string
      points: Array<{
        video: string
        view: string
      }>
    }>
    uniqueFeatures: Array<{
      video: string
      features: string[]
    }>
  }
  questions?: QuestionAnswer[]
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)

  const addTask = (task: Task) => {
    tasks.value.unshift(task)
    currentTask.value = task
  }

  const updateTask = (taskId: string, updates: Partial<Task>) => {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      Object.assign(task, updates)
      if (currentTask.value?.id === taskId) {
        currentTask.value = { ...task }
      }
    }
  }

  const setCurrentTask = (task: Task | null) => {
    currentTask.value = task
  }

  const loadTasks = () => {
    // 从 localStorage 加载任务历史
    const savedTasks = localStorage.getItem('tasks')
    if (savedTasks) {
      tasks.value = JSON.parse(savedTasks)
    }
  }

  const saveTasks = () => {
    // 保存任务到 localStorage
    localStorage.setItem('tasks', JSON.stringify(tasks.value))
  }

  // 监听 tasks 变化，自动保存
  const watchTasks = () => {
    watch(tasks, saveTasks, { deep: true })
  }

  return {
    tasks,
    currentTask,
    addTask,
    updateTask,
    setCurrentTask,
    loadTasks,
    saveTasks,
    watchTasks
  }
})

