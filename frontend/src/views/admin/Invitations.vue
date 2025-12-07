<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
      <div>
        <h1 class="text-3xl font-bold text-fortress-100">User Invitations</h1>
        <p class="text-fortress-400 mt-1">Manage pending and accepted invitations</p>
      </div>
      <button
        @click="showInviteModal = true"
        class="px-4 py-2 bg-secure text-white rounded-lg hover:bg-secure/90 transition-colors font-medium"
      >
        + Invite User
      </button>
    </div>

    <!-- Status Filters -->
    <div class="flex gap-3 flex-wrap">
      <button
        @click="statusFilter = null"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors',
          statusFilter === null
            ? 'bg-secure text-fortress-950'
            : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
        ]"
      >
        All Invitations
      </button>
      <button
        @click="statusFilter = 'pending'"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors',
          statusFilter === 'pending'
            ? 'bg-secure text-fortress-950'
            : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
        ]"
      >
        Pending
      </button>
      <button
        @click="statusFilter = 'accepted'"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors',
          statusFilter === 'accepted'
            ? 'bg-secure text-fortress-950'
            : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
        ]"
      >
        Accepted
      </button>
      <button
        @click="statusFilter = 'expired'"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors',
          statusFilter === 'expired'
            ? 'bg-alert text-fortress-950'
            : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
        ]"
      >
        Expired
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="text-center">
        <div class="inline-block w-12 h-12 mb-4 border-2 border-fortress-700 border-t-secure rounded-full animate-spin"></div>
        <p class="text-fortress-400">Loading invitations...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-alert/10 border border-alert/30 rounded-xl text-alert text-sm flex items-start gap-3">
      <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
      </svg>
      <div>
        <p class="font-medium">Error Loading Invitations</p>
        <p class="text-xs mt-1">{{ error }}</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="invitations.length === 0" class="text-center py-12 bg-fortress-900 rounded-xl border border-fortress-800">
      <svg class="w-12 h-12 text-fortress-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 12H9m4 5H8a4 4 0 00-4 4v2h16v-2a4 4 0 00-4-4z"/>
      </svg>
      <p class="text-fortress-400 font-medium">No invitations found</p>
      <p class="text-fortress-500 text-sm mt-1">Start by inviting users from the Users page</p>
    </div>

    <!-- Invitations Table -->
    <div v-else class="bg-fortress-900 rounded-xl border border-fortress-800 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-fortress-800 bg-fortress-950">
              <th class="px-6 py-4 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Email</th>
              <th class="px-6 py-4 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Role</th>
              <th class="px-6 py-4 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Status</th>
              <th class="px-6 py-4 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Invited By</th>
              <th class="px-6 py-4 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Expires</th>
              <th class="px-6 py-4 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-fortress-800">
            <tr v-for="invitation in invitations" :key="invitation.id" class="hover:bg-fortress-800/50 transition-colors">
              <!-- Email -->
              <td class="px-6 py-4">
                <div class="font-medium text-fortress-100">{{ invitation.email }}</div>
              </td>

              <!-- Role -->
              <td class="px-6 py-4">
                <span class="px-3 py-1 bg-secure/10 border border-secure/30 text-secure rounded-full text-xs font-medium">
                  {{ invitation.assigned_role || 'No role' }}
                </span>
              </td>

              <!-- Status -->
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <div v-if="invitation.status === 'pending' && !invitation.is_expired" class="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <div v-else-if="invitation.status === 'accepted'" class="w-2 h-2 bg-success rounded-full"></div>
                  <div v-else class="w-2 h-2 bg-alert rounded-full"></div>
                  <span :class="[
                    'text-xs font-medium',
                    invitation.status === 'pending' && !invitation.is_expired ? 'text-yellow-400' :
                    invitation.status === 'accepted' ? 'text-success' :
                    'text-alert'
                  ]">
                    {{ invitation.is_expired && invitation.status === 'pending' ? 'Expired' : invitation.status }}
                  </span>
                </div>
              </td>

              <!-- Invited By -->
              <td class="px-6 py-4">
                <div v-if="invitation.invited_by" class="text-sm">
                  <div class="font-medium text-fortress-100">{{ invitation.invited_by.username }}</div>
                  <div class="text-fortress-500 text-xs">{{ invitation.invited_by.full_name }}</div>
                </div>
                <div v-else class="text-fortress-500 text-sm">-</div>
              </td>

              <!-- Expires -->
              <td class="px-6 py-4">
                <div class="text-sm text-fortress-400">
                  {{ formatDate(invitation.expires_at) }}
                </div>
                <div v-if="invitation.status === 'accepted'" class="text-xs text-success mt-1">
                  Accepted {{ formatDate(invitation.accepted_at) }}
                </div>
              </td>

              <!-- Actions -->
              <td class="px-6 py-4">
                <div class="flex gap-2">
                  <button
                    v-if="invitation.status === 'pending' && !invitation.is_expired"
                    @click="resendInvitation(invitation.id)"
                    :disabled="resendingId === invitation.id"
                    class="px-3 py-1 bg-secure/20 border border-secure/30 text-secure rounded-lg hover:bg-secure/30 disabled:opacity-50 transition-colors text-xs font-medium"
                  >
                    <span v-if="resendingId === invitation.id">Sending...</span>
                    <span v-else>Resend</span>
                  </button>
                  <button
                    v-else-if="invitation.status === 'pending' && invitation.is_expired"
                    disabled
                    class="px-3 py-1 bg-fortress-800 text-fortress-500 rounded-lg text-xs font-medium cursor-not-allowed"
                  >
                    Expired
                  </button>
                  <button
                    v-else
                    disabled
                    class="px-3 py-1 bg-fortress-800 text-fortress-500 rounded-lg text-xs font-medium cursor-not-allowed"
                  >
                    -
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="invitations.length > 0" class="flex justify-between items-center py-4">
      <div class="text-sm text-fortress-400">
        Showing {{ offset + 1 }} to {{ Math.min(offset + limit, total) }} of {{ total }} invitations
      </div>
      <div class="flex gap-2">
        <button
          @click="previousPage"
          :disabled="offset === 0"
          class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 disabled:opacity-50 transition-colors"
        >
          Previous
        </button>
        <button
          @click="nextPage"
          :disabled="offset + limit >= total"
          class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 disabled:opacity-50 transition-colors"
        >
          Next
        </button>
      </div>
    </div>

    <!-- Invite Modal -->
    <UserInviteModal
      v-if="showInviteModal"
      :roles="roles"
      @invite="handleInviteUser"
      @close="showInviteModal = false"
    />

    <!-- Notification -->
    <div 
      v-if="notification.show" 
      :class="[
        'fixed bottom-4 right-4 p-4 rounded-lg text-sm transition-all z-40',
        notification.type === 'success'
          ? 'bg-secure/10 border border-secure/30 text-secure'
          : 'bg-alert/10 border border-alert/30 text-alert'
      ]"
    >
      {{ notification.message }}
      <button @click="notification.show = false" class="ml-2 hover:underline">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useAuthStore } from '../../stores/auth'
