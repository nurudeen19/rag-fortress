import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

export function useChatHistory() {
  const router = useRouter()
  const authStore = useAuthStore()
  
  const chats = ref([])
  const activeChat = ref(null)
  const loading = ref(false)
  const error = ref(null)

  /**
   * Load all chat conversations for the current user
   */
  const loadChats = async () => {
    if (!authStore.user) return
    
    loading.value = true
    error.value = null
    
    try {
      // For now, use mock data. Replace with actual API call
      // const response = await api.get('/v1/chats', { params: { limit: 100, offset: 0 } })
      // chats.value = response.data?.items || []
      
      // Mock data for demonstration
      chats.value = [
        {
          id: '1',
          title: 'Document Analysis - Q1 Report',
          category: 'analysis',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 12,
          last_message: 'What are the key metrics?'
        },
        {
          id: '2',
          title: 'Policy Research Discussion',
          category: 'research',
          created_at: new Date(Date.now() - 3600000).toISOString(),
          updated_at: new Date(Date.now() - 3600000).toISOString(),
          message_count: 8,
          last_message: 'Compare the two policy approaches'
        },
        {
          id: '3',
          title: 'Help with System Integration',
          category: 'support',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          updated_at: new Date(Date.now() - 86400000).toISOString(),
          message_count: 5,
          last_message: 'How to configure the API?'
        }
      ]
    } catch (err) {
      error.value = err.message || 'Failed to load chats'
      console.error('Error loading chats:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new chat conversation
   */
  const createNewChat = async (title = null, category = 'general') => {
    loading.value = true
    error.value = null
    
    try {
      // Generate a default title if not provided
      const chatTitle = title || `Conversation ${new Date().toLocaleTimeString()}`
      
      // For now, mock implementation
      // const response = await api.post('/v1/chats', {
      //   title: chatTitle,
      //   category: category
      // })
      
      const newChat = {
        id: Date.now().toString(),
        title: chatTitle,
        category: category,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0,
        last_message: ''
      }
      
      chats.value.unshift(newChat)
      activeChat.value = newChat
      
      // Navigate to the chat
      await router.push({ name: 'chat', params: { id: newChat.id } })
    } catch (err) {
      error.value = err.message || 'Failed to create chat'
      console.error('Error creating chat:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Select an existing chat conversation
   */
  const selectChat = async (chat) => {
    activeChat.value = chat
    await router.push({ name: 'chat', params: { id: chat.id } })
  }

  /**
   * Delete a chat conversation
   */
  const deleteChat = async (chatId) => {
    try {
      // const response = await api.delete(`/v1/chats/${chatId}`)
      chats.value = chats.value.filter(c => c.id !== chatId)
      
      if (activeChat.value?.id === chatId) {
        activeChat.value = null
        await router.push('/chat')
      }
    } catch (err) {
      error.value = err.message || 'Failed to delete chat'
      console.error('Error deleting chat:', err)
    }
  }

  /**
   * Rename a chat conversation
   */
  const renameChat = async (chatId, newTitle) => {
    try {
      // const response = await api.patch(`/v1/chats/${chatId}`, { title: newTitle })
      
      const chat = chats.value.find(c => c.id === chatId)
      if (chat) {
        chat.title = newTitle
      }
      if (activeChat.value?.id === chatId) {
        activeChat.value.title = newTitle
      }
    } catch (err) {
      error.value = err.message || 'Failed to rename chat'
      console.error('Error renaming chat:', err)
    }
  }

  /**
   * Update chat category
   */
  const updateChatCategory = async (chatId, category) => {
    try {
      // const response = await api.patch(`/v1/chats/${chatId}`, { category })
      
      const chat = chats.value.find(c => c.id === chatId)
      if (chat) {
        chat.category = category
      }
      if (activeChat.value?.id === chatId) {
        activeChat.value.category = category
      }
    } catch (err) {
      error.value = err.message || 'Failed to update category'
      console.error('Error updating category:', err)
    }
  }

  /**
   * Load messages for a specific chat
   */
  const loadChatMessages = async (chatId) => {
    try {
      // const response = await api.get(`/v1/chats/${chatId}/messages`, {
      //   params: { limit: 50, offset: 0 }
      // })
      // return response.data?.items || []
      
      // Mock implementation
      return []
    } catch (err) {
      console.error('Error loading messages:', err)
      return []
    }
  }

  /**
   * Save a message to a chat
   */
  const saveMessage = async (chatId, message, role = 'user') => {
    try {
      // const response = await api.post(`/v1/chats/${chatId}/messages`, {
      //   content: message,
      //   role: role
      // })
      // return response.data
      
      // Mock implementation
      return {
        id: Date.now().toString(),
        content: message,
        role: role,
        created_at: new Date().toISOString()
      }
    } catch (err) {
      console.error('Error saving message:', err)
      throw err
    }
  }

  /**
   * Get chat statistics
   */
  const getChatStats = computed(() => ({
    total: chats.value.length,
    byCategory: {
      general: chats.value.filter(c => c.category === 'general').length,
      research: chats.value.filter(c => c.category === 'research').length,
      support: chats.value.filter(c => c.category === 'support').length,
      analysis: chats.value.filter(c => c.category === 'analysis').length,
    },
    totalMessages: chats.value.reduce((sum, c) => sum + (c.message_count || 0), 0),
    averageMessages: chats.value.length > 0 
      ? Math.round(chats.value.reduce((sum, c) => sum + (c.message_count || 0), 0) / chats.value.length)
      : 0
  }))

  return {
    // State
    chats,
    activeChat,
    loading,
    error,
    
    // Methods
    loadChats,
    createNewChat,
    selectChat,
    deleteChat,
    renameChat,
    updateChatCategory,
    loadChatMessages,
    saveMessage,
    
    // Computed
    getChatStats
  }
}
