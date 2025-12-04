<template>
  <div class="min-h-screen bg-fortress-950">
    <div class="max-w-7xl mx-auto p-6">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-fortress-100 mb-2">Pending Override Requests</h1>
        <p class="text-fortress-400">Review and approve temporary clearance elevation requests</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="bg-fortress-900 rounded-lg border border-fortress-700 p-12 text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-secure mx-auto mb-4"></div>
        <p class="text-fortress-400">Loading requests...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="requests.length === 0" class="bg-fortress-900 rounded-lg border border-fortress-700 p-12 text-center">
        <svg class="w-16 h-16 text-fortress-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-fortress-300 font-medium mb-1">No Pending Requests</p>
        <p class="text-fortress-500 text-sm">All override requests have been processed</p>
      </div>

      <!-- Requests List -->
      <div v-else class="space-y-4">
        <div
          v-for="request in requests"
          :key="request.id"
          class="bg-fortress-900 rounded-lg border border-fortress-700 p-6 hover:border-fortress-600 transition-colors"
        >
          <div class="flex items-start justify-between gap-4">
            <!-- Request Info -->
            <div class="flex-1">
              <!-- Header -->
              <div class="flex items-start gap-3 mb-4">
                <div class="flex-shrink-0 w-10 h-10 rounded-full bg-fortress-800 flex items-center justify-center">
                  <svg class="w-5 h-5 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2">
                    <h3 class="text-lg font-semibold text-fortress-100">{{ request.user_name || 'Unknown User' }}</h3>
                    <span
                      :class="[
                        'px-2 py-0.5 text-xs font-medium rounded',
                        request.override_type === 'org_wide' 
                          ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                          : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      ]"
                    >
                      {{ request.override_type === 'org_wide' ? 'Organization-Wide' : 'Department' }}
                    </span>
                    <span
                      v-if="request.auto_escalated"
                      class="px-2 py-0.5 text-xs font-medium rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"
                    >
                      Escalated
                    </span>
                  </div>
                  <p class="text-sm text-fortress-400 mt-0.5">{{ request.user_email }}</p>
                </div>
              </div>

              <!-- Request Details Grid -->
              <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p class="text-xs text-fortress-500 mb-1">Requested Clearance</p>
                  <p class="text-sm font-medium text-fortress-200">{{ getLevelName(request.override_permission_level) }}</p>
                </div>
                <div>
                  <p class="text-xs text-fortress-500 mb-1">Duration</p>
                  <p class="text-sm font-medium text-fortress-200">{{ formatDuration(request.valid_from, request.valid_until) }}</p>
                </div>
                <div>
                  <p class="text-xs text-fortress-500 mb-1">Requested</p>
                  <p class="text-sm font-medium text-fortress-200">{{ formatDate(request.created_at) }}</p>
                </div>
                <div v-if="request.department_name">
                  <p class="text-xs text-fortress-500 mb-1">Department</p>
                  <p class="text-sm font-medium text-fortress-200">{{ request.department_name }}</p>
                </div>
              </div>

              <!-- Context (if available) -->
              <div v-if="request.trigger_query || request.trigger_file_id" class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-3 mb-4">
                <p class="text-xs font-medium text-fortress-400 mb-2">REQUEST CONTEXT</p>
                <p v-if="request.trigger_query" class="text-sm text-fortress-300 mb-1">
                  <span class="text-fortress-500">Query:</span> "{{ request.trigger_query }}"
                </p>
                <p v-if="request.trigger_file_id" class="text-sm text-fortress-300">
                  <span class="text-fortress-500">File ID:</span> {{ request.trigger_file_id }}
                </p>
              </div>

              <!-- Reason -->
              <div class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-3">
                <p class="text-xs font-medium text-fortress-400 mb-1">BUSINESS JUSTIFICATION</p>
                <p class="text-sm text-fortress-300">{{ request.reason }}</p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex-shrink-0 flex flex-col gap-2">
              <button
                @click="showApproveModal(request)"
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                :disabled="processing"
              >
                Approve
              </button>
              <button
                @click="showDenyModal(request)"
                class="px-4 py-2 bg-alert text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                :disabled="processing"
              >
                Deny
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Approve Confirmation Modal -->
    <div v-if="approveModalRequest" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
        <div class="p-6 border-b border-fortress-700">
          <h2 class="text-xl font-bold text-fortress-100">Approve Request</h2>
          <p class="text-sm text-fortress-400 mt-1">Confirm approval for {{ approveModalRequest.user_name }}</p>
        </div>
        <div class="p-6 space-y-4">
          <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <p class="text-sm text-green-300">
              This will grant <strong>{{ getLevelName(approveModalRequest.override_permission_level) }}</strong> clearance
              for <strong>{{ formatDuration(approveModalRequest.valid_from, approveModalRequest.valid_until) }}</strong>.
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">
              Approval Notes <span class="text-fortress-500 text-xs">(Optional)</span>
            </label>
            <textarea
              v-model="approvalNotes"
              placeholder="Add any notes or conditions..."
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
              rows="3"
              :disabled="processing"
            />
          </div>
          <p v-if="modalError" class="text-sm text-alert">{{ modalError }}</p>
        </div>
        <div class="p-6 border-t border-fortress-700 flex justify-end gap-3">
          <button
            @click="closeApproveModal"
            class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 transition-colors"
            :disabled="processing"
          >
            Cancel
          </button>
          <button
            @click="confirmApprove"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            :disabled="processing"
          >
            {{ processing ? 'Approving...' : 'Confirm Approval' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Deny Confirmation Modal -->
    <div v-if="denyModalRequest" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
        <div class="p-6 border-b border-fortress-700">
          <h2 class="text-xl font-bold text-fortress-100">Deny Request</h2>
          <p class="text-sm text-fortress-400 mt-1">Provide reason for denial to {{ denyModalRequest.user_name }}</p>
        </div>
        <div class="p-6 space-y-4">
          <div class="bg-alert/10 border border-alert/30 rounded-lg p-4">
            <p class="text-sm text-red-300">The requester will be notified of your decision and the reason provided.</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">
              Denial Reason <span class="text-alert">*</span>
            </label>
            <textarea
              v-model="denialReason"
              placeholder="Explain why this request is being denied..."
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
              rows="4"
              :disabled="processing"
            />
            <p class="text-xs text-fortress-400 mt-1">Minimum 10 characters</p>
          </div>
          <p v-if="modalError" class="text-sm text-alert">{{ modalError }}</p>
        </div>
        <div class="p-6 border-t border-fortress-700 flex justify-end gap-3">
          <button
            @click="closeDenyModal"
            class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 transition-colors"
            :disabled="processing"
          >
            Cancel
          </button>
          <button
            @click="confirmDeny"
            class="px-4 py-2 bg-alert text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            :disabled="processing || denialReason.length < 10"
          >
            {{ processing ? 'Denying...' : 'Confirm Denial' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'

const adminStore = useAdminStore()

const requests = ref([])
const loading = ref(false)
const processing = ref(false)

// Modal state
const approveModalRequest = ref(null)
const denyModalRequest = ref(null)
const approvalNotes = ref('')
const denialReason = ref('')
const modalError = ref('')

onMounted(async () => {
  await loadRequests()
})

async function loadRequests() {
  loading.value = true
  try {
    const result = await adminStore.fetchPendingOverrideRequests()
    if (result.success) {
      requests.value = result.requests
    }
  } finally {
    loading.value = false
  }
}

function showApproveModal(request) {
  approveModalRequest.value = request
  approvalNotes.value = ''
  modalError.value = ''
}

function closeApproveModal() {
  approveModalRequest.value = null
  approvalNotes.value = ''
  modalError.value = ''
}

async function confirmApprove() {
  if (!approveModalRequest.value) return

  processing.value = true
  modalError.value = ''

  try {
    const result = await adminStore.approveOverrideRequest(
      approveModalRequest.value.id,
      approvalNotes.value || null
    )

    if (result.success) {
      // Remove from list
      requests.value = requests.value.filter(r => r.id !== approveModalRequest.value.id)
      closeApproveModal()
    } else {
      modalError.value = result.error || 'Failed to approve request'
    }
  } finally {
    processing.value = false
  }
}

function showDenyModal(request) {
  denyModalRequest.value = request
  denialReason.value = ''
  modalError.value = ''
}

function closeDenyModal() {
  denyModalRequest.value = null
  denialReason.value = ''
  modalError.value = ''
}

async function confirmDeny() {
  if (!denyModalRequest.value || denialReason.value.length < 10) {
    modalError.value = 'Please provide a reason (minimum 10 characters)'
    return
  }

  processing.value = true
  modalError.value = ''

  try {
    const result = await adminStore.denyOverrideRequest(
      denyModalRequest.value.id,
      denialReason.value
    )

    if (result.success) {
      // Remove from list
      requests.value = requests.value.filter(r => r.id !== denyModalRequest.value.id)
      closeDenyModal()
    } else {
      modalError.value = result.error || 'Failed to deny request'
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
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
}
</script>
