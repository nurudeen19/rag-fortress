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
            :disabled="loading || departmentsLoading || (invitationLimits?.is_department_manager && !invitationLimits?.is_admin)"
          >
            <option value="">No department</option>
            <option
              v-for="dept in availableDepartments"
              :key="dept.id"
              :value="dept.id"
            >
              {{ dept.name }}
            </option>
          </select>
          <p v-if="departmentsLoading || limitsLoading" class="text-fortress-400 text-xs mt-1">Loading...</p>
          <p v-else-if="invitationLimits?.is_department_manager && !invitationLimits?.is_admin" class="text-fortress-400 text-xs mt-1">
            As a department manager, you can only invite to your own department
          </p>
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

        <!-- Organization Clearance Level -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Organization Clearance Level <span class="text-alert">*</span>
          </label>
          <select
            v-model="orgLevelPermission"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
            :disabled="loading || limitsLoading"
          >
            <option
              v-for="level in availableOrgLevels"
              :key="level.value"
              :value="level.value"
            >
              {{ level.label }}
            </option>
          </select>
          <p class="text-fortress-400 text-xs mt-1">
            Organization-wide security clearance level
          </p>
        </div>

        <!-- Department Clearance Level (if department selected) -->
        <div v-if="selectedDepartmentId">
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Department Clearance Level <span class="text-fortress-500 text-xs">(Optional)</span>
          </label>
          <select
            v-model="deptLevelPermission"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
            :disabled="loading || limitsLoading"
          >
            <option :value="null">No department clearance</option>
            <option
              v-for="level in availableDeptLevels"
              :key="level.value"
              :value="level.value"
            >
              {{ level.label }}
            </option>
          </select>
          <p class="text-fortress-400 text-xs mt-1">
            Department-specific security clearance level
          </p>
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
import { ref, onMounted, computed } from 'vue'
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
const limitsLoading = ref(false)
const departments = ref([])
const emailError = ref('')
const roleError = ref('')

// Clearance fields
const orgLevelPermission = ref(1)
const deptLevelPermission = ref(null)
const invitationLimits = ref(null)

// Computed: Available clearance levels based on user's limits
const availableOrgLevels = computed(() => {
  if (!invitationLimits.value) return []
  
  const maxLevel = invitationLimits.value.max_org_clearance
  return invitationLimits.value.clearance_levels.filter(level => level.value <= maxLevel)
})

const availableDeptLevels = computed(() => {
  if (!invitationLimits.value || !invitationLimits.value.max_dept_clearance) return []
  
  const maxLevel = invitationLimits.value.max_dept_clearance
  return invitationLimits.value.clearance_levels.filter(level => level.value <= maxLevel)
})

// Filter departments based on invitation limits
const availableDepartments = computed(() => {
  if (!invitationLimits.value) return departments.value
  
  // If admin, return all departments
  if (invitationLimits.value.is_admin) return departments.value
  
  // If department manager, filter to allowed departments only
  const allowedIds = invitationLimits.value.allowed_departments
  if (!allowedIds) return departments.value
  
  return departments.value.filter(dept => allowedIds.includes(dept.id))
})

// Load departments and limits on mount
onMounted(async () => {
  await Promise.all([
    loadDepartments(),
    loadInvitationLimits()
  ])
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

async function loadInvitationLimits() {
  limitsLoading.value = true
  try {
    const response = await api.get('/v1/admin/users/me/invitation-limits')
    invitationLimits.value = response
    
    // Set default org clearance to user's max if available
    if (response.max_org_clearance) {
      orgLevelPermission.value = Math.min(1, response.max_org_clearance)
    }
    
    // If user is department manager (not admin), auto-select their department
    if (response.is_department_manager && !response.is_admin && response.allowed_departments?.length === 1) {
      selectedDepartmentId.value = response.allowed_departments[0].toString()
    }
  } catch (err) {
    console.error('Failed to load invitation limits:', err)
    invitationLimits.value = null
  } finally {
    limitsLoading.value = false
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
      isManager: isManager.value && !!selectedDepartmentId.value,
      orgLevelPermission: parseInt(orgLevelPermission.value),
      departmentLevelPermission: deptLevelPermission.value ? parseInt(deptLevelPermission.value) : null
    })
    
    // Reset form
    email.value = ''
    selectedRoleId.value = ''
    selectedDepartmentId.value = ''
    isManager.value = false
    invitationMessage.value = ''
    orgLevelPermission.value = 1
    deptLevelPermission.value = null
  } finally {
    loading.value = false
  }
}
</script>

