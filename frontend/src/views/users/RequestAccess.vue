<template>
  <div class="h-full flex flex-col">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-fortress-100 mb-2">Request Access</h1>
      <p class="text-fortress-400">Request temporary elevated access to documents when you need additional clearance</p>
    </div>

    <!-- New Request Button Card -->
    <div class="card p-6 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-fortress-100 mb-1">New Access Request</h2>
          <p class="text-sm text-fortress-400">Submit a request for temporary elevated clearance</p>
        </div>
        <button
          @click="showModal = true"
          class="px-6 py-2 bg-secure hover:bg-secure-dark text-white rounded-lg font-medium transition-colors"
        >
          <svg class="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          New Request
        </button>
      </div>
    </div>

    <!-- Request Modal -->
    <RequestAccessModal
      v-if="showModal"
      :show="showModal"
      @close="showModal = false"
      @success="handleSuccess"
    />

    <!-- My Requests History -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-fortress-100">My Requests</h2>
        <button @click="loadMyRequests" class="text-secure hover:text-secure-light text-sm">
          <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <div v-if="loading" class="text-center py-8">
        <svg class="w-8 h-8 animate-spin mx-auto text-secure mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <p class="text-fortress-400">Loading requests...</p>
      </div>

      <div v-else-if="error" class="text-center py-8">
        <p class="text-alert mb-2">{{ error }}</p>
        <button @click="loadMyRequests" class="text-secure hover:text-secure-light text-sm">Try Again</button>
      </div>

      <div v-else-if="requests.length === 0" class="text-center py-8">
        <svg class="w-12 h-12 mx-auto text-fortress-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-fortress-400">No access requests yet</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="request in requests"
          :key="request.id"
          class="p-4 bg-fortress-800 border border-fortress-700 rounded-lg hover:border-fortress-600 transition-colors"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-fortress-200">
                  {{ request.override_type === 'org_wide' ? 'Organization-Wide' : 'Department' }}
                  Access
                </span>
                <span
                  :class="[
                    'text-xs px-2 py-0.5 rounded-full',
                    request.status === 'pending' ? 'bg-warning/20 text-warning' :
                    request.status === 'approved' ? 'bg-success/20 text-success' :
                    request.status === 'denied' ? 'bg-alert/20 text-alert' :
                    'bg-fortress-700 text-fortress-400'
                  ]"
                >
                  {{ request.status.toUpperCase() }}
                </span>
              </div>
              <p class="text-sm text-fortress-400 mb-2">{{ request.reason }}</p>
              <div class="flex items-center gap-4 text-xs text-fortress-500">
                <span>Level: {{ getPermissionLevelName(request.requested_permission_level) }}</span>
                <span>Duration: {{ request.requested_duration_hours }}h</span>
                <span>{{ formatDate(request.created_at) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="request.status === 'pending'"
                @click="cancelRequest(request.id)"
                class="px-3 py-1 text-xs bg-alert/10 text-alert hover:bg-alert/20 rounded transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
          
          <div v-if="request.approval_notes || request.denial_reason" class="mt-3 pt-3 border-t border-fortress-700">
            <p class="text-xs text-fortress-400">
              <span class="font-medium">Admin Note:</span>
              {{ request.approval_notes || request.denial_reason }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import RequestAccessModal from '@/components/admin/RequestAccessModal.vue'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const error = ref(null)
const requests = ref([])
const showModal = ref(false)

const permissionLevelNames = {
  1: 'General',
  2: 'Restricted',
  3: 'Confidential',
  4: 'Top Secret'
}

const getPermissionLevelName = (level) => permissionLevelNames[level] || 'Unknown'

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadMyRequests = async () => {
  loading.value = true
  error.value = null
  
  try {
    const result = await adminStore.fetchMyOverrideRequests()
    requests.value = result.requests || []
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load requests'
  } finally {
    loading.value = false
  }
}

const cancelRequest = async (requestId) => {
  if (!confirm('Are you sure you want to cancel this request?')) return
  
  try {
    const result = await adminStore.cancelOverrideRequest(requestId)
    if (result.success) {
      await loadMyRequests()
    } else {
      alert(result.error || 'Failed to cancel request')
    }
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to cancel request')
  }
}

const handleSuccess = () => {
  showModal.value = false
  loadMyRequests()
}

onMounted(() => {
  loadMyRequests()
})
</script>

<style scoped>
.card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.5) 100%);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.75rem;
}

.animate-fade-in {
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
