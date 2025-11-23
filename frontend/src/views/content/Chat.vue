<template>
  <div class="flex flex-col h-[calc(100vh-4rem)] bg-gradient-to-b from-fortress-950 to-fortress-900">
    <!-- Conversation Header -->
    <div class="bg-fortress-900/80 backdrop-blur-sm border-b border-fortress-800/50 px-6 py-4 flex items-center justify-between flex-shrink-0">
      <div class="flex-1">
        <div class="flex items-center space-x-3">
          <div>
            <h1 class="text-2xl font-bold text-fortress-100">{{ currentChatTitle }}</h1>
            <p class="text-sm text-fortress-400 mt-1">Query your documents with AI-powered retrieval</p>
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
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-4 py-6 space-y-6 bg-transparent">
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
          
          <h2 class="text-3xl font-bold text-fortress-100 mb-3">What can I help you with?</h2>
          <p class="text-fortress-400 text-lg mb-8">Ask questions about your documents and get AI-powered answers</p>
          
          <!-- Quick Suggestions -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
            <button
              @click="inputMessage = 'What are the key points in the sales playbook?'; focusInput()"
              class="group text-left p-4 bg-fortress-800/50 hover:bg-fortress-800 border border-fortress-700/50 hover:border-secure/50 rounded-xl transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
            >
              <div class="flex items-start gap-3">
                <div class="p-2 bg-secure/10 rounded-lg group-hover:bg-secure/20 transition-colors">
                  <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-fortress-200 group-hover:text-fortress-100 transition-colors">Summarize documents</p>
                  <p class="text-sm text-fortress-500 mt-1">Get key insights from your files</p>
                </div>
              </div>
            </button>
            
            <button
              @click="inputMessage = 'Find information about our company policies'; focusInput()"
              class="group text-left p-4 bg-fortress-800/50 hover:bg-fortress-800 border border-fortress-700/50 hover:border-secure/50 rounded-xl transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
            >
              <div class="flex items-start gap-3">
                <div class="p-2 bg-secure/10 rounded-lg group-hover:bg-secure/20 transition-colors">
                  <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-fortress-200 group-hover:text-fortress-100 transition-colors">Search knowledge</p>
                  <p class="text-sm text-fortress-500 mt-1">Find specific information</p>
                </div>
              </div>
            </button>
            
            <button
              @click="inputMessage = 'Compare different approaches in the documentation'; focusInput()"
              class="group text-left p-4 bg-fortress-800/50 hover:bg-fortress-800 border border-fortress-700/50 hover:border-secure/50 rounded-xl transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
            >
              <div class="flex items-start gap-3">
                <div class="p-2 bg-secure/10 rounded-lg group-hover:bg-secure/20 transition-colors">
                  <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-fortress-200 group-hover:text-fortress-100 transition-colors">Analyze & compare</p>
                  <p class="text-sm text-fortress-500 mt-1">Deep dive into content</p>
                </div>
              </div>
            </button>
            
            <button
              @click="inputMessage = 'Explain the process described in the guidelines'; focusInput()"
              class="group text-left p-4 bg-fortress-800/50 hover:bg-fortress-800 border border-fortress-700/50 hover:border-secure/50 rounded-xl transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
            >
              <div class="flex items-start gap-3">
                <div class="p-2 bg-secure/10 rounded-lg group-hover:bg-secure/20 transition-colors">
                  <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p class="font-medium text-fortress-200 group-hover:text-fortress-100 transition-colors">Get explanations</p>
                  <p class="text-sm text-fortress-500 mt-1">Understand complex topics</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Messages -->
      <div class="max-w-4xl mx-auto space-y-6">
        <template v-for="(message, index) in messages" :key="index">
          <!-- User Message -->
          <div v-if="message.role === 'user'" class="flex justify-end animate-slide-in-right">
            <div class="max-w-[75%] lg:max-w-[65%]">
              <div class="bg-gradient-to-br from-secure/30 to-secure/20 border border-secure/40 rounded-2xl rounded-tr-sm px-5 py-3 shadow-lg">
                <p class="text-fortress-50 leading-relaxed">{{ message.content }}</p>
              </div>
              <div class="flex items-center justify-end gap-2 mt-2 px-2">
                <p class="text-xs text-fortress-500">{{ formatTime(message.timestamp) }}</p>
                <div class="w-1 h-1 rounded-full bg-secure/50"></div>
                <p class="text-xs text-fortress-500">You</p>
              </div>
            </div>
          </div>

          <!-- Assistant Message -->
          <div v-else class="flex justify-start animate-slide-in-left">
            <div class="max-w-[85%] lg:max-w-[75%]">
              <div class="flex items-start gap-3">
                <!-- AI Avatar -->
                <div class="flex-shrink-0 mt-1">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-secure/30 to-secure/10 border border-secure/30 flex items-center justify-center">
                    <svg class="w-4 h-4 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                </div>
                
                <div class="flex-1">
                  <!-- Main Response -->
                  <div class="bg-fortress-800/60 backdrop-blur-sm border border-fortress-700/50 rounded-2xl rounded-tl-sm px-5 py-4 shadow-lg">
                    <p class="text-fortress-100 leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
                  </div>
                  
                  <!-- Sources/References -->
                  <div v-if="message.sources && message.sources.length > 0" class="mt-3 ml-2">
                    <div class="flex items-center gap-2 mb-2">
                      <svg class="w-4 h-4 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p class="text-xs font-semibold text-fortress-400 uppercase tracking-wide">Sources</p>
                    </div>
                    <div class="space-y-2">
                      <div
                        v-for="(source, idx) in message.sources"
                        :key="idx"
                        class="group flex items-start gap-3 p-3 bg-fortress-800/40 hover:bg-fortress-800/60 border border-fortress-700/30 hover:border-secure/30 rounded-lg transition-all duration-200 cursor-pointer"
                      >
                        <div class="flex-shrink-0 w-6 h-6 rounded-full bg-secure/10 flex items-center justify-center border border-secure/20">
                          <span class="text-xs font-semibold text-secure">{{ idx + 1 }}</span>
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-sm text-fortress-200 group-hover:text-fortress-100 font-medium break-words transition-colors">{{ source.document }}</p>
                          <div class="flex items-center gap-2 mt-1">
                            <div class="flex-1 bg-fortress-700/30 rounded-full h-1.5 overflow-hidden">
                              <div class="bg-gradient-to-r from-secure to-secure/70 h-full rounded-full transition-all duration-300" :style="{ width: `${source.score * 100}%` }"></div>
                            </div>
                            <span class="text-xs font-medium text-secure">{{ Math.round(source.score * 100) }}%</span>
                          </div>
                        </div>
                      </div>
                    </div>
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

      <!-- Loading Indicator -->
      <div v-if="loading" class="max-w-4xl mx-auto">
        <div class="flex justify-start animate-slide-in-left">
          <div class="flex items-start gap-3">
            <!-- AI Avatar -->
            <div class="flex-shrink-0 mt-1">
              <div class="w-8 h-8 rounded-full bg-gradient-to-br from-secure/30 to-secure/10 border border-secure/30 flex items-center justify-center animate-pulse">
                <svg class="w-4 h-4 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            
            <div class="bg-fortress-800/60 backdrop-blur-sm border border-fortress-700/50 rounded-2xl rounded-tl-sm px-5 py-4 shadow-lg">
              <div class="flex items-center gap-3">
                <div class="flex gap-1.5">
                  <div class="w-2.5 h-2.5 bg-secure/60 rounded-full animate-bounce" style="animation-delay: 0s; animation-duration: 0.6s;"></div>
                  <div class="w-2.5 h-2.5 bg-secure/60 rounded-full animate-bounce" style="animation-delay: 0.15s; animation-duration: 0.6s;"></div>
                  <div class="w-2.5 h-2.5 bg-secure/60 rounded-full animate-bounce" style="animation-delay: 0.3s; animation-duration: 0.6s;"></div>
                </div>
                <span class="text-fortress-300 text-sm font-medium">Analyzing your documents...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="bg-transparent border-t border-fortress-800/50 px-4 py-4 flex-shrink-0">
      <div class="max-w-4xl mx-auto">
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
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
  addMessage
} = useChatHistory()

