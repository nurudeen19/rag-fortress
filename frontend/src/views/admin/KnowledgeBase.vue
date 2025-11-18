<template>
  <div class="h-full flex flex-col bg-fortress-950">
    <!-- Header -->
    <div class="bg-fortress-900 border-b border-fortress-800 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-fortress-100">Knowledge Base</h1>
          <p class="text-sm text-fortress-400 mt-1">Manage and organize your documents</p>
        </div>
        <button
          @click="showUploadModal = true"
          class="bg-secure hover:bg-secure/90 px-4 py-2 rounded-lg text-white font-medium transition-colors flex items-center space-x-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>Upload Document</span>
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="bg-fortress-900 border-b border-fortress-800 px-6">
      <div class="flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-4 border-b-2 font-medium transition-colors',
            activeTab === tab.id
              ? 'border-secure text-secure'
              : 'border-transparent text-fortress-400 hover:text-fortress-300'
          ]"
        >
          {{ tab.name }}
          <span v-if="tab.badge" class="ml-2 px-2 py-0.5 bg-alert/20 text-alert text-xs rounded-full">
            {{ tab.badge }}
          </span>
        </button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-y-auto p-6">
      <!-- My Submissions Tab -->
      <div v-show="activeTab === 'submissions'" class="space-y-4">
        <MySubmissions
          :documents="myDocuments"
          :loading="loading"
          @upload="showUploadModal = true"
          @delete="deleteDocument"
          @resubmit="showResubmitModal"
        />
      </div>

      <!-- Pending Approval Tab (Admin Only) -->
      <div v-if="isAdmin" v-show="activeTab === 'pending'" class="space-y-4">
        <PendingApprovals
          :documents="pendingDocuments"
          :loading="loading"
          @approve="approveDocument"
          @reject="showRejectModal"
        />
      </div>

      <!-- Knowledge Base Tab -->
      <div v-show="activeTab === 'knowledge-base'" class="space-y-4">
        <KnowledgeBase
          :documents="approvedDocuments"
          :loading="loading"
        />
      </div>

      <!-- Settings Tab (Admin Only) -->
      <div v-if="isAdmin" v-show="activeTab === 'settings'" class="space-y-4">
        <KnowledgeBaseSettings />
      </div>
    </div>

    <!-- Upload Modal -->
    <DocumentUploadModal
      :is-open="showUploadModal"
      @close="showUploadModal = false"
      @submit="handleUpload"
    />

    <!-- Reject Modal -->
    <RejectDocumentModal
      :is-open="showRejectModalFlag"
      :document="selectedDocument"
      @close="showRejectModalFlag = false"
      @submit="handleReject"
    />

    <!-- Resubmit Modal -->
    <ResubmitDocumentModal
      :is-open="showResubmitModalFlag"
      :document="selectedDocument"
      @close="showResubmitModalFlag = false"
      @submit="handleResubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useRoleAccess } from '../../composables/useRoleAccess'
import MySubmissions from './KnowledgeBase/MySubmissions.vue'
import PendingApprovals from './KnowledgeBase/PendingApprovals.vue'
import KnowledgeBase from './KnowledgeBase/KnowledgeBase.vue'
import KnowledgeBaseSettings from './KnowledgeBase/Settings.vue'
import DocumentUploadModal from './KnowledgeBase/DocumentUploadModal.vue'
import RejectDocumentModal from './KnowledgeBase/RejectDocumentModal.vue'
import ResubmitDocumentModal from './KnowledgeBase/ResubmitDocumentModal.vue'

const authStore = useAuthStore()
const { isAdmin } = useRoleAccess()

// State
const activeTab = ref('submissions')
const showUploadModal = ref(false)
const showRejectModalFlag = ref(false)
const showResubmitModalFlag = ref(false)
const loading = ref(false)
const selectedDocument = ref(null)

// Document lists
const myDocuments = ref([])
const pendingDocuments = ref([])
const approvedDocuments = ref([])

// Computed
const tabs = computed(() => {
  const baseTabs = [
    {
      id: 'submissions',
      name: 'My Submissions',
      badge: myDocuments.value.filter(d => d.status === 'pending').length || null
    },
    {
      id: 'knowledge-base',
      name: 'Knowledge Base'
    }
  ]

  if (isAdmin.value) {
    baseTabs.splice(1, 0, {
      id: 'pending',
      name: 'Pending Approval',
      badge: pendingDocuments.value.length || null
    })
    baseTabs.push({
      id: 'settings',
      name: 'Settings'
    })
  }

  return baseTabs
})

// Load data
const loadDocuments = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API calls
    // Load my submissions
    myDocuments.value = [
      {
        id: 1,
        file_name: 'Q4_Financial_Report.pdf',
        file_size: 2048000,
        status: 'approved',
        security_level: 'confidential',
        uploaded_at: new Date(Date.now() - 86400000).toISOString(),
        uploaded_by: authStore.user?.username,
        chunks_created: 125,
        approval_reason: 'Verified with finance team'
      },
      {
        id: 2,
        file_name: 'Sales_Process_Guide.docx',
        file_size: 512000,
        status: 'pending',
        security_level: 'internal',
        uploaded_at: new Date(Date.now() - 3600000).toISOString(),
        uploaded_by: authStore.user?.username
      }
    ]

    // Load pending approvals (admin only)
    if (isAdmin.value) {
      pendingDocuments.value = [
        {
          id: 3,
          file_name: 'New_Product_Strategy.pptx',
          file_size: 1024000,
          status: 'pending',
          security_level: 'restricted',
          uploaded_at: new Date(Date.now() - 7200000).toISOString(),
          uploaded_by: 'john_doe',
          file_purpose: 'Strategic planning for Q1 2025'
        },
        {
          id: 4,
          file_name: 'Customer_Success_Metrics.xlsx',
          file_size: 524288,
          status: 'pending',
          security_level: 'internal',
          uploaded_at: new Date(Date.now() - 10800000).toISOString(),
          uploaded_by: 'jane_smith',
          file_purpose: 'CS team performance tracking'
        }
      ]
    }

    // Load approved documents
    approvedDocuments.value = [
      {
        id: 1,
        file_name: 'Q4_Financial_Report.pdf',
        file_size: 2048000,
        status: 'processed',
        security_level: 'confidential',
        uploaded_at: new Date(Date.now() - 86400000).toISOString(),
        uploaded_by: 'admin',
        chunks_created: 125
      },
      {
        id: 5,
        file_name: 'Engineering_Best_Practices.md',
        file_size: 256000,
        status: 'processed',
        security_level: 'internal',
        uploaded_at: new Date(Date.now() - 172800000).toISOString(),
        uploaded_by: 'tech_lead',
        chunks_created: 42
      }
    ]
  } catch (error) {
    console.error('Failed to load documents:', error)
  } finally {
    loading.value = false
  }
}

