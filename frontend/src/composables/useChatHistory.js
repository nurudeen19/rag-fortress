import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const CACHE_KEY = 'fortress_conversations_cache'
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

// Singleton state - shared across all components
const chats = ref([])
const activeChat = ref(null)
const loading = ref(false)
const error = ref(null)

export function useChatHistory() {
  const router = useRouter()
  const authStore = useAuthStore()

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
   * Open new chat window (doesn't create conversation yet)
   */
  const openNewChat = async () => {
    activeChat.value = null
    await router.push('/chat/new')
  }

  /**
   * Create a new chat conversation without navigation.
   * The caller is responsible for handling navigation or URL updates.
   * This allows streaming to complete before any route changes.
   * 
   * @param {string} firstMessage - The first message to use for generating the title
   * @param {boolean} navigate - Whether to navigate to the new conversation (default: false)
   * @param {boolean} updateActiveChat - Whether to update activeChat immediately (default: true)
   * @returns {Promise<Object>} The created conversation object
   */
  const createConversation = async (firstMessage, navigate = false, updateActiveChat = true) => {
    loading.value = true
    error.value = null
    
    try {
      // Generate title from first message (first 50 chars)
      const title = firstMessage.length > 50 
        ? firstMessage.substring(0, 47) + '...' 
        : firstMessage
      
      const newChat = await api.post('/v1/conversations', {
        title: title
      })
      
      // Response is already unwrapped by axios interceptor
      chats.value.unshift(newChat)
      
      // Only update activeChat if requested (default true for backwards compatibility)
      // Caller can defer this to prevent UI remounts during streaming
      if (updateActiveChat) {
        activeChat.value = newChat
      }
      
      // Update cache
      setCache(chats.value)
      
      // Only navigate if explicitly requested
      // For streaming flows, caller should update URL after streaming completes
      if (navigate) {
        await router.push('/chat/' + newChat.id)
      }
      
      return newChat
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
    await router.push('/chat/' + chat.id)
  }

  /**
   * Delete a chat conversation
   */
  const deleteChat = async (chatId) => {
    const deletedChat = chats.value.find(c => c.id === chatId)
    
    try {
      // Optimistic deletion: Remove from local state and storage immediately
      chats.value = chats.value.filter(c => c.id !== chatId)
      setCache(chats.value)
      
      // Clear active chat if it's the one being deleted
      if (activeChat.value?.id === chatId) {
        activeChat.value = null
      }
      
      // Navigate away if we're deleting the active chat
      if (router.currentRoute.value.params.id === chatId) {
        await router.push('/chat')
      }
      
      // Send delete request to server (in background)
      await api.delete(`/v1/conversations/${chatId}`)
      
      // Success! The optimistic update was correct, no need to reload
    } catch (err) {
      error.value = err.message || 'Failed to delete conversation'
      console.error('Error deleting conversation:', err)
      
      // Rollback: Restore the deleted chat to local state if request failed
      if (deletedChat) {
        chats.value.unshift(deletedChat)
        setCache(chats.value)
      }
      
      throw err
    }
  }

  /**
   * Rename a chat conversation
   */
  const renameChat = async (chatId, newTitle) => {
    try {
      const updatedChat = await api.patch(`/v1/conversations/${chatId}`, { 
        title: newTitle 
      })
      
      // Response is already unwrapped by axios interceptor
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
   * Load messages for a specific chat conversation
   * Returns { conversation, messages, total, limit, offset }
   */
  const loadChatMessages = async (chatId, limit = 50, offset = 0) => {
    try {
      const response = await api.get(`/v1/conversations/${chatId}/messages`, {
        params: { limit, offset }
      })
      return response
    } catch (err) {
      console.error('Error loading messages:', err)
      throw err
    }
  }

  /**
   * Add a message to a chat
   */
  const addMessage = async (chatId, content, role = 'USER', meta = null) => {
    try {
      const message = await api.post(`/v1/conversations/${chatId}/messages`, {
        role,
        content,
        meta
      })
      // Response is already unwrapped by axios interceptor
      return message
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
    openNewChat,
    createConversation,
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