// State
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const inputField = ref(null)
const showChatOptions = ref(false)
const showRenameModal = ref(false)
const renameInput = ref('')
const loadingMessages = ref(false)

const currentChatTitle = computed(() => activeChat.value?.title || 'New Conversation')

// Format time to HH:MM
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// Load messages from backend
const loadMessagesForConversation = async (conversationId) => {
  if (!conversationId) {
    messages.value = []
    return
  }

  loadingMessages.value = true
  try {
    const messagesList = await loadChatMessages(conversationId, 50, 0)
    
    // Map backend messages to display format
    messages.value = messagesList.map(msg => ({
      id: msg.id,
      role: msg.role.toLowerCase(),
      content: msg.content,
      timestamp: msg.created_at,
      sources: msg.meta?.sources || [],
      error: msg.meta?.error || null
    }))

    await scrollToBottom()
  } catch (error) {
    console.error('Failed to load messages:', error)
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

// Watch for conversation changes when route changes
watch(
  () => route.params.id,
  async (newId) => {
    if (newId) {
      await loadMessagesForConversation(newId)
    } else {
      messages.value = []
    }
  },
  { immediate: true }
)

// Scroll to bottom when new messages arrive
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Send message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value || !activeChat.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // Add user message
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date().toISOString()
  })

  loading.value = true
  await scrollToBottom()

  try {
    // Save user message to backend
    const userMsg = await addMessage(activeChat.value.id, userMessage, 'USER')
    
    // Update user message with server timestamp and id
    if (messages.value[messages.value.length - 1].role === 'user') {
      messages.value[messages.value.length - 1].id = userMsg.id
      messages.value[messages.value.length - 1].timestamp = userMsg.created_at
    }

    // TODO: Replace with actual API call to RAG backend
    // const response = await api.post('/v1/chat', {
    //   message: userMessage,
    //   conversation_id: activeChat.value.id
    // })

    // Simulate API response for now
    await new Promise(resolve => setTimeout(resolve, 1500))

    // Mock response based on user input
    let responseContent = ''
    let sources = []

    if (userMessage.toLowerCase().includes('sales')) {
      responseContent = `Based on the SALES DEPARTMENT PLAYBOOK in our knowledge base, here are key insights:

The Sales Department follows a structured sales cycle:
• Initial meetings: 4-6 per week
• Pipeline generation: $100K+ per month

The discovery call typically lasts 20-30 minutes and includes:
1. Introduction (2 min)
2. Purpose statement (1 min)
3. Discovery questions (15 min)
4. Qualification assessment (5 min)
5. Next steps discussion (2 min)`

      sources = [
        { document: 'SALES_DEPARTMENT_PLAYBOOK.md', score: 0.95 },
        { document: 'sales_process_guide.md', score: 0.87 }
      ]
    } else if (userMessage.toLowerCase().includes('document')) {
      responseContent = `I can help you find information in your documents. Our system supports:

• Full-text search through all uploaded documents
• Semantic search using AI embeddings
• Multi-document context retrieval
• Source attribution for all answers

To get the best results, please ask specific questions about the content you're looking for.`

      sources = [
        { document: 'user_guide.md', score: 0.92 }
      ]
    } else {
      responseContent = `I'm here to help you find information in your knowledge base. Feel free to ask questions about:

• Specific documents or topics
• Relationships between concepts
• Historical information or processes
• Guidelines and best practices

I'll provide relevant sources for each answer.`
      sources = []
    }

    // Save assistant message to backend
    const assistantMsg = await addMessage(activeChat.value.id, responseContent, 'ASSISTANT', { sources })

    messages.value.push({
      role: 'assistant',
      id: assistantMsg.id,
      content: responseContent,
      sources: sources,
      timestamp: assistantMsg.created_at
    })
  } catch (error) {
    console.error('Chat error:', error)

    messages.value.push({
      role: 'assistant',
      content: 'I encountered an error processing your request.',
      error: error.message || 'Unable to retrieve information. Please try again.',
      timestamp: new Date().toISOString()
    })
  } finally {
    loading.value = false
    await scrollToBottom()
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

// Delete chat
const deleteChat = async () => {
  if (confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
    if (activeChat.value) {
      await deleteChatFromHistory(activeChat.value.id)
      showChatOptions.value = false
    }
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
</style>