// Handlers
const handleUpload = async (data) => {
  try {
    loading.value = true
    // TODO: Replace with actual API call
    // const formData = new FormData()
    // formData.append('file', data.file)
    // formData.append('security_level', data.securityLevel)
    // formData.append('file_purpose', data.purpose)
    // const response = await api.post('/v1/files/upload', formData)

    // Simulate upload
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Add to my documents
    const newDoc = {
      id: Date.now(),
      file_name: data.file.name,
      file_size: data.file.size,
      status: 'pending',
      security_level: data.securityLevel || 'internal',
      uploaded_at: new Date().toISOString(),
      uploaded_by: authStore.user?.username,
      file_purpose: data.purpose,
      department: data.department
    }

    myDocuments.value.unshift(newDoc)
    showUploadModal.value = false

    // Show success notification (you'll integrate with toast notifications later)
    console.log('Document uploaded successfully')
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    loading.value = false
  }
}

const approveDocument = async (documentId) => {
  try {
    loading.value = true
    // TODO: Replace with actual API call
    // const response = await api.post(`/v1/files/${documentId}/approve`)

    // Simulate approval
    await new Promise(resolve => setTimeout(resolve, 500))

    // Move from pending to knowledge base
    const docIndex = pendingDocuments.value.findIndex(d => d.id === documentId)
    if (docIndex !== -1) {
      const doc = pendingDocuments.value[docIndex]
      doc.status = 'processed'
      approvedDocuments.value.unshift(doc)
      pendingDocuments.value.splice(docIndex, 1)
    }

    console.log('Document approved')
  } catch (error) {
    console.error('Approval failed:', error)
  } finally {
    loading.value = false
  }
}

const deleteDocument = async (documentId) => {
  if (!confirm('Are you sure you want to delete this document?')) return

  try {
    loading.value = true
    // TODO: Replace with actual API call
    // const response = await api.delete(`/v1/files/${documentId}`)

    await new Promise(resolve => setTimeout(resolve, 500))

    myDocuments.value = myDocuments.value.filter(d => d.id !== documentId)
    console.log('Document deleted')
  } catch (error) {
    console.error('Deletion failed:', error)
  } finally {
    loading.value = false
  }
}

const showRejectModal = (document) => {
  selectedDocument.value = document
  showRejectModalFlag.value = true
}

const handleReject = async (data) => {
  try {
    loading.value = true
    // TODO: Replace with actual API call
    // const response = await api.post(`/v1/files/${data.documentId}/reject`, { 
    //   reason: data.reason,
    //   notify: data.notifyUploader 
    // })

    await new Promise(resolve => setTimeout(resolve, 500))

    const docIndex = pendingDocuments.value.findIndex(d => d.id === data.documentId)
    if (docIndex !== -1) {
      pendingDocuments.value[docIndex].status = 'rejected'
      pendingDocuments.value[docIndex].rejection_reason = data.reason
      pendingDocuments.value.splice(docIndex, 1)
    }

    showRejectModalFlag.value = false
    console.log('Document rejected')
  } catch (error) {
    console.error('Rejection failed:', error)
  } finally {
    loading.value = false
  }
}

const showResubmitModal = (document) => {
  selectedDocument.value = document
  showResubmitModalFlag.value = true
}

const handleResubmit = async (data) => {
  try {
    loading.value = true
    // TODO: Replace with actual API call
    // const formData = new FormData()
    // if (data.file) formData.append('file', data.file)
    // formData.append('document_id', data.documentId)
    // formData.append('security_level', data.securityLevel)
    // formData.append('file_purpose', data.purpose)
    // const response = await api.post('/v1/files/resubmit', formData)

    await new Promise(resolve => setTimeout(resolve, 1000))

    // Update document status
    const docIndex = myDocuments.value.findIndex(d => d.id === data.documentId)
    if (docIndex !== -1) {
      myDocuments.value[docIndex].status = 'pending'
      myDocuments.value[docIndex].uploaded_at = new Date().toISOString()
      myDocuments.value[docIndex].file_purpose = data.purpose
      myDocuments.value[docIndex].security_level = data.securityLevel
      if (data.file) {
        myDocuments.value[docIndex].file_name = data.file.name
        myDocuments.value[docIndex].file_size = data.file.size
      }
    }

    showResubmitModalFlag.value = false
    console.log('Document resubmitted')
  } catch (error) {
    console.error('Resubmit failed:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = (query) => {
  // TODO: Implement search/filter
  console.log('Search query:', query)
}

// Load data on mount
onMounted(() => {
  loadDocuments()
})
</script>
