<template>
  <div class="space-y-6">
    <!-- Document Processing Settings -->
    <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
      <h3 class="text-lg font-semibold text-fortress-100 mb-4">Document Processing</h3>
      
      <div class="space-y-4">
        <!-- Chunk Size -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Document Chunk Size
          </label>
          <div class="flex items-center space-x-3">
            <input
              v-model.number="settings.chunkSize"
              type="range"
              min="256"
              max="2048"
              step="256"
              class="flex-1 h-2 bg-fortress-700 rounded-lg appearance-none cursor-pointer accent-secure"
            />
            <span class="text-sm text-fortress-400 w-20">{{ settings.chunkSize }} tokens</span>
          </div>
          <p class="text-xs text-fortress-500 mt-2">Size of document chunks for embedding (smaller = more granular, larger = more context)</p>
        </div>

        <!-- Chunk Overlap -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Chunk Overlap
          </label>
          <div class="flex items-center space-x-3">
            <input
              v-model.number="settings.chunkOverlap"
              type="range"
              min="0"
              max="512"
              step="32"
              class="flex-1 h-2 bg-fortress-700 rounded-lg appearance-none cursor-pointer accent-secure"
            />
            <span class="text-sm text-fortress-400 w-20">{{ settings.chunkOverlap }} tokens</span>
          </div>
          <p class="text-xs text-fortress-500 mt-2">Overlap between chunks to preserve context</p>
        </div>

        <!-- Max File Size -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Maximum Upload Size
          </label>
          <div class="flex items-center space-x-3">
            <select
              v-model="settings.maxFileSize"
              class="flex-1 bg-fortress-700 border border-fortress-600 rounded-lg px-3 py-2 text-fortress-100 focus:outline-none focus:border-secure"
            >
              <option value="10">10 MB</option>
              <option value="25">25 MB</option>
              <option value="50">50 MB</option>
              <option value="100">100 MB</option>
              <option value="250">250 MB</option>
            </select>
          </div>
          <p class="text-xs text-fortress-500 mt-2">Maximum file size allowed for document uploads</p>
        </div>
      </div>
    </div>

    <!-- Security Settings -->
    <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
      <h3 class="text-lg font-semibold text-fortress-100 mb-4">Security Settings</h3>
      
      <div class="space-y-4">
        <!-- Default Security Level -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Default Security Level
          </label>
          <select
            v-model="settings.defaultSecurityLevel"
            class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-3 py-2 text-fortress-100 focus:outline-none focus:border-secure"
          >
            <option value="internal">Internal</option>
            <option value="confidential">Confidential</option>
            <option value="restricted">Restricted</option>
          </select>
          <p class="text-xs text-fortress-500 mt-2">Default classification for newly uploaded documents</p>
        </div>

        <!-- Allowed File Types -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Allowed File Types
          </label>
          <div class="bg-fortress-900/50 rounded-lg border border-fortress-700 p-3">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="type in settings.allowedFileTypes"
                :key="type"
                class="inline-flex items-center space-x-2 bg-secure/20 text-secure px-3 py-1 rounded-full text-sm border border-secure/50"
              >
                <span>{{ type }}</span>
                <button
                  @click="removeFileType(type)"
                  class="hover:text-alert transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>
          <p class="text-xs text-fortress-500 mt-2">File extensions that can be uploaded</p>
        </div>

        <!-- Require Approval -->
        <div class="flex items-center space-x-3">
          <input
            v-model="settings.requireApproval"
            type="checkbox"
            class="w-4 h-4 rounded border-fortress-600 text-secure focus:ring-secure cursor-pointer"
          />
          <label class="text-sm font-medium text-fortress-300 cursor-pointer">
            Require approval for all uploads
          </label>
        </div>
      </div>
    </div>

    <!-- Queue Status -->
    <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
      <h3 class="text-lg font-semibold text-fortress-100 mb-4">Processing Queue</h3>
      
      <div class="space-y-4">
        <!-- Queue Stats -->
        <div class="grid grid-cols-3 gap-3">
          <div class="bg-fortress-900/50 rounded-lg p-3 border border-fortress-700">
            <p class="text-xs text-fortress-500">Queued</p>
            <p class="text-2xl font-bold text-fortress-100">{{ queueStats.queued }}</p>
          </div>
          <div class="bg-fortress-900/50 rounded-lg p-3 border border-fortress-700">
            <p class="text-xs text-fortress-500">Processing</p>
            <p class="text-2xl font-bold text-fortress-100">{{ queueStats.processing }}</p>
          </div>
          <div class="bg-fortress-900/50 rounded-lg p-3 border border-fortress-700">
            <p class="text-xs text-fortress-500">Failed</p>
            <p class="text-2xl font-bold text-alert">{{ queueStats.failed }}</p>
          </div>
        </div>

        <!-- Queue Controls -->
        <div class="flex items-center space-x-3">
          <button
            @click="pauseQueue"
            :disabled="queuePaused"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              queuePaused
                ? 'bg-fortress-700/50 text-fortress-500 cursor-not-allowed'
                : 'bg-amber-900/30 text-amber-300 hover:bg-amber-900/50 border border-amber-700/50'
            ]"
          >
            {{ queuePaused ? 'Queue Paused' : 'Pause Queue' }}
          </button>
          <button
            @click="resumeQueue"
            :disabled="!queuePaused"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-colors',
              !queuePaused
                ? 'bg-fortress-700/50 text-fortress-500 cursor-not-allowed'
                : 'bg-success/20 text-success hover:bg-success/30 border border-success/50'
            ]"
          >
            Resume Queue
          </button>
          <button
            @click="clearFailedJobs"
            class="px-4 py-2 bg-alert/20 text-alert hover:bg-alert/30 rounded-lg font-medium transition-colors border border-alert/50"
          >
            Clear Failed
          </button>
        </div>

        <!-- Queue Info -->
        <div class="p-3 bg-fortress-900/50 rounded-lg border border-fortress-700">
          <p class="text-xs text-fortress-500">
            Last job: <span class="text-fortress-300 font-medium">{{ queueStats.lastJobTime }}</span>
          </p>
          <p class="text-xs text-fortress-500 mt-1">
            Avg processing time: <span class="text-fortress-300 font-medium">{{ queueStats.avgTime }}</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Save Changes -->
    <div class="flex items-center justify-end space-x-3">
      <button
        @click="resetSettings"
        class="px-6 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg font-medium transition-colors"
      >
        Reset
      </button>
      <button
        @click="saveSettings"
        class="px-6 py-2 bg-secure hover:bg-secure/90 text-white rounded-lg font-medium transition-colors"
      >
        Save Changes
      </button>
    </div>

    <!-- Success Message -->
    <transition name="fade">
      <div v-if="showSuccess" class="fixed bottom-4 right-4 bg-success text-white px-4 py-3 rounded-lg shadow-lg">
        Settings saved successfully
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const settings = ref({
  chunkSize: 1024,
  chunkOverlap: 128,
  maxFileSize: '50',
  defaultSecurityLevel: 'internal',
  allowedFileTypes: ['.pdf', '.txt', '.docx', '.xlsx', '.md'],
  requireApproval: true
})

const queueStats = ref({
  queued: 3,
  processing: 1,
  failed: 0,
  lastJobTime: '2 minutes ago',
  avgTime: '45 seconds'
})

const queuePaused = ref(false)
const showSuccess = ref(false)

const removeFileType = (type) => {
  settings.value.allowedFileTypes = settings.value.allowedFileTypes.filter(t => t !== type)
}

const pauseQueue = () => {
  queuePaused.value = true
  // TODO: API call to pause queue
}

const resumeQueue = () => {
  queuePaused.value = false
  // TODO: API call to resume queue
}

const clearFailedJobs = () => {
  queueStats.value.failed = 0
  // TODO: API call to clear failed jobs
}

const saveSettings = () => {
  // TODO: API call to save settings
  showSuccess.value = true
  setTimeout(() => {
    showSuccess.value = false
  }, 3000)
}

const resetSettings = () => {
  settings.value = {
    chunkSize: 1024,
    chunkOverlap: 128,
    maxFileSize: '50',
    defaultSecurityLevel: 'internal',
    allowedFileTypes: ['.pdf', '.txt', '.docx', '.xlsx', '.md'],
    requireApproval: true
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
