<template>
  <transition name="modal">
    <div v-if="document" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-4xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-fortress-700 bg-fortress-800">
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

        <!-- Tabs Navigation (only show operations tab for admins) -->
        <div v-if="!isUserView" class="flex gap-0 border-b border-fortress-700 bg-fortress-900/30 px-6">
          <button
            @click="activeTab = 'operations'"
            :class="[
              'px-4 py-3 font-medium transition-colors border-b-2',
              activeTab === 'operations'
                ? 'text-secure border-secure'
                : 'text-fortress-400 hover:text-fortress-300 border-transparent'
            ]"
          >
            Operations
          </button>
          <button
            @click="activeTab = 'preview'"
            :class="[
              'px-4 py-3 font-medium transition-colors border-b-2',
              activeTab === 'preview'
                ? 'text-secure border-secure'
                : 'text-fortress-400 hover:text-fortress-300 border-transparent'
            ]"
          >
            File Preview
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <!-- Operations Tab (admin only) -->
          <div v-if="!isUserView && activeTab === 'operations'" class="space-y-6">
            <!-- File Information -->
            <div class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4 space-y-3">
              <h3 class="text-sm font-semibold text-fortress-300 mb-4">File Information</h3>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-fortress-400">File Name:</span>
                  <p class="text-fortress-100 font-medium">{{ document.file_name }}</p>
                </div>
                <div>
                  <span class="text-fortress-400">File Size:</span>
                  <p class="text-fortress-100 font-medium">{{ formatFileSize(document.file_size) }}</p>
                </div>
                <div>
                  <span class="text-fortress-400">Uploaded By:</span>
                  <p class="text-fortress-100 font-medium">{{ document.uploaded_by }}</p>
                </div>
                <div>
                  <span class="text-fortress-400">Uploaded At:</span>
                  <p class="text-fortress-100 font-medium">{{ formatDate(document.uploaded_at) }}</p>
                </div>
              </div>
            </div>

            <!-- Status & Security -->
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
                <p class="text-xs font-semibold text-fortress-400 mb-2">Status</p>
                <span :class="['px-3 py-1 rounded-full text-sm font-medium inline-block', getStatusBadge(document.status)]">
                  {{ getStatusLabel(document.status) }}
                </span>
              </div>
              <div class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
                <p class="text-xs font-semibold text-fortress-400 mb-2">Security Level</p>
                <span :class="['px-3 py-1 rounded-full text-sm font-medium inline-block', getSecurityBadge(document.security_level)]">
                  {{ document.security_level }}
                </span>
              </div>
            </div>

            <!-- File Purpose -->
            <div v-if="document.file_purpose" class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
              <h3 class="text-sm font-semibold text-fortress-300 mb-2">File Purpose</h3>
              <p class="text-sm text-fortress-400">{{ document.file_purpose }}</p>
            </div>

            <!-- Processing Info -->
            <div v-if="document.chunks_created" class="p-4 bg-secure/10 border border-secure/50 rounded-lg">
              <p class="text-sm">
                <span class="font-semibold text-secure">{{ document.chunks_created }}</span>
                <span class="text-fortress-400">chunks created from this document</span>
              </p>
            </div>

            <!-- Rejection Reason -->
            <div v-if="document.rejection_reason" class="p-4 bg-alert/10 border border-alert/50 rounded-lg">
              <h3 class="text-sm font-semibold text-alert mb-2">Rejection Reason</h3>
              <p class="text-sm text-fortress-300">{{ document.rejection_reason }}</p>
            </div>

            <!-- Approval Options (if pending) -->
            <div v-if="!isUserView && document.status === 'pending'" class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4 space-y-3">
              <h3 class="text-sm font-semibold text-fortress-300">Approval Options</h3>
              <div class="space-y-2">
                <button
                  @click="$emit('approveQuick', document.id)"
                  class="w-full px-4 py-2 bg-success hover:bg-success/90 text-white font-medium rounded-lg transition-colors text-sm"
                >
                  ✓ Approve & Process Immediately
                </button>
                <button
                  @click="$emit('approveScheduled', document.id)"
                  class="w-full px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors text-sm"
                >
                  ⏰ Approve & Schedule for Later
                </button>
                <button
                  @click="$emit('approveManual', document.id)"
                  class="w-full px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors text-sm"
                >
                  👤 Approve & Manual Processing
                </button>
              </div>
            </div>

            <!-- Rejection Option (if pending or rejected) -->
            <div v-if="!isUserView && (document.status === 'pending' || document.status === 'rejected')" class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
              <button
                @click="$emit('reject', document)"
                class="w-full px-4 py-2 bg-alert/20 hover:bg-alert/30 text-alert font-medium rounded-lg transition-colors text-sm border border-alert/50"
              >
                ✗ Reject Document
              </button>
            </div>

            <!-- Resubmit Option (if rejected) -->
            <div v-if="!isUserView && document.status === 'rejected'" class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
              <button
                @click="$emit('resubmit', document)"
                class="w-full px-4 py-2 bg-secure hover:bg-secure/90 text-white font-medium rounded-lg transition-colors text-sm"
              >
                🔄 Request Resubmission
              </button>
            </div>
          </div>

          <!-- File Details (user view - always show) -->
          <div v-if="isUserView" class="space-y-6">
            <!-- File Information -->
            <div class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4 space-y-3">
              <h3 class="text-sm font-semibold text-fortress-300 mb-4">File Information</h3>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-fortress-400">File Name:</span>
                  <p class="text-fortress-100 font-medium">{{ document.file_name }}</p>
                </div>
                <div>
                  <span class="text-fortress-400">File Size:</span>
                  <p class="text-fortress-100 font-medium">{{ formatFileSize(document.file_size) }}</p>
                </div>
                <div>
                  <span class="text-fortress-400">Uploaded By:</span>
                  <p class="text-fortress-100 font-medium">{{ document.uploaded_by }}</p>
                </div>
                <div>
                  <span class="text-fortress-400">Uploaded At:</span>
                  <p class="text-fortress-100 font-medium">{{ formatDate(document.uploaded_at) }}</p>
                </div>
              </div>
            </div>

            <!-- Status & Security -->
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
                <p class="text-xs font-semibold text-fortress-400 mb-2">Status</p>
                <span :class="['px-3 py-1 rounded-full text-sm font-medium inline-block', getStatusBadge(document.status)]">
                  {{ getStatusLabel(document.status) }}
                </span>
              </div>
              <div class="bg-fortress-900/30 rounded-lg border border-fortress-700 p-4">
                <p class="text-xs font-semibold text-fortress-400 mb-2">Security Level</p>
                <span :class="['px-3 py-1 rounded-full text-sm font-medium inline-block', getSecurityBadge(document.security_level)]">
                  {{ document.security_level }}
                </span>
              </div>
            </div>

            <!-- Processing Info -->
            <div v-if="document.chunks_created" class="p-4 bg-secure/10 border border-secure/50 rounded-lg">
              <p class="text-sm">
                <span class="font-semibold text-secure">{{ document.chunks_created }}</span>
                <span class="text-fortress-400">chunks created from this document</span>
              </p>
            </div>

            <!-- File Preview Section -->
            <div class="space-y-4">
              <h3 class="text-sm font-semibold text-fortress-300">File Preview</h3>
              <FileViewerComponent
                :file-id="document.id"
                :file-name="document.file_name"
                :auto-load="true"
              />
            </div>
          </div>

          <!-- File Preview Tab (admin) -->
          <div v-else-if="!isUserView && activeTab === 'preview'" class="space-y-4">
            <FileViewerComponent
              :file-id="document.id"
              :file-name="document.file_name"
              :auto-load="true"
            />
          </div>
        </div>

        <!-- Footer -->
        <div class="flex gap-3 p-6 border-t border-fortress-700 bg-fortress-900/30">
          <button
            @click="$emit('close')"
            class="flex-1 px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'
import FileViewerComponent from './FileViewerComponent.vue'

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

defineEmits(['close', 'reject', 'resubmit', 'approveQuick', 'approveScheduled', 'approveManual'])

const activeTab = ref(props.isUserView ? 'details' : 'operations')

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