import UserInviteModal from '../../components/admin/UserInviteModal.vue'
import api from '../../services/api'

const adminStore = useAdminStore()
const authStore = useAuthStore()

const invitations = ref([])
const loading = ref(false)
const error = ref('')
const statusFilter = ref(null)
const limit = ref(10)
const offset = ref(0)
const total = ref(0)
const resendingId = ref(null)
const showInviteModal = ref(false)
const roles = ref([])
const notification = ref({
  show: false,
  type: 'success',
  message: ''
})

const loadInvitations = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const params = {
      limit: limit.value,
      offset: offset.value,
    }
    
    if (statusFilter.value) {
      params.status_filter = statusFilter.value
    }
    
    const response = await api.get('/v1/admin/invitations', { params })
    
    // Response is InvitationsListResponse with {total, limit, offset, invitations}
    invitations.value = response.invitations || []
    total.value = response.total || 0
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load invitations'
  } finally {
    loading.value = false
  }
}

const resendInvitation = async (invitationId) => {
  resendingId.value = invitationId

  try {
    // Provide the frontend signup link template to backend so emails use correct URL
    const baseUrl = window.location.origin
    const invitationLinkTemplate = `${baseUrl}/signup?token={token}`

    const response = await api.post(`/v1/admin/invitations/${invitationId}/resend`, {
      invitation_link_template: invitationLinkTemplate
    })

    if (response.message) {
      // Show success message
      notification.value = {
        show: true,
        type: 'success',
        message: response.message || `Invitation resent to ${invitationId}`
      }
      // Auto-hide notification after 3 seconds
      setTimeout(() => {
        notification.value.show = false
      }, 3000)

      await loadInvitations()
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to resend invitation'
  } finally {
    resendingId.value = null
  }
}

const previousPage = () => {
  if (offset.value >= limit.value) {
    offset.value -= limit.value
  }
}

const nextPage = () => {
  if (offset.value + limit.value < total.value) {
    offset.value += limit.value
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadRoles = async () => {
  // Only admins can fetch roles (managers don't have access to roles endpoint)
  if (authStore.isAdmin) {
    try {
      await adminStore.fetchRoles()
      roles.value = adminStore.roles
    } catch (err) {
      console.error('Failed to load roles:', err)
    }
  }
}

const handleInviteUser = async (inviteData) => {
  const result = await adminStore.inviteUser(
    inviteData.email, 
    inviteData.roleId,
    inviteData.invitationLinkTemplate,
    inviteData.invitationMessage,
    inviteData.departmentId,
    inviteData.isManager,
    inviteData.orgLevelPermission,
    inviteData.departmentLevelPermission
  )
  
  if (result.success) {
    notification.value = {
      show: true,
      type: 'success',
      message: `Invitation sent to ${inviteData.email}`
    }
    // Auto-hide notification after 3 seconds
    setTimeout(() => {
      notification.value.show = false
    }, 3000)
    showInviteModal.value = false
    // Reload invitations to show the new one
    offset.value = 0
    await loadInvitations()
  } else {
    notification.value = {
      show: true,
      type: 'error',
      message: result.error || 'Failed to send invitation'
    }
  }
}

watch(statusFilter, () => {
  offset.value = 0
  loadInvitations()
})

onMounted(() => {
  loadInvitations()
  loadRoles()
})
</script>
