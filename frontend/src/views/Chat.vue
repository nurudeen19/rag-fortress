<template>
  <div class="chat">
    <h1>Chat with Your Documents</h1>
    
    <div class="chat-container">
      <div class="messages">
        <div v-for="message in messages" :key="message.id" :class="['message', message.role]">
          <div class="message-content">
            {{ message.content }}
          </div>
        </div>
      </div>

      <div class="input-area">
        <input 
          v-model="userInput" 
          @keyup.enter="sendMessage"
          placeholder="Ask a question about your documents..."
          :disabled="loading"
        />
        <button @click="sendMessage" :disabled="loading">
          {{ loading ? 'Sending...' : 'Send' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: 'Hello! I\'m ready to help you query your documents. What would you like to know?'
  }
])

const userInput = ref('')
const loading = ref(false)

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  // Add user message
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userInput.value
  })

  const query = userInput.value
  userInput.value = ''
  loading.value = true

  try {
    // TODO: Replace with actual API call
    // const response = await api.chat(query)
    
    // Simulated response
    setTimeout(() => {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: 'This is a placeholder response. Connect to the backend API to get real responses.'
      })
      loading.value = false
    }, 1000)
  } catch (error) {
    console.error('Error sending message:', error)
    loading.value = false
  }
}
</script>

<style scoped>
.chat {
  max-width: 800px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #2c3e50;
}

.chat-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.messages {
  height: 500px;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  max-width: 70%;
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 1rem;
  border-radius: 8px;
  line-height: 1.5;
}

.message.user .message-content {
  background-color: #42b983;
  color: white;
}

.message.assistant .message-content {
  background-color: #f0f0f0;
  color: #2c3e50;
}

.input-area {
  display: flex;
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  gap: 0.5rem;
}

.input-area input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.input-area input:focus {
  outline: none;
  border-color: #42b983;
}

.input-area button {
  padding: 0.75rem 1.5rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.input-area button:hover:not(:disabled) {
  background-color: #3aa876;
}

.input-area button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
