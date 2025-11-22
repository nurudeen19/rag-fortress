<template>
  <div class="h-full flex flex-col bg-fortress-950">
    <!-- Conversation Header -->
    <div class="bg-fortress-900 border-b border-fortress-800 px-6 py-4 flex items-center justify-between">
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
          class="p-2 rounded-lg text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 transition-colors relative"
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
          class="absolute right-6 top-20 w-48 bg-fortress-900 border border-fortress-800 rounded-lg shadow-glow overflow-hidden animate-fade-in"
        >
          <div class="p-2 space-y-1">
            <button
              @click="renameChat"
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
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
      <!-- Empty State -->
      <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto mb-4 text-fortress-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p class="text-fortress-300 text-lg">Start a conversation</p>
          <p class="text-fortress-500 text-sm mt-2">Ask questions about your documents</p>
        </div>
      </div>

      <!-- Messages -->
      <template v-for="(message, index) in messages" :key="index">
        <!-- User Message -->
        <div v-if="message.role === 'user'" class="flex justify-end">
          <div class="max-w-xs lg:max-w-md bg-secure/20 border border-secure/40 rounded-lg px-4 py-3">
            <p class="text-fortress-100">{{ message.content }}</p>
            <p class="text-xs text-secure/60 mt-1">{{ formatTime(message.timestamp) }}</p>
          </div>
        </div>

        <!-- Assistant Message -->
        <div v-else class="flex justify-start">
          <div class="max-w-xs lg:max-w-md">
            <!-- Main Response -->
            <div class="bg-fortress-800 rounded-lg px-4 py-3 mb-2">
              <p class="text-fortress-100 whitespace-pre-wrap">{{ message.content }}</p>
              <p class="text-xs text-fortress-500 mt-2">{{ formatTime(message.timestamp) }}</p>
            </div>

            <!-- Sources/References -->
            <div v-if="message.sources && message.sources.length > 0" class="text-sm">
              <p class="text-fortress-400 mb-2">📄 <span class="font-medium">Sources:</span></p>
              <div class="space-y-1 ml-4">
                <div
                  v-for="(source, idx) in message.sources"
                  :key="idx"
                  class="flex items-start space-x-2 p-2 bg-fortress-800/50 rounded border border-fortress-700"
                >
                  <span class="text-fortress-500 text-xs font-medium mt-0.5">{{ idx + 1 }}.</span>
                  <div class="flex-1">
                    <p class="text-fortress-300 text-xs break-words">{{ source.document }}</p>
                    <p class="text-fortress-500 text-xs mt-0.5">Relevance: {{ Math.round(source.score * 100) }}%</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="message.error" class="bg-alert/10 border border-alert/30 rounded-lg px-3 py-2">
              <p class="text-alert text-sm">⚠️ {{ message.error }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- Loading Indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="bg-fortress-800 rounded-lg px-4 py-3">
          <div class="flex items-center space-x-2">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-fortress-500 rounded-full animate-bounce" style="animation-delay: 0s"></div>
              <div class="w-2 h-2 bg-fortress-500 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-fortress-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
            <span class="text-fortress-400 text-sm">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="bg-fortress-900 border-t border-fortress-800 px-6 py-4">
      <form @submit.prevent="sendMessage" class="space-y-3">
        <div class="flex items-end space-x-3">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Ask a question about your documents..."
            class="flex-1 bg-fortress-800 border border-fortress-700 rounded-lg px-4 py-3 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure focus:ring-1 focus:ring-secure transition-colors"
            :disabled="loading"
            @keydown.enter="sendMessage"
          />
          <button
            type="submit"
            class="bg-secure hover:bg-secure/90 disabled:bg-secure/50 disabled:cursor-not-allowed px-6 py-3 rounded-lg text-white font-medium transition-colors"
            :disabled="loading || !inputMessage.trim()"
          >
            <span v-if="!loading">Send</span>
            <span v-else class="flex items-center space-x-1">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Sending</span>
            </span>
          </button>
        </div>

        <!-- Character Count -->
        <div class="flex justify-between items-center text-xs">
          <p class="text-fortress-500">
            {{ inputMessage.length }} / 2000 characters
          </p>
          <button
            v-if="messages.length > 0"
            type="button"
            @click="clearHistory"
            class="text-fortress-500 hover:text-fortress-400 transition-colors"
          >
            Clear History
          </button>
        </div>
      </form>

      <!-- Info Message -->
      <div v-if="messages.length === 0" class="mt-4 p-3 bg-fortress-800/50 rounded-lg border border-fortress-700">
        <p class="text-fortress-400 text-sm">
          💡 <span class="font-medium">Tip:</span> Ask specific questions about your documents for better results. You can ask about concepts, facts, or relationships in your knowledge base.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useChatHistory } from '../../composables/useChatHistory'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { activeChat, deleteChat: deleteChatFromHistory, renameChat: renameChatFromHistory } = useChatHistory()

// State
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const showChatOptions = ref(false)

const currentChatTitle = computed(() => activeChat.value?.title || 'New Conversation')

