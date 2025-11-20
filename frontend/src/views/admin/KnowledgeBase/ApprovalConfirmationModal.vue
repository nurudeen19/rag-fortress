<template>
  <transition name="modal">
    <div v-if="isOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-md shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-fortress-700">
          <h2 class="text-xl font-semibold text-fortress-100">Confirm Approval</h2>
          <button
            @click="close"
            class="p-1 hover:bg-fortress-700 rounded-lg transition-colors"
          >
            <svg class="w-6 h-6 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="p-6 space-y-6">
          <!-- Document Info -->
          <div v-if="document" class="bg-fortress-900/50 rounded-lg border border-fortress-700 p-4">
            <div class="flex items-start space-x-3">
              <svg class="w-8 h-8 text-fortress-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
              </svg>
              <div class="flex-1 min-w-0">
                <p class="text-fortress-300 font-medium truncate">{{ document.file_name }}</p>
                <p class="text-fortress-500 text-sm mt-1">
                  {{ formatFileSize(document.file_size) }} • {{ formatDate(document.uploaded_at) }}
                </p>
              </div>
            </div>
          </div>

          <!-- Action Description -->
          <div class="bg-secure/10 border border-secure/30 rounded-lg p-4">
            <p class="text-sm text-fortress-100">
              <span class="font-semibold">Approve & Process Now:</span>
              <span class="text-fortress-300 block mt-1">The document will be immediately ingested into the knowledge base.</span>
            </p>
          </div>

          <!-- Confirmation Message -->
          <div>
            <p class="text-sm text-fortress-400 text-center">
              This action cannot be undone. Proceed with approval?
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end space-x-3 p-6 border-t border-fortress-700 bg-fortress-900/50">
          <button
            @click="close"
            class="px-6 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            @click="confirm"
            :disabled="loading"
            :class="[
              'px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2',
              !loading
                ? 'bg-secure hover:bg-secure/90 text-white'
                : 'bg-secure/50 text-fortress-300 cursor-not-allowed'
            ]"
          >
            <span v-if="!loading">Approve & Process</span>
            <span v-else>Processing...</span>
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  document: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'confirm'])

const close = () => {
  emit('close')
}

const confirm = () => {
  emit('confirm')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
