<template>
  <div class="min-h-screen bg-fortress-950">
    <div class="max-w-7xl mx-auto p-6">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-fortress-100 mb-2">My Override Requests</h1>
        <p class="text-fortress-400">View and manage your clearance elevation requests</p>
      </div>

      <!-- Filters -->
      <div class="bg-fortress-900 rounded-lg border border-fortress-700 p-4 mb-6">
        <div class="flex items-center gap-4">
          <label class="text-sm font-medium text-fortress-300">Filter by status:</label>
          <div class="flex gap-2">
            <button
              v-for="status in statusFilters"
              :key="status.value"
              @click="selectedStatus = status.value"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                selectedStatus === status.value
                  ? 'bg-secure text-white'
                  : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
              ]"
            >
              {{ status.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="bg-fortress-900 rounded-lg border border-fortress-700 p-12 text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-secure mx-auto mb-4"></div>
        <p class="text-fortress-400">Loading requests...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredRequests.length === 0" class="bg-fortress-900 rounded-lg border border-fortress-700 p-12 text-center">
        <svg class="w-16 h-16 text-fortress-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-fortress-300 font-medium mb-1">No Requests Found</p>
        <p class="text-fortress-500 text-sm">
          {{ selectedStatus ? 'No requests with this status' : 'You haven\'t made any override requests yet' }}
        </p>
      </div>

      <!-- Requests List -->
      <div v-else class="space-y-4">
        <div
          v-for="request in filteredRequests"
          :key="request.id"
          class="bg-fortress-900 rounded-lg border border-fortress-700 p-6"
        >
          <div class="flex items-start justify-between gap-4">
            <!-- Request Info -->
            <div class="flex-1">
              <!-- Header with Status -->
              <div class="flex items-start justify-between mb-4">
                <div>
                  <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-lg font-semibold text-fortress-100">
                      {{ getLevelName(request.override_permission_level) }}
                    </h3>
                    <span
                      :class="[
                        'px-2 py-0.5 text-xs font-medium rounded',
                        request.override_type === 'org_wide' 
                          ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                          : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      ]"
                    >
                      {{ request.override_type === 'org_wide' ? 'Org-Wide' : 'Department' }}
                    </span>
                  </div>
                  <p class="text-sm text-fortress-400">Requested {{ formatDate(request.created_at) }}</p>
                </div>
                <span
                  :class="[
                    'px-3 py-1 text-sm font-medium rounded-lg',
                    getStatusClass(request.status)
                  ]"
                >
                  {{ getStatusLabel(request.status) }}
                </span>
              </div>

              <!-- Details Grid -->
              <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p class="text-xs text-fortress-500 mb-1">Duration</p>
                  <p class="text-sm font-medium text-fortress-200">{{ formatDuration(request.valid_from, request.valid_until) }}</p>
                </div>
                <div v-if="request.department_name">
                  <p class="text-xs text-fortress-500 mb-1">Department</p>
                  <p class="text-sm font-medium text-fortress-200">{{ request.department_name }}</p>
                </div>
                <div v-if="request.approver_name">
                  <p class="text-xs text-fortress-500 mb-1">{{ request.status === 'approved' ? 'Approved By' : 'Reviewed By' }}</p>
                  <p class="text-sm font-medium text-fortress-200">{{ request.approver_name }}</p>
                </div>
                <div v-if="request.decided_at">
                  <p class="text-xs text-fortress-500 mb-1">Decision Date</p>
                  <p class="text-sm font-medium text-fortress-200">{{ formatDate(request.decided_at) }}</p>
                </div>
              </div>

              <!-- Context (if available) -->
              <div v-if="request.trigger_query" class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-3 mb-3">
                <p class="text-xs font-medium text-fortress-400 mb-1">CONTEXT</p>
                <p class="text-sm text-fortress-300">{{ request.trigger_query }}</p>
              </div>

              <!-- Reason -->
              <div class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-3 mb-3">
                <p class="text-xs font-medium text-fortress-400 mb-1">YOUR JUSTIFICATION</p>
                <p class="text-sm text-fortress-300">{{ request.reason }}</p>
              </div>

              <!-- Approval/Denial Notes -->
              <div v-if="request.approval_notes" class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-3">
                <p class="text-xs font-medium text-fortress-400 mb-1">
                  {{ request.status === 'approved' ? 'APPROVAL NOTES' : 'DENIAL REASON' }}
                </p>
                <p class="text-sm text-fortress-300">{{ request.approval_notes }}</p>
              </div>

              <!-- Expiry Warning (for approved, active requests) -->
              <div v-if="request.status === 'approved' && request.is_active" class="mt-3">
                <div v-if="isExpiringSoon(request.valid_until)" class="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                  <p class="text-sm text-yellow-300">
                    <strong>Expiring soon:</strong> This override will expire {{ formatDate(request.valid_until) }}
                  </p>
                </div>
                <div v-else class="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                  <p class="text-sm text-green-300">
                    <strong>Active:</strong> Valid until {{ formatDate(request.valid_until) }}
                  </p>
                </div>
              </div>

              <!-- Escalation Notice -->
              <div v-if="request.auto_escalated" class="mt-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                <p class="text-sm text-yellow-300">
                  <strong>Escalated:</strong> This request was escalated to administrators on {{ formatDate(request.escalated_at) }}
                </p>
              </div>
            </div>

            <!-- Actions (only for pending) -->
            <div v-if="request.status === 'pending'" class="flex-shrink-0">
              <button
                @click="showCancelModal(request)"
                class="px-4 py-2 bg-alert text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                :disabled="processing"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cancel Confirmation Modal -->
    <div v-if="cancelModalRequest" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
        <div class="p-6 border-b border-fortress-700">
          <h2 class="text-xl font-bold text-fortress-100">Cancel Request</h2>
          <p class="text-sm text-fortress-400 mt-1">Are you sure you want to cancel this request?</p>
        </div>
        <div class="p-6 space-y-4">
          <div class="bg-alert/10 border border-alert/30 rounded-lg p-4">
            <p class="text-sm text-red-300">
              This action cannot be undone. You'll need to submit a new request if you still need elevated access.
            </p>
          </div>
          <p v-if="modalError" class="text-sm text-alert">{{ modalError }}</p>
        </div>
        <div class="p-6 border-t border-fortress-700 flex justify-end gap-3">
          <button
            @click="closeCancelModal"
            class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 transition-colors"
            :disabled="processing"
          >
            Keep Request
          </button>
          <button
            @click="confirmCancel"
            class="px-4 py-2 bg-alert text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            :disabled="processing"
          >
            {{ processing ? 'Cancelling...' : 'Cancel Request' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()

const requests = ref([])
const loading = ref(false)
const processing = ref(false)
const selectedStatus = ref(null)

// Modal state
const cancelModalRequest = ref(null)
const modalError = ref('')

const statusFilters = [
  { value: null, label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'denied', label: 'Denied' }
]

const filteredRequests = computed(() => {
  if (!selectedStatus.value) return requests.value
  return requests.value.filter(r => r.status === selectedStatus.value)
})

onMounted(async () => {
  await loadRequests()
})

watch(selectedStatus, async () => {
  await loadRequests()
})

async function loadRequests() {
  loading.value = true
  try {
    const result = await adminStore.fetchMyOverrideRequests(selectedStatus.value)
    if (result.success) {
      requests.value = result.requests
    }
  } finally {
    loading.value = false
  }
}

function showCancelModal(request) {
  cancelModalRequest.value = request
  modalError.value = ''
}

function closeCancelModal() {
  cancelModalRequest.value = null
  modalError.value = ''
}

async function confirmCancel() {
  if (!cancelModalRequest.value) return

  processing.value = true
  modalError.value = ''

  try {
    const result = await adminStore.cancelOverrideRequest(cancelModalRequest.value.id)

    if (result.success) {
      // Remove from list
      requests.value = requests.value.filter(r => r.id !== cancelModalRequest.value.id)
      closeCancelModal()
    } else {
      modalError.value = result.error || 'Failed to cancel request'
    }
  } finally {
    processing.value = false
  }
}

function getLevelName(level) {
  const levels = {
    1: 'Level 1 - General',
    2: 'Level 2 - Confidential',
    3: 'Level 3 - Highly Confidential',
    4: 'Level 4 - Top Secret'
  }
  return levels[level] || `Level ${level}`
}

function getStatusLabel(status) {
  const labels = {
    pending: 'Pending Review',
    approved: 'Approved',
    denied: 'Denied',
    expired: 'Expired',
    revoked: 'Revoked'
  }
  return labels[status] || status
}

function getStatusClass(status) {
  const classes = {
    pending: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
    approved: 'bg-green-500/20 text-green-300 border border-green-500/30',
    denied: 'bg-red-500/20 text-red-300 border border-red-500/30',
    expired: 'bg-fortress-700 text-fortress-400 border border-fortress-600',
    revoked: 'bg-fortress-700 text-fortress-400 border border-fortress-600'
  }
  return classes[status] || 'bg-fortress-700 text-fortress-400'
}

function formatDuration(validFrom, validUntil) {
  const start = new Date(validFrom)
  const end = new Date(validUntil)
  const hours = Math.round((end - start) / (1000 * 60 * 60))
  
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''}`
  const days = Math.round(hours / 24)
  return `${days} day${days !== 1 ? 's' : ''}`
}

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
  
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
}

function isExpiringSoon(validUntil) {
  const expiry = new Date(validUntil)
  const now = new Date()
  const hoursUntilExpiry = (expiry - now) / (1000 * 60 * 60)
  return hoursUntilExpiry <= 24 && hoursUntilExpiry > 0
}
</script>
