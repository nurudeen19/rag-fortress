<template>
  <div class="min-h-screen bg-fortress-900 p-6">
    <!-- Header -->
    <div class="mb-8">
      <router-link to="/knowledge-base" class="text-secure hover:text-secure/80 text-sm font-medium flex items-center gap-2 mb-3">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Knowledge Base
      </router-link>
      <h1 class="text-3xl font-bold text-fortress-100">Document Details</h1>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-96">
      <div class="text-center">
        <svg class="w-8 h-8 animate-spin mx-auto text-secure mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <p class="text-fortress-400">Loading document...</p>
      </div>
    </div>

    <!-- Content -->
    <div v-else-if="document" class="max-w-6xl mx-auto">
      <!-- Tabs Navigation -->
      <div class="flex gap-0 border-b border-fortress-700 bg-fortress-900/30 px-6 -mx-6 mb-6">
        <button
          @click="activeTab = 'operations'"
          :class="[
            'px-6 py-3 font-medium transition-colors border-b-2',
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
            'px-6 py-3 font-medium transition-colors border-b-2',
            activeTab === 'preview'
              ? 'text-secure border-secure'
              : 'text-fortress-400 hover:text-fortress-300 border-transparent'
          ]"
        >
          File Preview
        </button>
      </div>

      <!-- Operations Tab -->
      <div v-if="activeTab === 'operations'" class="space-y-6">
        <!-- File Information -->
        <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-6 space-y-4">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">File Information</h3>
          <div class="grid grid-cols-2 gap-6 text-sm">
            <div>
              <span class="text-fortress-400 text-xs font-semibold uppercase">File Name</span>
              <p class="text-fortress-100 font-medium mt-1">{{ document.file_name }}</p>
            </div>
            <div>
              <span class="text-fortress-400 text-xs font-semibold uppercase">File Size</span>
              <p class="text-fortress-100 font-medium mt-1">{{ formatFileSize(document.file_size) }}</p>
            </div>
            <div>
              <span class="text-fortress-400 text-xs font-semibold uppercase">Uploaded By</span>
              <p class="text-fortress-100 font-medium mt-1">{{ document.uploaded_by }}</p>
            </div>
            <div>
              <span class="text-fortress-400 text-xs font-semibold uppercase">Uploaded At</span>
              <p class="text-fortress-100 font-medium mt-1">{{ formatDate(document.uploaded_at) }}</p>
            </div>
          </div>
        </div>

        <!-- Status & Security -->
        <div class="grid grid-cols-2 gap-6">
          <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
            <p class="text-xs font-semibold text-fortress-400 uppercase mb-3">Status</p>
            <span :class="['px-3 py-1 rounded-full text-sm font-medium inline-block', getStatusBadge(document.status)]">
              {{ getStatusLabel(document.status) }}
            </span>
          </div>
          <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
            <p class="text-xs font-semibold text-fortress-400 uppercase mb-3">Security Level</p>
            <span :class="['px-3 py-1 rounded-full text-sm font-medium inline-block', getSecurityBadge(document.security_level)]">
              {{ document.security_level }}
            </span>
          </div>
        </div>

        <!-- File Purpose -->
        <div v-if="document.file_purpose" class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
          <h3 class="text-sm font-semibold text-fortress-100 mb-3">File Purpose</h3>
          <p class="text-sm text-fortress-400">{{ document.file_purpose }}</p>
        </div>

        <!-- Processing Info -->
        <div v-if="document.chunks_created" class="p-6 bg-secure/10 border border-secure/50 rounded-lg">
          <p class="text-sm">
            <span class="font-semibold text-secure">{{ document.chunks_created }}</span>
            <span class="text-fortress-400">chunks created from this document</span>
          </p>
        </div>

        <!-- Rejection Reason -->
        <div v-if="document.rejection_reason" class="p-6 bg-alert/10 border border-alert/50 rounded-lg">
          <h3 class="text-sm font-semibold text-alert mb-2">Rejection Reason</h3>
          <p class="text-sm text-fortress-300">{{ document.rejection_reason }}</p>
        </div>

        <!-- Approval & Rejection Options (if pending) -->
        <div v-if="document.status === 'pending'" class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Approval Options</h3>
          
          <!-- Approval buttons inline -->
          <div class="grid grid-cols-3 gap-3 mb-6">
            <button
              @click="handleApproveQuick"
              :disabled="approving"
              class="px-4 py-3 bg-gradient-to-r from-success to-success/80 hover:from-success/90 hover:to-success/70 disabled:opacity-50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
              title="Approve and start processing immediately"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Quick
            </button>
            <button
              @click="handleApproveScheduled"
              :disabled="approving"
              class="px-4 py-3 bg-fortress-700 hover:bg-fortress-600 disabled:opacity-50 text-fortress-100 font-medium rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
              title="Approve for later processing"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Schedule
            </button>
            <button
              @click="handleApproveManual"
              :disabled="approving"
              class="px-4 py-3 bg-fortress-700 hover:bg-fortress-600 disabled:opacity-50 text-fortress-100 font-medium rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
              title="Approve for manual processing"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Manual
            </button>
          </div>
          
          <!-- Rejection button -->
          <button
            @click="showRejectDialog = true"
            :disabled="approving"
            class="w-full px-4 py-3 bg-alert/20 hover:bg-alert/30 disabled:opacity-50 text-alert font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-alert/50"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Reject Document
          </button>
        </div>
      </div>

      <!-- File Preview Tab -->
      <div v-else-if="activeTab === 'preview'" class="bg-fortress-800 rounded-lg border border-fortress-700 p-6">
        <FileViewerComponent
          :file-id="document.id"
          :file-name="document.file_name"
          :auto-load="true"
        />
      </div>
    </div>
  </div>

  <!-- Approval Confirmation Dialog -->
  <transition name="modal">
    <div v-if="showApprovalDialog" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-md shadow-2xl">
        <div class="p-6">
          <h3 class="text-xl font-semibold text-fortress-100 mb-2">Confirm Approval</h3>
          <p class="text-fortress-400 mb-6">
            {{ approvalMode === 'quick' 
              ? 'This document will be approved and ingestion will start immediately.'
              : approvalMode === 'scheduled'
              ? 'This document will be approved. Ingestion can be processed manually later.'
              : 'This document will be approved. Processing will require manual action.'
            }}
          </p>

          <div class="flex gap-3">
            <button
              @click="showApprovalDialog = false"
              class="flex-1 px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 font-medium rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              @click="confirmApproval"
              :disabled="approving"
              class="flex-1 px-4 py-2 bg-secure hover:bg-secure/80 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
            >
              {{ approving ? 'Processing...' : 'Confirm' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>

  <!-- Reject Document Modal -->
  <RejectDocumentModal
    :is-open="showRejectDialog"
    :document="document"
    @close="showRejectDialog = false"
    @submit="handleReject"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../../services/api'
import FileViewerComponent from './FileViewerComponent.vue'
import RejectDocumentModal from './RejectDocumentModal.vue'

const router = useRouter()
const route = useRoute()

// State
const document = ref(null)
const loading = ref(false)
const approving = ref(false)
const activeTab = ref('operations')
const approvalMode = ref(null)
const showApprovalDialog = ref(false)
const showRejectDialog = ref(false)
const rejectionReason = ref('')

// Load document
const loadDocument = async () => {
  try {
    loading.value = true
    const documentId = route.params.id
    
    // Check if document was passed via route state
    if (history.state?.document) {
      document.value = mapBackendResponse(history.state.document)
      loading.value = false
      return
    }
    
    // Fallback: fetch from backend using the correct endpoint
    const response = await api.get(`/v1/files/${documentId}`)
    const data = response.data || response
    document.value = mapBackendResponse(data)
  } catch (err) {
    console.error('Failed to load document:', err)
    alert('Failed to load document')
    router.push({ name: 'knowledge-base' })
  } finally {
    loading.value = false
  }
}

// Map backend response to frontend format
const mapBackendResponse = (item) => {
  return {
    id: item.id,
    file_name: item.file_name,
    file_size: item.file_size,
    file_type: item.file_type,
    status: item.status,
    security_level: item.security_level,
    uploaded_at: item.created_at,
    uploaded_by: item.uploader_info?.full_name || `User #${item.uploaded_by_id}`,
    uploaded_by_id: item.uploaded_by_id,
    file_purpose: item.file_purpose,
    chunks_created: item.chunks_created,
    processing_error: item.processing_error,
    rejection_reason: null // Backend doesn't currently store rejection reason
  }
}

// Approval handlers
const handleApproveQuick = () => {
  approvalMode.value = 'quick'
  showApprovalDialog.value = true
}

const handleApproveScheduled = () => {
  approvalMode.value = 'scheduled'
  showApprovalDialog.value = true
}

const handleApproveManual = () => {
  approvalMode.value = 'manual'
  showApprovalDialog.value = true
}

const confirmApproval = async () => {
  approving.value = true
  try {
    const documentId = document.value.id

    // Approve the document
    await api.post(`/v1/files/${documentId}/approve`)

    // If quick mode, also ingest immediately
    if (approvalMode.value === 'quick') {
      await api.post(`/v1/files/${documentId}/ingest`)
    }

    // Refresh document
    await loadDocument()
    showApprovalDialog.value = false
    alert('Document approved successfully!')
  } catch (error) {
    console.error('Approval failed:', error)
    alert('Failed to approve document')
  } finally {
    approving.value = false
  }
}

const handleReject = async (data) => {
  approving.value = true
  try {
    await api.post(`/v1/files/${data.documentId}/reject`, {
      reason: data.reason
    })

    // Refresh document
    await loadDocument()
    showRejectDialog.value = false
    alert('Document rejected successfully!')
  } catch (error) {
    console.error('Rejection failed:', error)
    alert('Failed to reject document')
  } finally {
    approving.value = false
  }
}

// Formatting utilities
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

// Lifecycle
onMounted(() => {
  loadDocument()
})
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
