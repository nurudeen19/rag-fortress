<template>
  <div class="w-full">
    <!-- Notification Toast -->
    <div v-if="notification.show" class="fixed top-4 right-4 max-w-md z-50 p-4 rounded-lg shadow-lg border" :class="notification.type === 'success' ? 'bg-secure/20 text-secure border-secure/50' : 'bg-alert/20 text-alert border-alert/50'">
      <div class="flex items-center justify-between">
        <span>{{ notification.message }}</span>
        <button @click="notification.show = false" class="ml-2 hover:opacity-70">×</button>
      </div>
    </div>

    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-2">
        <h1 class="text-3xl font-bold text-fortress-100">Knowledge Base</h1>
        <div class="flex gap-2">
          <router-link
            to="/document-upload"
            class="px-4 py-2 rounded-lg font-medium transition-colors bg-secure hover:bg-secure/90 text-white flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Upload Document
          </router-link>
          <button
            @click="refreshDocuments"
            :disabled="loading"
            class="px-4 py-2 rounded-lg font-medium transition-colors bg-fortress-800 hover:bg-fortress-700 disabled:opacity-50 text-fortress-300 flex items-center gap-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>
      <p class="text-fortress-400">Manage all documents in the knowledge base (Admin only)</p>
    </div>

    <!-- Status Filter - Ordered with Pending first -->
    <div class="mb-6 flex gap-2 flex-wrap">
      <button
        v-for="status in statuses"
        :key="status.value"
        @click="currentStatus = status.value; onStatusChange()"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors',
          currentStatus === status.value
            ? 'bg-secure text-white'
            : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
        ]"
      >
        {{ status.label }}
        <span class="ml-2 text-sm">{{ getStatusCount(status.value) }}</span>
      </button>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="mb-6 p-4 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
      {{ error }}
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <div v-if="loading" class="p-12 text-center">
        <svg class="w-8 h-8 animate-spin mx-auto text-secure mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <p class="text-fortress-400">Loading documents...</p>
      </div>

      <div v-else-if="filteredDocuments.length === 0" class="p-12 text-center">
        <svg class="w-12 h-12 text-fortress-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-fortress-400">No documents found</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-fortress-700 bg-fortress-900/50">
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">File Name</th>
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">File Type</th>
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">Uploaded By</th>
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">Size</th>
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">Status</th>
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">Security</th>
              <th class="text-left px-6 py-4 font-semibold text-fortress-100">Uploaded</th>
              <th class="text-right px-6 py-4 font-semibold text-fortress-100">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="doc in filteredDocuments"
              :key="doc.id"
              class="border-b border-fortress-800 hover:bg-fortress-900/50 transition-colors"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <svg class="w-5 h-5 text-fortress-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                  </svg>
                  <div class="truncate">
                    <p class="text-fortress-100 font-medium truncate">{{ doc.file_name }}</p>
                    <p v-if="doc.file_purpose" class="text-xs text-fortress-500 truncate">{{ doc.file_purpose }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="px-3 py-1 rounded-full text-xs font-medium bg-fortress-800 text-fortress-200">
                  {{ formatFileType(doc.file_type) }}
                </span>
              </td>
              <td class="px-6 py-4 text-fortress-300 text-sm">
                <div>
                  <p class="font-medium">{{ doc.uploaded_by_name || `User #${doc.uploaded_by_id}` }}</p>
                  <p v-if="doc.uploaded_by_dept" class="text-xs text-fortress-500">{{ doc.uploaded_by_dept }}</p>
                </div>
              </td>
              <td class="px-6 py-4 text-fortress-300">{{ formatFileSize(doc.file_size) }}</td>
              <td class="px-6 py-4">
                <span :class="['px-3 py-1 rounded-full text-xs font-medium', getStatusBadge(doc.status)]">
                  {{ getStatusLabel(doc.status) }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span :class="['px-3 py-1 rounded-full text-xs font-medium', getSecurityBadge(doc.security_level)]">
                  {{ doc.security_level }}
                </span>
              </td>
              <td class="px-6 py-4 text-fortress-300 text-sm">
                {{ formatDate(doc.uploaded_at) }}
              </td>
              <td class="px-6 py-4">
                <div class="flex justify-end gap-2">
                  <button
                    @click="viewDocument(doc)"
                    class="p-1 text-fortress-400 hover:text-secure hover:bg-secure/10 rounded transition-colors"
                    title="View Details"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  
                  <!-- Approve/Reject buttons for pending documents -->
                  <template v-if="doc.status === 'pending'">
                    <button
                      @click="initiateApproval(doc)"
                      :disabled="loading"
                      class="p-1 text-success hover:bg-success/10 disabled:opacity-50 rounded transition-colors"
                      title="Quick Approve & Process"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      @click="showRejectModal(doc)"
                      :disabled="loading"
                      class="p-1 text-alert hover:bg-alert/10 disabled:opacity-50 rounded transition-colors"
                      title="Reject"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l-2-2m0 0l-2-2m2 2l2-2m-2 2l-2 2" />
                      </svg>
                    </button>
                  </template>

                  <!-- Delete button -->
                  <button
                    @click="deleteDocument(doc.id)"
                    :disabled="loading"
                    class="p-1 text-fortress-400 hover:text-alert hover:bg-alert/10 disabled:opacity-50 rounded transition-colors"
                    title="Delete"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination Controls -->
        <div class="flex items-center justify-between p-4 border-t border-fortress-800">
          <div class="text-sm text-fortress-400">
            Showing {{ pagination.offset + 1 }}-{{ Math.min(pagination.offset + pagination.limit, pagination.total) }} of {{ pagination.total }} documents
          </div>
          <div class="flex gap-2">
            <button
              @click="prevPage"
              :disabled="pagination.offset === 0 || loading"
              class="px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-fortress-800 hover:bg-fortress-700 text-fortress-300"
            >
              ← Previous
            </button>
            <button
              @click="nextPage"
              :disabled="pagination.offset + pagination.limit >= pagination.total || loading"
              class="px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-fortress-800 hover:bg-fortress-700 text-fortress-300"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <RejectDocumentModal
      :is-open="showRejectModalFlag"
      :document="rejectDocument"
      @close="showRejectModalFlag = false"
      @submit="handleReject"
    />

    <!-- Approval Confirmation Modal -->
    <ApprovalConfirmationModal
      :is-open="showApprovalConfirm"
      :document="approvalDocument"
      :loading="approvingDocument"
      @close="showApprovalConfirm = false"
      @confirm="confirmApproval"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api'
import RejectDocumentModal from './KnowledgeBase/RejectDocumentModal.vue'
import ApprovalConfirmationModal from './KnowledgeBase/ApprovalConfirmationModal.vue'

const router = useRouter()

// State
const documents = ref([])
const counts = ref({})
const loading = ref(false)
const error = ref(null)
const rejectDocument = ref(null)
const showRejectModalFlag = ref(false)
const currentStatus = ref('pending')
const pagination = ref({ limit: 50, offset: 0, total: 0 })
const showApprovalConfirm = ref(false)
const approvalDocument = ref(null)
const approvingDocument = ref(false)
const notification = ref({ show: false, message: '', type: 'success' })

// Status filters ordered with pending first for admins
const statuses = [
  { value: 'pending', label: 'Pending Approval' },
  { value: 'all', label: 'All Documents' },
  { value: 'approved', label: 'Approved' },
  { value: 'processed', label: 'Processed' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'failed', label: 'Failed' }
]

// Notification helper
const showNotification = (message, type = 'success') => {
  notification.value = { show: true, message, type }
  setTimeout(() => {
    notification.value.show = false
  }, 4000)
}

// Computed
const filteredDocuments = computed(() => {
  if (currentStatus.value === 'all') {
    return documents.value
  }
  return documents.value.filter(d => d.status === currentStatus.value)
})

// Helper functions
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
    day: 'numeric'
  })
}

