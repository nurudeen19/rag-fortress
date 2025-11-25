<template>
  <div class="h-full flex flex-col">
    <h1 class="text-2xl font-bold text-fortress-100 mb-2">System Settings</h1>
    <p class="text-fortress-400 mb-6">Configure custom application settings and manage system jobs</p>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Application Settings Card -->
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <svg class="w-6 h-6 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <h2 class="text-lg font-semibold text-fortress-100">Application Settings</h2>
        </div>
        <p class="text-fortress-400 text-sm mb-6">
          Configure custom application settings that will be enforced across the system. These settings control system behavior and defaults.
        </p>
        <button 
          class="px-4 py-2 bg-secure hover:bg-secure/90 text-white rounded-lg font-medium transition-colors"
          disabled
        >
          Configure Settings (Coming Soon)
        </button>
      </div>

      <!-- Job Management Card -->
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <svg class="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
          <h2 class="text-lg font-semibold text-fortress-100">Job Management</h2>
        </div>
        <p class="text-fortress-400 text-sm mb-6">
          Process all approved files through the ingestion pipeline. You'll receive notifications when the job starts and completes.
        </p>
        
        <!-- Status Messages -->
        <div v-if="jobStatus.message" 
             class="mb-4 p-3 rounded-lg text-sm" 
             :class="jobStatus.type === 'success' ? 'bg-secure/20 text-secure' : 'bg-error/20 text-error'">
          <div class="flex items-start gap-2">
            <svg v-if="jobStatus.type === 'success'" class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <svg v-else class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            <span>{{ jobStatus.message }}</span>
          </div>
        </div>

        <button 
          @click="triggerBatchIngestion"
          :disabled="isProcessing"
          class="px-4 py-2 bg-warning hover:bg-warning/90 disabled:bg-fortress-600 disabled:cursor-not-allowed text-black rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          <svg v-if="isProcessing" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>{{ isProcessing ? 'Starting...' : 'Start Batch Ingestion' }}</span>
        </button>
        
        <p class="text-fortress-500 text-xs mt-3">
          Check your notifications for progress updates
        </p>
      </div>
    </div>

    <!-- Info Box -->
    <div class="mt-8 card p-6 bg-fortress-800/30">
      <div class="flex items-start gap-4">
        <svg class="w-6 h-6 text-info flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
          <h3 class="font-semibold text-fortress-100 mb-1">About Batch Ingestion</h3>
          <p class="text-fortress-400 text-sm">
            Batch ingestion processes all approved files through the document pipeline (parsing, chunking, embedding, and vector storage). 
            This runs as a background job and you'll receive notifications when it starts and completes.
            You can also view job status in the <router-link to="/activity-logs" class="text-secure hover:text-secure-light">Activity Logs</router-link>.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api'

const isProcessing = ref(false)
const jobStatus = ref({
  type: null,
  message: null
})

async function triggerBatchIngestion() {
  isProcessing.value = true
  jobStatus.value = { type: null, message: null }
  
  try {
    const response = await api.post('/v1/admin/files/trigger-batch-ingestion')
    
    jobStatus.value = {
      type: 'success',
      message: response.message
    }
    
    // Clear success message after 5 seconds
    setTimeout(() => {
      if (jobStatus.value.type === 'success') {
        jobStatus.value = { type: null, message: null }
      }
    }, 5000)
    
  } catch (error) {
    const errorMessage = error.response?.data?.detail || 'Failed to start batch ingestion'
    
    jobStatus.value = {
      type: 'error',
      message: errorMessage
    }
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
.card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.5) 100%);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.5rem;
}
</style>