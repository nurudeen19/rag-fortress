import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const CACHE_KEY = 'fortress_conversations_cache'
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

export function useChatHistory() {
  const router = useRouter()
  const authStore = useAuthStore()
  
  const chats = ref([])
  const activeChat = ref(null)
  const loading = ref(false)
  const error = ref(null)

  /**
   * Get cache from local storage
   */
  const getCache = () => {
    try {
      const cached = localStorage.getItem(CACHE_KEY)
      if (!cached) return null
      
      const { data, timestamp } = JSON.parse(cached)
      const now = Date.now()
      
      // Check if cache has expired
      if (now - timestamp > CACHE_TTL) {
        localStorage.removeItem(CACHE_KEY)
        return null
      }
      
      return data
    } catch (err) {
      console.error('Error reading cache:', err)
      return null
    }
  }

  /**
   * Set cache in local storage
   */
  const setCache = (data) => {
    try {
      const cacheData = {
        data,
        timestamp: Date.now()
      }
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
    } catch (err) {
      console.error('Error writing cache:', err)
    }
  }

  /**
   * Clear cache from local storage
   */
  const clearCache = () => {
    try {
      localStorage.removeItem(CACHE_KEY)
    } catch (err) {
      console.error('Error clearing cache:', err)
    }
  }

  /**
   * Load all chat conversations for the current user
   * Uses local storage cache to reduce API calls
   */
  const loadChats = async (forceRefresh = false) => {
    if (!authStore.user) return
    
    // Try to use cache if not forcing refresh
    if (!forceRefresh) {
      const cached = getCache()
      if (cached) {
        chats.value = cached
        return
      }
    }
    
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/v1/conversations', { 
        params: { limit: 100, offset: 0 } 
      })
      
      chats.value = response.conversations || []
      setCache(chats.value)
    } catch (err) {
      error.value = err.message || 'Failed to load conversations'
      console.error('Error loading conversations:', err)
      // Fall back to cache even if error
      const cached = getCache()
      if (cached) {
        chats.value = cached
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new chat conversation
   */
  const createNewChat = async (title = null) => {
    loading.value = true
    error.value = null
    
    try {
      // Generate a default title if not provided
      const chatTitle = title || `Conversation ${new Date().toLocaleTimeString()}`
      
      const response = await api.post('/v1/conversations', {
        title: chatTitle
      })
      
      const newChat = response.conversation
      chats.value.unshift(newChat)
      activeChat.value = newChat
      
      // Update cache
      setCache(chats.value)
      
      // Navigate to the chat
      await router.push({ name: 'chat', params: { id: newChat.id } })
    } catch (err) {
      error.value = err.message || 'Failed to create conversation'
      console.error('Error creating conversation:', err)
      throw err
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
      await api.delete(`/v1/conversations/${chatId}`)
      chats.value = chats.value.filter(c => c.id !== chatId)
      
      // Update cache
      setCache(chats.value)
      
      if (activeChat.value?.id === chatId) {
        activeChat.value = null
        await router.push('/chat')
      }
    } catch (err) {
      error.value = err.message || 'Failed to delete conversation'
      console.error('Error deleting conversation:', err)
      throw err
    }
  }

  /**
   * Rename a chat conversation
   */
  const renameChat = async (chatId, newTitle) => {
    try {
      const response = await api.patch(`/v1/conversations/${chatId}`, { 
        title: newTitle 
      })
      
      const updatedChat = response.conversation
      const index = chats.value.findIndex(c => c.id === chatId)
      if (index !== -1) {
        chats.value[index] = updatedChat
      }
      
      if (activeChat.value?.id === chatId) {
        activeChat.value = updatedChat
      }
      
      // Update cache
      setCache(chats.value)
    } catch (err) {
      error.value = err.message || 'Failed to rename conversation'
      console.error('Error renaming conversation:', err)
      throw err
    }
  }

  /**
   * Load messages for a specific chat
   */
  const loadChatMessages = async (chatId, limit = 50, offset = 0) => {
    try {
      const response = await api.get(`/v1/conversations/${chatId}/messages`, {
        params: { limit, offset }
      })
      return response.messages || []
    } catch (err) {
      console.error('Error loading messages:', err)
      return []
    }
  }

  /**
   * Add a message to a chat
   */
  const addMessage = async (chatId, content, role = 'USER', meta = null) => {
    try {
      const response = await api.post(`/v1/conversations/${chatId}/messages`, {
        role,
        content,
        meta
      })
      return response.message
    } catch (err) {
      console.error('Error adding message:', err)
      throw err
    }
  }

  /**
   * Get conversation context for LLM (last N messages)
   */
  const getConversationContext = async (chatId, lastN = 6) => {
    try {
      const response = await api.get(`/v1/conversations/${chatId}/context`, {
        params: { last_n: lastN }
      })
      return response.context || []
    } catch (err) {
      console.error('Error getting conversation context:', err)
      return []
    }
  }

  /**
   * Get chat statistics
   */
  const getChatStats = computed(() => ({
    total: chats.value.length,
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
    loadChatMessages,
    addMessage,
    getConversationContext,
    clearCache,
    
    // Computed
    getChatStats
  }
}
