<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="p-6 border-b border-fortress-700">
        <h2 class="text-xl font-bold text-fortress-100">Invite New User</h2>
        <p class="text-sm text-fortress-400 mt-1">Send an invitation link to join the platform</p>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-4">
        <!-- Email Field -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Email Address <span class="text-alert">*</span>
          </label>
          <input
            v-model="email"
            type="email"
            placeholder="user@example.com"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
            :disabled="loading"
          />
          <p v-if="emailError" class="text-alert text-xs mt-1">{{ emailError }}</p>
        </div>

        <!-- Role Selection -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Assign Role <span class="text-alert">*</span>
          </label>
          <select
            v-model="selectedRoleId"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
            :disabled="loading"
          >
            <option value="">Select a role...</option>
            <option
              v-for="role in roles"
              :key="role.id"
              :value="role.id"
            >
              {{ role.name }}
            </option>
          </select>
          <p v-if="roleError" class="text-alert text-xs mt-1">{{ roleError }}</p>
        </div>

        <!-- Department Selection (Optional) -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Assign to Department <span class="text-fortress-500 text-xs">(Optional)</span>
          </label>
          <select
            v-model="selectedDepartmentId"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
            :disabled="loading || departmentsLoading"
          >
            <option value="">No department</option>
            <option
              v-for="dept in departments"
              :key="dept.id"
              :value="dept.id"
            >
              {{ dept.name }}
            </option>
          </select>
          <p v-if="departmentsLoading" class="text-fortress-400 text-xs mt-1">Loading departments...</p>
        </div>

        <!-- Manager Checkbox -->
        <div class="flex items-center gap-3">
          <input
            v-model="isManager"
            type="checkbox"
            id="manager-checkbox"
            class="w-4 h-4 rounded border-fortress-600 bg-fortress-800 text-secure focus:ring-secure cursor-pointer"
            :disabled="loading || !selectedDepartmentId"
          />
          <label for="manager-checkbox" class="text-sm text-fortress-300 cursor-pointer" :class="{ 'opacity-50': !selectedDepartmentId }">
            Make this user a manager of the assigned department
          </label>
        </div>

        <!-- Message Field (Optional) -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Custom Message <span class="text-fortress-500 text-xs">(Optional)</span>
          </label>
          <textarea
            v-model="invitationMessage"
            placeholder="Add a personal message to include in the invitation email..."
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
            rows="3"
            :disabled="loading"
            maxlength="500"
          />
          <p class="text-fortress-400 text-xs mt-1">{{ invitationMessage.length }}/500</p>
        </div>

        <!-- Info -->
        <div class="bg-secure/10 border border-secure/30 rounded-lg p-3">
          <p class="text-xs text-fortress-300">
            An invitation email will be sent to the user. They'll have 7 days to accept and set their password.
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-fortress-700 flex justify-end gap-2">
        <button
          @click="$emit('close')"
          :disabled="loading"
          class="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          @click="handleInvite"
          :disabled="!email || !selectedRoleId || loading"
          class="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Sending...' : 'Send Invite' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const props = defineProps({
  roles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['invite', 'close'])

const email = ref('')
const selectedRoleId = ref('')
const selectedDepartmentId = ref('')
const isManager = ref(false)
const invitationMessage = ref('')
const loading = ref(false)
const departmentsLoading = ref(false)
const departments = ref([])
const emailError = ref('')
const roleError = ref('')

// Load departments on mount
onMounted(async () => {
  await loadDepartments()
})

async function loadDepartments() {
  departmentsLoading.value = true
  try {
    const response = await api.get('/v1/admin/departments')
    departments.value = response.departments || []
  } catch (err) {
    console.error('Failed to load departments:', err)
    departments.value = []
  } finally {
    departmentsLoading.value = false
  }
}

function validateForm() {
  emailError.value = ''
  roleError.value = ''

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email.value)) {
    emailError.value = 'Please enter a valid email address'
    return false
  }

  if (!selectedRoleId.value) {
    roleError.value = 'Please select a role'
    return false
  }

  return true
}

async function handleInvite() {
  if (!validateForm()) return

  loading.value = true
  try {
    // Build the frontend signup URL with token placeholder
    const baseUrl = window.location.origin
    const invitationLinkTemplate = `${baseUrl}/signup?token={token}`
    
    emit('invite', {
      email: email.value,
      roleId: parseInt(selectedRoleId.value),
      invitationLinkTemplate,
      invitationMessage: invitationMessage.value || null,
      departmentId: selectedDepartmentId.value ? parseInt(selectedDepartmentId.value) : null,
      isManager: isManager.value && !!selectedDepartmentId.value
    })
    
    // Reset form
    email.value = ''
    selectedRoleId.value = ''
    selectedDepartmentId.value = ''
    isManager.value = false
    invitationMessage.value = ''
  } finally {
    loading.value = false
  }
}
</script>

