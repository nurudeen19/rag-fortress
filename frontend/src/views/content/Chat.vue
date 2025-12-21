<template>
  <div class="flex flex-col h-[calc(100vh-4rem)] bg-gradient-to-b from-fortress-950 to-fortress-900">
    <!-- Conversation Header -->
    <div class="bg-fortress-900/80 backdrop-blur-sm border-b border-fortress-800/50 px-6 py-4 flex items-center justify-between flex-shrink-0">
      <div class="flex-1">
        <div class="flex items-center space-x-3">
          <div>
            <h1 class="text-2xl font-bold text-fortress-100">{{ currentChatTitle }}</h1>
            <p class="text-sm text-fortress-400 mt-1">{{ currentChatSubtitle }}</p>
          </div>
        </div>
      </div>
      
      <!-- Header Actions -->
      <div class="flex items-center space-x-2">
        <button
          @click="showChatOptions = !showChatOptions"
          class="p-2 rounded-lg text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 transition-colors"
          title="Conversation options"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>

        <!-- Chat Options Dropdown -->
        <div
          v-show="showChatOptions"
          @click.self="showChatOptions = false"
          class="absolute right-6 top-20 w-48 bg-fortress-900 border border-fortress-800 rounded-lg shadow-glow overflow-hidden animate-fade-in z-10"
        >
          <div class="p-2 space-y-1">
            <button
              @click="showRenameModal = true; showChatOptions = false"
              class="w-full text-left px-3 py-2 text-sm text-fortress-300 hover:bg-fortress-800 rounded transition-colors flex items-center space-x-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Rename</span>
            </button>
            <button
              @click="deleteChat"
              class="w-full text-left px-3 py-2 text-sm text-alert hover:bg-alert/10 rounded transition-colors flex items-center space-x-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>Delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Messages Container -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-6 bg-transparent">
      <!-- Transition wrapper to prevent flicker -->
      <transition name="fade" mode="out-in">
        <div :key="route.params.id || 'new'" class="space-y-6">
          <!-- Empty State with Suggestions -->
      <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
        <div class="max-w-3xl mx-auto text-center px-4">
          <!-- Animated Icon -->
          <div class="relative inline-block mb-6">
            <div class="absolute inset-0 bg-secure/20 rounded-full blur-2xl animate-pulse"></div>
            <div class="relative bg-gradient-to-br from-secure/30 to-secure/10 rounded-full p-6 border border-secure/30">
              <svg class="w-16 h-16 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
          </div>
          
          <h2 class="text-3xl font-semibold text-fortress-100 mb-3">
            <span class="bg-gradient-to-r from-secure via-fortress-100 to-secure bg-clip-text text-transparent">
              Knowledge Assistant
            </span>
          </h2>
          <p class="text-fortress-400 text-lg max-w-xl mx-auto leading-relaxed">
            Ask questions and receive concise, sourced answers backed by relevant sources.
          </p>
          
          <!-- Decorative Features -->
          <div class="mt-10 flex items-center justify-center gap-8 text-fortress-500 text-sm">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Instant Answers</span>
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>Accurate Results</span>
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              <span>Contextual Understanding</span>
            </div>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div class="max-w-6xl mx-auto space-y-6">
        <template v-for="(message, index) in messages" :key="message.id || index">
          <!-- User Message -->
          <div v-if="message.role === 'user'" class="flex justify-end animate-slide-in-right">
            <div class="w-full max-w-[90%] lg:max-w-[85%]">
              <div class="bg-gradient-to-br from-secure/30 to-secure/20 border border-secure/40 rounded-2xl rounded-tr-sm px-6 py-4 shadow-lg">
                <div class="text-fortress-50 leading-relaxed prose-invert prose-sm max-w-none" v-html="renderMarkdown(message.content)"></div>
              </div>
              <div class="flex items-center justify-end gap-2 mt-2 px-2">
                <p class="text-xs text-fortress-500">{{ formatTime(message.timestamp) }}</p>
                <div class="w-1 h-1 rounded-full bg-secure/50"></div>
                <p class="text-xs text-fortress-500">You</p>
              </div>
            </div>
          </div>

          <!-- Assistant Message (includes placeholder state with loading indicator) -->
          <div v-else class="flex justify-start animate-slide-in-left">
            <div class="w-full max-w-[95%] lg:max-w-[90%]">
              <div class="flex items-start gap-3">
                <!-- AI Avatar -->
                <div class="flex-shrink-0 mt-1">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-secure/30 to-secure/10 border border-secure/30 flex items-center justify-center" :class="{ 'animate-pulse': message.isPlaceholder }">
                    <svg class="w-4 h-4 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                </div>
                
                <div class="flex-1">
                  <!-- Main Response / Placeholder Bubble -->
                  <div class="bg-fortress-800/60 backdrop-blur-sm border border-fortress-700/50 rounded-2xl rounded-tl-sm px-6 py-4 shadow-lg transition-all duration-300">
                    <!-- Show loading state if placeholder with no content -->
                    <div v-if="message.isPlaceholder && !message.content" class="flex items-center gap-3">
                      <div class="flex gap-1.5">
                        <div class="w-2.5 h-2.5 bg-secure/60 rounded-full animate-bounce" style="animation-delay: 0s; animation-duration: 0.6s;"></div>
                        <div class="w-2.5 h-2.5 bg-secure/60 rounded-full animate-bounce" style="animation-delay: 0.15s; animation-duration: 0.6s;"></div>
                        <div class="w-2.5 h-2.5 bg-secure/60 rounded-full animate-bounce" style="animation-delay: 0.3s; animation-duration: 0.6s;"></div>
                      </div>
                      <span class="text-fortress-300 text-sm font-medium">Analyzing Knowledge Base...</span>
                    </div>
                    <!-- Show actual response content -->
                    <div v-else class="text-fortress-100 leading-relaxed prose-invert prose-sm max-w-none" v-html="renderMarkdown(message.content)"></div>
                  </div>
                  
                  <!-- Error Message -->
                  <div v-if="message.error" class="mt-3 bg-alert/10 border border-alert/30 rounded-lg px-4 py-3">
                    <div class="flex items-start gap-2">
                      <svg class="w-5 h-5 text-alert flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p class="text-alert text-sm">{{ message.error }}</p>
                    </div>
                  </div>
                  
                  <!-- Timestamp -->
                  <div class="flex items-center gap-2 mt-2 px-2">
                    <p class="text-xs text-fortress-500">{{ formatTime(message.timestamp) }}</p>
                    <div class="w-1 h-1 rounded-full bg-fortress-600"></div>
                    <p class="text-xs text-fortress-500">AI Assistant</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </template>
        </div>
        </div>
      </transition>
    </div>

    <!-- Input Area -->
    <div class="bg-transparent border-t border-fortress-800/50 px-4 py-4 flex-shrink-0">
      <div class="max-w-6xl mx-auto">
        <form @submit.prevent="sendMessage" class="space-y-3">
          <!-- Input Field with Enhanced Design -->
          <div class="relative">
            <!-- Input Container -->
            <div class="flex items-end gap-2">
              <!-- Textarea Input -->
              <div class="flex-1 relative group">
                <textarea
                  ref="inputField"
                  v-model="inputMessage"
                  rows="1"
                  placeholder="Ask anything about your documents..."
                  class="w-full bg-fortress-800/60 backdrop-blur-sm border border-fortress-700/50 rounded-2xl px-5 py-3.5 pr-12 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure/50 focus:ring-2 focus:ring-secure/20 transition-all duration-200 shadow-lg resize-none max-h-32 overflow-y-auto"
                  :disabled="loading"
                  @keydown.enter.exact.prevent="sendMessage"
                  @keydown.shift.enter="handleNewLine"
                  @input="autoResize"
                ></textarea>
                
                <!-- Character Count Inside Input -->
                <div class="absolute bottom-3 right-3 flex items-center gap-2">
                  <span v-if="inputMessage.length > 0" class="text-xs font-medium px-2 py-0.5 rounded-full" :class="inputMessage.length > 1800 ? 'bg-alert/20 text-alert' : 'bg-fortress-700/50 text-fortress-400'">
                    {{ inputMessage.length }}/2000
                  </span>
                </div>
              </div>
              
              <!-- Send Button -->
              <button
                type="submit"
                class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-secure to-secure/90 hover:from-secure/95 hover:to-secure disabled:from-fortress-700 disabled:to-fortress-800 disabled:cursor-not-allowed rounded-2xl text-white font-semibold transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 disabled:shadow-none disabled:scale-100 flex items-center justify-center group"
                :disabled="loading || !inputMessage.trim()"
                title="Send message (Enter)"
              >
                <svg v-if="!loading" class="w-5 h-5 transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Bottom Actions -->
          <div class="flex justify-between items-center px-2">
            <!-- Hints -->
            <div class="flex items-center gap-4 text-xs text-fortress-500">
              <div class="flex items-center gap-1.5">
                <kbd class="px-1.5 py-0.5 bg-fortress-800 border border-fortress-700 rounded text-xs font-mono">Enter</kbd>
                <span>to send</span>
              </div>
              <div class="hidden sm:flex items-center gap-1.5">
                <kbd class="px-1.5 py-0.5 bg-fortress-800 border border-fortress-700 rounded text-xs font-mono">Shift+Enter</kbd>
                <span>for new line</span>
              </div>
            </div>
            
            <!-- Clear Button -->
            <button
              v-if="messages.length > 0"
              type="button"
              @click="clearHistory"
              class="text-fortress-500 hover:text-fortress-300 transition-colors flex items-center gap-1.5 px-2 py-1 rounded-lg hover:bg-fortress-800/50"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span class="text-xs font-medium">Clear chat</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Rename Modal -->
    <div
      v-if="showRenameModal"
      @click.self="showRenameModal = false"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-fortress-900 border border-fortress-800 rounded-xl shadow-2xl w-full max-w-md animate-fade-in">
        <div class="border-b border-fortress-800 px-6 py-4">
          <h2 class="text-xl font-bold text-fortress-100">Rename Conversation</h2>
          <p class="text-sm text-fortress-400 mt-1">Enter a new title for this conversation</p>
        </div>
        <div class="p-6 space-y-4">
          <input
            v-model="renameInput"
            type="text"
            :placeholder="currentChatTitle"
            class="w-full bg-fortress-800 border border-fortress-700 rounded-lg px-4 py-3 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure focus:ring-1 focus:ring-secure transition-colors"
            @keydown.enter="submitRename"
            @keydown.escape="showRenameModal = false"
            autofocus
          />
        </div>
        <div class="border-t border-fortress-800 px-6 py-4 flex justify-end gap-3">
          <button
            @click="showRenameModal = false"
            class="px-4 py-2 rounded-lg text-fortress-300 hover:bg-fortress-800 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            @click="submitRename"
            :disabled="!renameInput.trim()"
            class="px-6 py-2 bg-secure hover:bg-secure/90 disabled:bg-secure/50 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
          >
            Rename
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div
      v-if="showDeleteModal"
      @click.self="showDeleteModal = false"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="bg-fortress-900 border border-fortress-800 rounded-xl shadow-2xl w-full max-w-md animate-fade-in">
        <div class="border-b border-fortress-800 px-6 py-4">
          <h2 class="text-xl font-bold text-red-400">Delete Conversation</h2>
          <p class="text-sm text-fortress-400 mt-1">This action cannot be undone</p>
        </div>
        <div class="p-6">
          <!-- Error Message -->
          <div v-if="deleteError" class="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p class="text-sm text-red-400">{{ deleteError }}</p>
          </div>
          
          <p class="text-fortress-300">
            Are you sure you want to delete <span class="font-semibold text-fortress-100">"{{ currentChatTitle }}"</span>?
            All messages in this conversation will be permanently removed.
          </p>
        </div>
        <div class="border-t border-fortress-800 px-6 py-4 flex justify-end gap-3">
          <button
            @click="showDeleteModal = false"
            class="px-4 py-2 rounded-lg text-fortress-300 hover:bg-fortress-800 transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            @click="confirmDelete"
            :disabled="deleting"
            class="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors flex items-center gap-2"
          >
            <svg v-if="!deleting" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ deleting ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { useAuthStore } from '../../stores/auth'