const formatFileType = (fileType) => {
  if (!fileType) return 'Unknown'
  const typeMap = {
    'markdown': 'Markdown',
    'csv': 'CSV',
    'json': 'JSON',
    'pdf': 'PDF',
    'text': 'Text',
    'excel': 'Excel'
  }
  return typeMap[fileType] || fileType.charAt(0).toUpperCase() + fileType.slice(1)
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

const getStatusCount = (status) => {
  if (status === 'all') return counts.value.all || 0
  return counts.value[status] || 0
}

// Actions
const viewDocument = (doc) => {
  // Navigate to details page and pass document as state
  router.push({
    name: 'document-details',
    params: { id: doc.id },
    state: { document: doc }
  })
}

const initiateApproval = (doc) => {
  approvalDocument.value = doc
  showApprovalConfirm.value = true
}

const confirmApproval = async () => {
  if (!approvalDocument.value) return

  try {
    approvingDocument.value = true
    const documentId = approvalDocument.value.id
    
    // Approve and ingest immediately (approve endpoint triggers job)
    const response = await api.post(`/v1/files/${documentId}/approve`)

    // Update document status
    const doc = documents.value.find(d => d.id === documentId)
    if (doc) {
      doc.status = 'approved'
    }

    showApprovalConfirm.value = false
    approvalDocument.value = null
    
    // Refresh counts
    await loadCounts()
    
    // Show success feedback with job info
    const message = response.data?.message || 'Document approved successfully!'
    const jobInfo = response.data?.data?.job_id ? ` (Job #${response.data.data.job_id})` : ''
    showNotification(message + jobInfo, 'success')
  } catch (error) {
    console.error('Approval failed:', error)
    const errorMsg = error.response?.data?.detail || error.message || 'Failed to approve document'
    showNotification(errorMsg, 'error')
  } finally {
    approvingDocument.value = false
  }
}

const showRejectModal = (doc) => {
  rejectDocument.value = doc
  showRejectModalFlag.value = true
}

const handleReject = async (data) => {
  try {
    loading.value = true
    // Backend expects multipart/form-data with fields: reason (string) and notify_user (bool)
    const formData = new FormData()
    formData.append('reason', data.reason)
    formData.append('notify_user', data.notifyUploader)
    await api.post(`/v1/files/${data.documentId}/reject`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    const doc = documents.value.find(d => d.id === data.documentId)
    if (doc) {
      doc.status = 'rejected'
    }

    // Refresh counts
    await loadCounts()

    showRejectModalFlag.value = false
    showNotification('Document rejected successfully', 'success')
  } catch (err) {
    console.error('Rejection failed:', err)
    const errorMsg = err.response?.data?.detail || err.message || 'Failed to reject document'
    showNotification(errorMsg, 'error')
  } finally {
    loading.value = false
  }
}

const deleteDocument = async (documentId) => {
  if (!confirm('Are you sure you want to delete this document?')) return

  try {
    loading.value = true
    documents.value = documents.value.filter(d => d.id !== documentId)
    console.log('Document deleted')
  } catch (err) {
    console.error('Delete failed:', err)
    error.value = 'Failed to delete document'
  } finally {
    loading.value = false
  }
}

const refreshDocuments = () => {
  loadDocuments()
  loadCounts()
}

// Load all documents from backend with status filtering and pagination
const loadDocuments = async () => {
  loading.value = true
  error.value = null
  try {
    const statusFilter = currentStatus.value === 'all' ? null : currentStatus.value
    const response = await api.get('/v1/files/list', {
      params: {
        status_filter: statusFilter,
        limit: pagination.value.limit,
        offset: pagination.value.offset
      }
    })

    // Update pagination
    pagination.value.total = response.total
    pagination.value.limit = response.limit
    pagination.value.offset = response.offset

    documents.value = (response.items || []).map(item => ({
      id: item.id,
      file_name: item.file_name,
      file_size: item.file_size,
      file_type: item.file_type,
      status: item.status,
      security_level: item.security_level,
      uploaded_at: item.created_at,
      uploaded_by_id: item.uploaded_by_id,
      uploaded_by_name: item.uploader_info?.full_name || null,
      uploaded_by_dept: item.uploader_info?.department_name || null,
      file_purpose: item.file_purpose
    }))
  } catch (err) {
    console.error('Failed to load documents:', err)
    error.value = 'Failed to load documents from server'
  } finally {
    loading.value = false
  }
}

// Load counts from dedicated stats endpoint
const loadCounts = async () => {
  try {
    const response = await api.get('/v1/files/stats/counts')
    counts.value = response.counts || {}
  } catch (err) {
    console.error('Failed to load counts:', err)
    // Silently fail - counts not critical
  }
}

// Handle status tab change
const onStatusChange = () => {
  pagination.value.offset = 0  // Reset to first page
  loadDocuments()
}

// Handle pagination
const nextPage = () => {
  if (pagination.value.offset + pagination.value.limit < pagination.value.total) {
    pagination.value.offset += pagination.value.limit
    loadDocuments()
  }
}

const prevPage = () => {
  if (pagination.value.offset > 0) {
    pagination.value.offset -= pagination.value.limit
    loadDocuments()
  }
}

// Load data on mount
onMounted(() => {
  loadDocuments()
  loadCounts()
})
</script>

<style scoped>
.card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.5) 100%);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.5rem;
}

table {
  background: transparent;
}

tbody tr {
  background: transparent;
}
</style>
