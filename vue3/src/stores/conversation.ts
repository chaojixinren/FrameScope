import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { conversationApi, type Conversation, type Message } from '@/api/conversation'

export const useConversationStore = defineStore('conversation', () => {
  // 状态
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const currentMessages = ref<Message[]>([])
  const loading = ref(false)

  // 计算属性
  const hasConversations = computed(() => conversations.value.length > 0)

  // 获取对话列表
  const loadConversations = async () => {
    loading.value = true
    try {
      const response = await conversationApi.getConversations()
      conversations.value = response.conversations
      return response
    } catch (error) {
      console.error('加载对话列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取对话详情（包含消息）
  const loadConversation = async (conversationId: number) => {
    loading.value = true
    try {
      const detail = await conversationApi.getConversation(conversationId)
      currentConversation.value = {
        id: detail.id,
        user_id: detail.user_id,
        title: detail.title,
        created_at: detail.created_at,
        updated_at: detail.updated_at,
        message_count: detail.message_count
      }
      currentMessages.value = detail.messages || []
      return detail
    } catch (error) {
      console.error('加载对话详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建新对话
  const createConversation = async (title?: string): Promise<Conversation> => {
    try {
      const conversation = await conversationApi.createConversation(title)
      // 添加到列表开头
      conversations.value.unshift(conversation)
      return conversation
    } catch (error) {
      console.error('创建对话失败:', error)
      throw error
    }
  }

  // 设置当前对话
  const setCurrentConversation = (conversation: Conversation | null) => {
    currentConversation.value = conversation
    if (conversation) {
      loadConversation(conversation.id)
    } else {
      currentMessages.value = []
    }
  }

  // 添加消息到当前对话
  const addMessage = (message: Message) => {
    currentMessages.value.push(message)
  }

  // 更新对话标题
  const updateConversationTitle = async (conversationId: number, title: string) => {
    try {
      await conversationApi.updateConversationTitle(conversationId, title)
      // 更新本地状态
      const conversation = conversations.value.find(c => c.id === conversationId)
      if (conversation) {
        conversation.title = title
      }
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value.title = title
      }
    } catch (error) {
      console.error('更新对话标题失败:', error)
      throw error
    }
  }

  // 删除对话
  const deleteConversation = async (conversationId: number) => {
    try {
      await conversationApi.deleteConversation(conversationId)
      // 从列表中移除
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
      // 如果删除的是当前对话，清空当前对话
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value = null
        currentMessages.value = []
      }
    } catch (error) {
      console.error('删除对话失败:', error)
      throw error
    }
  }

  // 刷新对话列表
  const refreshConversations = async () => {
    await loadConversations()
  }

  // 清空状态
  const clear = () => {
    conversations.value = []
    currentConversation.value = null
    currentMessages.value = []
  }

  return {
    // 状态
    conversations,
    currentConversation,
    currentMessages,
    loading,
    // 计算属性
    hasConversations,
    // 方法
    loadConversations,
    loadConversation,
    createConversation,
    setCurrentConversation,
    addMessage,
    updateConversationTitle,
    deleteConversation,
    refreshConversations,
    clear
  }
})

