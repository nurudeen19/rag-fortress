<template>
  <transition name="modal">
    <div v-if="document" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-xl max-h-[85vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 flex items-center justify-between p-6 border-b border-fortress-700 bg-fortress-800">
          <h2 class="text-xl font-semibold text-fortress-100">Document Details</h2>
          <button
            @click="$emit('close')"
            class="p-1 hover:bg-fortress-700 rounded-lg transition-colors"
          >
            <svg class="w-6 h-6 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="p-6 space-y-6">
          <!-- File Info -->
          <div>
            <h3 class="text-sm font-semibold text-fortress-300 mb-3">File Information</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-fortress-400">File Name:</span>
                <span class="text-fortress-100">{{ document.file_name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-fortress-400">File Size:</span>
                <span class="text-fortress-100">{{ formatFileSize(document.file_size) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-fortress-400">Uploaded By:</span>
                <span class="text-fortress-100">{{ document.uploaded_by }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-fortress-400">Uploaded At:</span>
                <span class="text-fortress-100">{{ formatDate(document.uploaded_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Status & Security -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm font-semibold text-fortress-300 mb-2">Status</p>
              <span :class="['px-3 py-1 rounded-full text-sm font-medium', getStatusBadge(document.status)]">
                {{ getStatusLabel(document.status) }}
              </span>
            </div>
            <div>
              <p class="text-sm font-semibold text-fortress-300 mb-2">Security Level</p>
              <span :class="['px-3 py-1 rounded-full text-sm font-medium', getSecurityBadge(document.security_level)]">
                {{ document.security_level }}
              </span>
            </div>
          </div>

          <!-- Purpose -->
          <div v-if="document.file_purpose">
            <h3 class="text-sm font-semibold text-fortress-300 mb-2">File Purpose</h3>
            <p class="text-sm text-fortress-400">{{ document.file_purpose }}</p>
          </div>

          <!-- Rejection Reason -->
          <div v-if="document.rejection_reason" class="p-4 bg-alert/10 border border-alert/50 rounded-lg">
            <h3 class="text-sm font-semibold text-alert mb-2">Rejection Reason</h3>
            <p class="text-sm text-fortress-300">{{ document.rejection_reason }}</p>
          </div>

          <!-- Processing Info -->
          <div v-if="document.chunks_created" class="p-4 bg-secure/10 border border-secure/50 rounded-lg">
            <p class="text-sm">
              <span class="font-semibold text-secure">{{ document.chunks_created }}</span>
              <span class="text-fortress-400">chunks created from this document</span>
            </p>
          </div>

          <!-- View File Button -->
          <div class="flex gap-3 pt-4 border-t border-fortress-700">
            <button
              @click="openFileViewer"
              class="flex-1 px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              View File
            </button>
          </div>

          <!-- Actions -->
          <div v-if="!isUserView && (document.status === 'pending' || document.status === 'rejected')" class="flex gap-3 pt-6 border-t border-fortress-700">
            <template v-if="document.status === 'pending'">
              <button
                @click="$emit('approve', document.id)"
                class="flex-1 px-4 py-2 bg-success hover:bg-success/90 text-white font-medium rounded-lg transition-colors"
              >
                Approve
              </button>
              <button
                @click="$emit('reject', document)"
                class="flex-1 px-4 py-2 bg-alert hover:bg-alert/90 text-white font-medium rounded-lg transition-colors"
              >
                Reject
              </button>
            </template>

            <template v-if="document.status === 'rejected'">
              <button
                @click="$emit('resubmit', document)"
                class="flex-1 px-4 py-2 bg-secure hover:bg-secure/90 text-white font-medium rounded-lg transition-colors"
              >
                Resubmit Document
              </button>
            </template>

            <button
              @click="$emit('close')"
              class="flex-1 px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors"
            >
              Close
            </button>
          </div>

          <!-- User View - Close Only -->
          <div v-else-if="isUserView" class="flex gap-3 pt-6 border-t border-fortress-700">
            <button
              @click="$emit('close')"
              class="w-full px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <!-- File Viewer Modal -->
  <FileViewerModal
    :is-open="showFileViewer"
    :file-id="document?.id"
    :file-name="document?.file_name"
    @close="showFileViewer = false"
  />
</template>

<script setup>
import { ref } from 'vue'
import FileViewerModal from './FileViewerModal.vue'

const props = defineProps({
  document: {
    type: Object,
    default: null
  },
  isUserView: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close', 'approve', 'reject', 'resubmit'])

const showFileViewer = ref(false)

const openFileViewer = () => {
  showFileViewer.value = true
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

const getStatusLabel = (status) => {
  const map = {
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
    processed: 'Processed'
  }
  return map[status] || status
}

const getStatusBadge = (status) => {
  const map = {
    pending: 'bg-warning/20 text-warning',
    approved: 'bg-success/20 text-success',
    rejected: 'bg-alert/20 text-alert',
    processed: 'bg-secure/20 text-secure'
  }
  return map[status] || 'bg-fortress-700 text-fortress-300'
}

const getSecurityBadge = (level) => {
  const map = {
    public: 'bg-secure/20 text-secure',
    internal: 'bg-fortress-700 text-fortress-200',
    confidential: 'bg-alert/20 text-alert'
  }
  return map[level] || 'bg-fortress-700 text-fortress-300'
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
