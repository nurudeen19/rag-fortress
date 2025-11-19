<template>
  <div class="w-full">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-2">
        <h1 class="text-3xl font-bold text-fortress-100">My Uploads</h1>
        <router-link
          to="/document-upload"
          class="bg-secure hover:bg-secure/90 px-4 py-2 rounded-lg text-white font-medium transition-colors flex items-center space-x-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Upload Document</span>
        </router-link>
      </div>
      <p class="text-fortress-400">Manage your uploaded documents</p>
    </div>

    <!-- Status Filter -->
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
        <p class="text-fortress-400">Loading your documents...</p>
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

                  <!-- Resubmit button for rejected documents only -->
                  <template v-if="doc.status === 'rejected'">
                    <button
                      @click="showResubmitModal(doc)"
                      class="p-1 text-secure hover:bg-secure/10 rounded transition-colors"
                      title="Resubmit Document"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Detail Modal -->
    <DocumentDetailModal
      v-if="selectedDocument"
      :document="selectedDocument"
      :is-user-view="true"
      @close="selectedDocument = null"
    />

    <!-- Resubmit Modal -->
    <ResubmitDocumentModal
      :is-open="showResubmitModalFlag"
      :document="resubmitDocument"
      @close="showResubmitModalFlag = false"
      @submit="handleResubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../services/api'
import DocumentDetailModal from '../admin/KnowledgeBase/DocumentDetailModal.vue'
import ResubmitDocumentModal from '../admin/KnowledgeBase/ResubmitDocumentModal.vue'

// State
const documents = ref([])
const counts = ref({})
const loading = ref(false)
const error = ref(null)
const selectedDocument = ref(null)
const resubmitDocument = ref(null)
const showResubmitModalFlag = ref(false)
const currentStatus = ref('all')
const pagination = ref({ limit: 50, offset: 0, total: 0 })

const statuses = [
  { value: 'all', label: 'All Documents' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'processed', label: 'Processed' }
]

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
  selectedDocument.value = doc
}

const showResubmitModal = (doc) => {
  resubmitDocument.value = doc
  showResubmitModalFlag.value = true
}

const handleResubmit = async (data) => {
  try {
    loading.value = true
    const doc = documents.value.find(d => d.id === data.documentId)
    if (doc) {
      doc.status = 'pending'
      doc.updated_at = new Date().toISOString()
      if (data.purpose) doc.file_purpose = data.purpose
      if (data.securityLevel) doc.security_level = data.securityLevel
    }

    showResubmitModalFlag.value = false
    selectedDocument.value = null
    console.log('Document resubmitted')
  } catch (err) {
    console.error('Resubmit failed:', err)
    error.value = 'Failed to resubmit document'
  } finally {
    loading.value = false
  }
}

// Load data from backend
const loadDocuments = async () => {
  loading.value = true
  error.value = null
  try {
    // Fetch user's own documents
    const status = currentStatus.value === 'all' ? null : currentStatus.value
    const response = await api.get('/v1/files/list/my-uploads', {
      params: {
        status: status,
        limit: pagination.value.limit,
        offset: pagination.value.offset
      }
    })

    // Update counts
    counts.value = response.counts || {}
    
    // Update pagination
    pagination.value.total = response.total
    pagination.value.limit = response.limit
    pagination.value.offset = response.offset

    documents.value = (response.items || []).map(item => ({
      id: item.id,
      file_name: item.file_name,
      file_size: item.file_size,
      status: item.status,
      security_level: item.security_level,
      uploaded_at: item.created_at,
      file_purpose: item.file_purpose
    }))
  } catch (err) {
    console.error('Failed to load documents:', err)
    error.value = 'Failed to load your documents'
  } finally {
    loading.value = false
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