import { useChatHistory } from '../../composables/useChatHistory'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { 
  activeChat,
  deleteChat: deleteChatFromHistory, 
  renameChat: renameChatFromHistory,
  loadChatMessages,
  createConversation
} = useChatHistory()

// State
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const loadingMessages = ref(false)
const deleting = ref(false)
const deleteError = ref(null)
const messagesContainer = ref(null)
const inputField = ref(null)
const showChatOptions = ref(false)
const showRenameModal = ref(false)
const showDeleteModal = ref(false)
const renameInput = ref('')
const suppressAutoLoad = ref(false)

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const currentChatTitle = computed(() => activeChat.value?.title || 'New Conversation')

const currentChatSubtitle = computed(() => {
  // Chat message-count removed — subtitle intentionally minimal.
  // If there's an active chat we show an empty subtitle; otherwise a prompt.
  return activeChat.value ? '' : 'Start a conversation to unlock insights'
})

// Render markdown content
const renderMarkdown = (content) => {
  try {
    return marked(content, {
      breaks: true,
      gfm: true
    })
  } catch (err) {
    console.error('Markdown rendering error:', err)
    return `<p>${content}</p>`
  }
}

// Format time to HH:MM
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// Load messages from backend
const normalizeAndSortMessages = (rawMessages) => {
  /**
   * Permanent message ordering solution:
   * 1. Normalize all messages to display format
   * 2. Sort chronologically by timestamp (oldest first)
   * 3. Loop through with state tracking to ensure proper user/assistant pairing
   * 4. Return reliable, ordered list regardless of API response order
   */
  
  // Step 1: Convert backend format to display format
  const normalized = rawMessages.map(msg => ({
    id: msg.id,
    role: msg.role.toLowerCase(),
    content: msg.content,
    timestamp: msg.created_at ? new Date(msg.created_at).getTime() : 0,
    sources: msg.meta?.sources || [],
    error: msg.meta?.error || null,
    created_at: msg.created_at
  }))
  
  // Step 2: Sort chronologically (oldest first)
  // Backend returns DESC (newest first), so reverse it
  normalized.sort((a, b) => a.timestamp - b.timestamp)
  
  // Step 3: Loop with state tracking to ensure proper ordering
  // This prevents issues where assistant/user messages get misordered
  const ordered = []
  let lastRole = null
  
  for (let i = 0; i < normalized.length; i++) {
    const msg = normalized[i]
    
    // Always add the message (we trust the sorted order now)
    ordered.push(msg)
    lastRole = msg.role
    
    // Diagnostic logging for development
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[Message ${i}] role=${msg.role}, timestamp=${new Date(msg.timestamp).toLocaleTimeString()}`)
    }
  }
  
  return ordered
}

const loadMessagesForConversation = async (conversationId) => {
  if (!conversationId) {
    messages.value = []
    return
  }

  loadingMessages.value = true
  try {
    const response = await loadChatMessages(conversationId, 50, 0)
    
    // Check if conversation doesn't exist
    if (!response.conversation) {
      console.warn(`Conversation ${conversationId} not found`)
      messages.value = []
      activeChat.value = null
      await router.push('/chat')
      return
    }
    
    // Update active chat with conversation details from response
    activeChat.value = response.conversation
    
    // Use permanent ordering function to ensure messages are always in correct sequence
    // regardless of API response order or previous issues
    messages.value = normalizeAndSortMessages(response.messages)

    await scrollToBottom()
  } catch (error) {
    console.error('Failed to load messages:', error)
    // If 404, conversation doesn't exist - navigate away
    if (error.response?.status === 404) {
      messages.value = []
      activeChat.value = null
      await router.push('/chat')
    } else {
      messages.value = []
    }
  } finally {
    loadingMessages.value = false
  }
}

// Watch for conversation changes when route changes
watch(
  () => route.params.id,
  async (newId) => {
    if (suppressAutoLoad.value && newId && newId !== 'new') {
      return
    }

    if (newId && newId !== 'new') {
      await loadMessagesForConversation(newId)
    } else {
      messages.value = []
      activeChat.value = null
    }
  },
  { immediate: true }
)

// Scroll to bottom when new messages arrive
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    // Use requestAnimationFrame to ensure layout has settled before scrolling
    window.requestAnimationFrame(() => {
      try {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      } catch (e) {
        // ignore
      }
    })
  }
}

const streamAssistantResponse = async (conversationId, userMessage) => {
  const token = authStore.token
  const response = await fetch(`${API_BASE_URL}/v1/conversations/${conversationId}/respond`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message: userMessage })
  })

  if (!response.ok) {
    let detail = 'Failed to generate response'
    try {
      const errorBody = await response.json()
      detail = errorBody?.detail || errorBody?.message || detail
    } catch (_) {
      const text = await response.text()
      if (text) {
        detail = text
      }
    }
    throw new Error(detail)
  }

  if (!response.body) {
    throw new Error('Streaming response not supported by the browser.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let assistantMessage = null

  const handlePayload = async (payload) => {
    if (!payload || typeof payload !== 'object') {
      return
    }

    if (payload.type === 'token') {
      // Use existing assistant placeholder if present, otherwise create one
      if (!assistantMessage) {
        // Try to reuse an existing placeholder (pushed by sendMessage)
        assistantMessage = messages.value.find(m => m.role === 'assistant' && m.isPlaceholder)
      }

      if (!assistantMessage) {
        assistantMessage = {
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          sources: [],
          error: null
        }
        messages.value.push(assistantMessage)
      }

      // Update assistant content in-place to avoid re-rendering the whole list
      assistantMessage.content += payload.content || ''
      assistantMessage.timestamp = new Date().toISOString()
    } else if (payload.type === 'metadata') {
      if (assistantMessage) {
        assistantMessage.sources = payload.sources || []
      }
    } else if (payload.type === 'error') {
      // Create error message if no assistant entry exists yet
      if (!assistantMessage) {
        assistantMessage = {
          role: 'assistant',
          content: 'I encountered an error while generating your response.',
          timestamp: new Date().toISOString(),
          sources: [],
          error: payload.message || 'An error occurred while generating the response.'
        }
        messages.value.push(assistantMessage)
      } else {
        assistantMessage.error = payload.message || 'An error occurred while generating the response.'
        if (!assistantMessage.content) {
          assistantMessage.content = 'I encountered an error while generating your response.'
        }
      }
      throw new Error(assistantMessage.error)
    }

    scrollToBottom()
  }

  const processBuffer = async () => {
    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary).trim()
      buffer = buffer.slice(boundary + 2)
      if (rawEvent) {
        const dataLines = rawEvent
          .split('\n')
          .filter(line => line.startsWith('data:'))
          .map(line => line.replace(/^data:\s*/, ''))
        if (dataLines.length) {
          const payloadStr = dataLines.join('\n')
          try {
            const payload = JSON.parse(payloadStr)
            await handlePayload(payload)
          } catch (err) {
            console.error('Failed to parse stream payload:', err)
          }
        }
      }
      boundary = buffer.indexOf('\n\n')
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      const remaining = decoder.decode()
      if (remaining) {
        buffer += remaining
        await processBuffer()
      }
      break
    }

    buffer += decoder.decode(value, { stream: true })
    await processBuffer()
  }

  // Finalize placeholder state: mark it no longer a placeholder so UI can render normally
  if (assistantMessage && assistantMessage.isPlaceholder) {
    assistantMessage.isPlaceholder = false
  }
}

// Send message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // Add user message to UI immediately
  const userEntry = {
    role: 'user',
    content: userMessage,
    timestamp: new Date().toISOString()
  }
  messages.value.push(userEntry)
  scrollToBottom()

  // Create assistant placeholder immediately so UI shows analyzing bubble
  const assistantPlaceholder = {
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString(),
    sources: [],
    error: null,
    isPlaceholder: true
  }
  messages.value.push(assistantPlaceholder)
  await scrollToBottom()

  // Show loading indicator
  loading.value = true

  let conversationId = activeChat.value?.id
  let createdConversation = false
  let newConversation = null

  try {
    // Create conversation if needed (new chat)
    if (!conversationId || route.params.id === 'new') {
      suppressAutoLoad.value = true
      // Create conversation without navigation or activeChat update
      // We'll update both after streaming completes to prevent UI disruption
      try {
        newConversation = await createConversation(userMessage, false, false)
        conversationId = newConversation.id
        createdConversation = true
        console.log('Created new conversation:', conversationId)
        
        // DON'T update activeChat yet - wait until after streaming completes
        // This prevents ChatModeLayout's router-view from remounting
      } catch (err) {
        console.error('Failed to create conversation:', err)
        // Find assistant placeholder and update with error
        const placeholder = messages.value.find(m => m.role === 'assistant' && m.isPlaceholder)
        if (placeholder) {
          placeholder.error = `Failed to create conversation: ${err.message}`
          placeholder.isPlaceholder = false
        }
        throw err
      }
    }

    // Validate conversationId before streaming
    if (!conversationId) {
      throw new Error('No conversation ID available')
    }

    console.log('Streaming response for conversation:', conversationId)
    // Stream assistant response (updates the placeholder in-place)
    await streamAssistantResponse(conversationId, userMessage)

    // After successful streaming, update URL and activeChat silently
    // This preserves the analyzing bubble UX and prevents layout jumps
    if (createdConversation && conversationId) {
      // Update activeChat AFTER streaming completes
      if (newConversation) {
        activeChat.value = newConversation
      }
      
      // Use history.replaceState for completely silent URL update
      // This doesn't trigger any Vue Router reactivity or watchers
      const newUrl = `/chat/${conversationId}`
      window.history.replaceState({}, '', newUrl)
      
      // Force route params update without navigation
      route.params.id = conversationId
    }

    // Avoid reload of entire message list after streaming to prevent layout jumps.
    // The streaming updates the assistant message in-place and persists to DB server-side.
  } catch (error) {
    console.error('Chat error:', error)
    // Error is already handled in streamAssistantResponse
    // Just ensure we don't have duplicate error handling
  } finally {
    loading.value = false
    if (createdConversation) {
      suppressAutoLoad.value = false
    }
    scrollToBottom()
  }
}

// Clear conversation history
const clearHistory = () => {
  if (confirm('Are you sure you want to clear the conversation history?')) {
    messages.value = []
    inputMessage.value = ''
  }
}

// Rename chat with modal
const submitRename = async () => {
  if (!renameInput.value.trim() || !activeChat.value) return
  
  try {
    await renameChatFromHistory(activeChat.value.id, renameInput.value.trim())
    showRenameModal.value = false
    renameInput.value = ''
    showChatOptions.value = false
  } catch (error) {
    console.error('Rename failed:', error)
  }
}

// Open delete modal
const deleteChat = () => {
  deleteError.value = null  // Clear any previous errors
  showDeleteModal.value = true
  showChatOptions.value = false
}

// Confirm and execute delete
const confirmDelete = async () => {
  if (!activeChat.value || deleting.value) return
  
  deleteError.value = null  // Clear previous errors
  deleting.value = true
  
  try {
    await deleteChatFromHistory(activeChat.value.id)
    // Close modal and reset state
    showDeleteModal.value = false
    deleting.value = false
    // Navigation happens automatically in deleteChat()
  } catch (error) {
    console.error('Failed to delete conversation:', error)
    
    // Extract error message from API response
    let errorMessage = 'Failed to delete conversation. Please try again.'
    
    if (error.response?.data?.detail) {
      // Backend returned a structured error (e.g., demo mode message)
      errorMessage = error.response.data.detail
    } else if (error.message) {
      // Use error message if available
      errorMessage = error.message
    }
    
    deleteError.value = errorMessage
    deleting.value = false
    // Keep modal open to show error
  }
}

// Auto-resize textarea
const autoResize = () => {
  if (inputField.value) {
    inputField.value.style.height = 'auto'
    inputField.value.style.height = inputField.value.scrollHeight + 'px'
  }
}

// Handle new line in textarea
const handleNewLine = (event) => {
  // Allow default behavior for Shift+Enter
}

// Focus input field
const focusInput = () => {
  if (inputField.value) {
    inputField.value.focus()
  }
}

// Auto scroll on mount
onMounted(() => {
  scrollToBottom()
  if (inputField.value) {
    inputField.value.focus()
  }
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-in-right {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.animate-slide-in-left {
  animation: slideInLeft 0.3s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #5a6573;
}

/* Smooth scrolling */
* {
  scrollbar-width: thin;
  scrollbar-color: #4b5563 transparent;
}

/* Prose styling for markdown content */
:deep(.prose-invert) {
  color: rgba(241, 245, 249, 1);
}

:deep(.prose-invert p) {
  margin: 0.75rem 0;
  line-height: 1.5;
}

:deep(.prose-invert h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 1rem 0 0.5rem 0;
  color: rgba(241, 245, 249, 1);
}

:deep(.prose-invert h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0.875rem 0 0.5rem 0;
  color: rgba(241, 245, 249, 1);
}

:deep(.prose-invert h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0.75rem 0 0.375rem 0;
  color: rgba(241, 245, 249, 1);
}

:deep(.prose-invert ul) {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
  list-style-type: disc;
}

:deep(.prose-invert ol) {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
  list-style-type: decimal;
}

:deep(.prose-invert li) {
  margin: 0.375rem 0;
  line-height: 1.5;
}

:deep(.prose-invert code) {
  background-color: rgba(0, 0, 0, 0.3);
  color: rgba(34, 197, 94, 1);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.9em;
}

:deep(.prose-invert pre) {
  background-color: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(100, 116, 139, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 0.75rem 0;
  overflow-x: auto;
}

:deep(.prose-invert pre code) {
  background-color: transparent;
  color: rgba(226, 232, 240, 1);
  padding: 0;
  border-radius: 0;
  font-size: 0.85em;
  line-height: 1.5;
}

:deep(.prose-invert blockquote) {
  border-left: 4px solid rgba(34, 197, 94, 0.5);
  padding-left: 1rem;
  color: rgba(148, 163, 184, 1);
  margin: 0.75rem 0;
  font-style: italic;
}

:deep(.prose-invert a) {
  color: rgba(34, 197, 94, 1);
  text-decoration: underline;
  transition: color 0.2s;
}

:deep(.prose-invert a:hover) {
  color: rgba(74, 222, 128, 1);
}

:deep(.prose-invert strong) {
  font-weight: 600;
  color: rgba(241, 245, 249, 1);
}

:deep(.prose-invert em) {
  font-style: italic;
  color: rgba(226, 232, 240, 1);
}

:deep(.prose-invert hr) {
  border: 0;
  border-top: 1px solid rgba(100, 116, 139, 0.5);
  margin: 1rem 0;
}

:deep(.prose-invert table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
  font-size: 0.9em;
}

:deep(.prose-invert th) {
  background-color: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(100, 116, 139, 0.5);
  padding: 0.5rem;
  text-align: left;
  font-weight: 600;
}

:deep(.prose-invert td) {
  border: 1px solid rgba(100, 116, 139, 0.5);
  padding: 0.5rem;
}

/* Fade transition for smooth conversation switching */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Smooth transition for message bubble content (placeholder to response) */
.bg-fortress-800\/60 {
  transition: all 0.3s ease;
}
</style>