// Format time to HH:MM
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// Scroll to bottom when new messages arrive
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Send message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

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
    // TODO: Replace with actual API call to RAG backend
    // const response = await api.post('/v1/chat', {
    //   message: userMessage,
    //   conversation_id: conversationId
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

    messages.value.push({
      role: 'assistant',
      content: responseContent,
      sources: sources,
      timestamp: new Date().toISOString()
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

// Rename chat
const renameChat = async () => {
  const newTitle = prompt('Enter new conversation title:', currentChatTitle.value)
  if (newTitle && newTitle.trim() && activeChat.value) {
    await renameChatFromHistory(activeChat.value.id, newTitle.trim())
    showChatOptions.value = false
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

// Auto scroll on mount
onMounted(() => {
  scrollToBottom()
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
</style>
      <!-- Empty State -->
      <div v-if="messages.length === 0" class="h-full flex items-center justify-center">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto mb-4 text-fortress-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p class="text-fortress-300 text-lg">Start a conversation</p>
          <p class="text-fortress-500 text-sm mt-2">Ask questions about your documents</p>
        </div>
      </div>

      <!-- Messages -->
      <template v-for="(message, index) in messages" :key="index">
        <!-- User Message -->
        <div v-if="message.role === 'user'" class="flex justify-end">
          <div class="max-w-xs lg:max-w-md bg-secure/20 border border-secure/40 rounded-lg px-4 py-3">
            <p class="text-fortress-100">{{ message.content }}</p>
            <p class="text-xs text-secure/60 mt-1">{{ formatTime(message.timestamp) }}</p>
          </div>
        </div>

        <!-- Assistant Message -->
        <div v-else class="flex justify-start">
          <div class="max-w-xs lg:max-w-md">
            <!-- Main Response -->
            <div class="bg-fortress-800 rounded-lg px-4 py-3 mb-2">
              <p class="text-fortress-100 whitespace-pre-wrap">{{ message.content }}</p>
              <p class="text-xs text-fortress-500 mt-2">{{ formatTime(message.timestamp) }}</p>
            </div>

            <!-- Sources/References -->
            <div v-if="message.sources && message.sources.length > 0" class="text-sm">
              <p class="text-fortress-400 mb-2">📄 <span class="font-medium">Sources:</span></p>
              <div class="space-y-1 ml-4">
                <div
                  v-for="(source, idx) in message.sources"
                  :key="idx"
                  class="flex items-start space-x-2 p-2 bg-fortress-800/50 rounded border border-fortress-700"
                >
                  <span class="text-fortress-500 text-xs font-medium mt-0.5">{{ idx + 1 }}.</span>
                  <div class="flex-1">
                    <p class="text-fortress-300 text-xs break-words">{{ source.document }}</p>
                    <p class="text-fortress-500 text-xs mt-0.5">Relevance: {{ Math.round(source.score * 100) }}%</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="message.error" class="bg-alert/10 border border-alert/30 rounded-lg px-3 py-2">
              <p class="text-alert text-sm">⚠️ {{ message.error }}</p>
            </div>
          </div>
        </div>
      </template>

      <!-- Loading Indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="bg-fortress-800 rounded-lg px-4 py-3">
          <div class="flex items-center space-x-2">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-fortress-500 rounded-full animate-bounce" style="animation-delay: 0s"></div>
              <div class="w-2 h-2 bg-fortress-500 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-fortress-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
            <span class="text-fortress-400 text-sm">Thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="bg-fortress-900 border-t border-fortress-800 px-6 py-4">
      <form @submit.prevent="sendMessage" class="space-y-3">
        <div class="flex items-end space-x-3">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Ask a question about your documents..."
            class="flex-1 bg-fortress-800 border border-fortress-700 rounded-lg px-4 py-3 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure focus:ring-1 focus:ring-secure transition-colors"
            :disabled="loading"
            @keydown.enter="sendMessage"
          />
          <button
            type="submit"
            class="bg-secure hover:bg-secure/90 disabled:bg-secure/50 disabled:cursor-not-allowed px-6 py-3 rounded-lg text-white font-medium transition-colors"
            :disabled="loading || !inputMessage.trim()"
          >
            <span v-if="!loading">Send</span>
            <span v-else class="flex items-center space-x-1">
              <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Sending</span>
            </span>
          </button>
        </div>

        <!-- Character Count -->
        <div class="flex justify-between items-center text-xs">
          <p class="text-fortress-500">
            {{ inputMessage.length }} / 2000 characters
          </p>
          <button
            v-if="messages.length > 0"
            type="button"
            @click="clearHistory"
            class="text-fortress-500 hover:text-fortress-400 transition-colors"
          >
            Clear History
          </button>
        </div>
      </form>

      <!-- Info Message -->
      <div v-if="messages.length === 0" class="mt-4 p-3 bg-fortress-800/50 rounded-lg border border-fortress-700">
        <p class="text-fortress-400 text-sm">
          💡 <span class="font-medium">Tip:</span> Ask specific questions about your documents for better results. You can ask about concepts, facts, or relationships in your knowledge base.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

// State
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

// Format time to HH:MM
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// Scroll to bottom when new messages arrive
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Send message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

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
    // TODO: Replace with actual API call to RAG backend
    // const response = await api.post('/v1/chat', {
    //   message: userMessage,
    //   conversation_id: conversationId
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

    messages.value.push({
      role: 'assistant',
      content: responseContent,
      sources: sources,
      timestamp: new Date().toISOString()
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

// Auto scroll on mount
onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
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
</style>