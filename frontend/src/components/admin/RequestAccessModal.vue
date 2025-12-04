<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-fortress-900 rounded-lg max-w-lg w-full border border-fortress-700 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="p-6 border-b border-fortress-700">
        <h2 class="text-xl font-bold text-fortress-100">Request Access</h2>
        <p class="text-sm text-fortress-400 mt-1">Request temporary elevated clearance to access restricted content</p>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-4">
        <!-- Context Display -->
        <div v-if="triggerQuery || triggerFileName" class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-4">
          <p class="text-xs font-medium text-fortress-400 mb-2">REQUEST CONTEXT</p>
          <p v-if="triggerQuery" class="text-sm text-fortress-300 mb-2">
            <span class="text-fortress-500">Query:</span> "{{ triggerQuery }}"
          </p>
          <p v-if="triggerFileName" class="text-sm text-fortress-300">
            <span class="text-fortress-500">File:</span> {{ triggerFileName }}
          </p>
        </div>

        <!-- Current Clearance -->
        <div class="bg-fortress-800/50 border border-fortress-700 rounded-lg p-4">
          <p class="text-xs font-medium text-fortress-400 mb-2">YOUR CURRENT CLEARANCE</p>
          <div class="flex gap-4">
            <div>
              <p class="text-xs text-fortress-500">Organization</p>
              <p class="text-sm font-medium text-fortress-200">{{ currentOrgLevel }}</p>
            </div>
            <div v-if="currentDeptLevel">
              <p class="text-xs text-fortress-500">Department</p>
              <p class="text-sm font-medium text-fortress-200">{{ currentDeptLevel }}</p>
            </div>
          </div>
        </div>

        <!-- Override Type -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Request Type <span class="text-alert">*</span>
          </label>
          <div class="space-y-2">
            <label class="flex items-start gap-3 p-3 bg-fortress-800 border border-fortress-700 rounded-lg cursor-pointer hover:border-fortress-600 transition-colors">
              <input
                v-model="overrideType"
                type="radio"
                value="department"
                class="mt-0.5 w-4 h-4 border-fortress-600 bg-fortress-800 text-secure focus:ring-secure cursor-pointer"
                :disabled="loading || !hasDepartment"
              />
              <div class="flex-1">
                <p class="text-sm font-medium text-fortress-200">Department Access</p>
                <p class="text-xs text-fortress-400 mt-0.5">Request elevated clearance for your department only</p>
                <p v-if="!hasDepartment" class="text-xs text-alert mt-1">You must be assigned to a department</p>
              </div>
            </label>
            <label class="flex items-start gap-3 p-3 bg-fortress-800 border border-fortress-700 rounded-lg cursor-pointer hover:border-fortress-600 transition-colors">
              <input
                v-model="overrideType"
                type="radio"
                value="org_wide"
                class="mt-0.5 w-4 h-4 border-fortress-600 bg-fortress-800 text-secure focus:ring-secure cursor-pointer"
                :disabled="loading"
              />
              <div class="flex-1">
                <p class="text-sm font-medium text-fortress-200">Organization-Wide Access</p>
                <p class="text-xs text-fortress-400 mt-0.5">Request elevated clearance across the entire organization</p>
              </div>
            </label>
          </div>
        </div>

        <!-- Requested Clearance Level -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Requested Clearance Level <span class="text-alert">*</span>
          </label>
          <select
            v-model="requestedLevel"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
            :disabled="loading"
          >
            <option value="">Select level...</option>
            <option
              v-for="level in availableLevels"
              :key="level.value"
              :value="level.value"
            >
              {{ level.label }}
            </option>
          </select>
          <p v-if="suggestedLevel" class="text-xs text-fortress-400 mt-1">
            <span class="text-secure">Suggested:</span> {{ suggestedLevel }}
          </p>
        </div>

        <!-- Duration -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Access Duration <span class="text-alert">*</span>
          </label>
          <select
            v-model="durationHours"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
            :disabled="loading"
          >
            <option value="">Select duration...</option>
            <option :value="1">1 hour</option>
            <option :value="4">4 hours</option>
            <option :value="8">8 hours (1 work day)</option>
            <option :value="24">24 hours (1 day)</option>
            <option :value="72">72 hours (3 days)</option>
            <option :value="168">168 hours (1 week - maximum)</option>
          </select>
          <p class="text-xs text-fortress-400 mt-1">How long you need elevated access</p>
        </div>

        <!-- Reason -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Business Justification <span class="text-alert">*</span>
          </label>
          <textarea
            v-model="reason"
            placeholder="Explain why you need this elevated access and how it relates to your work..."
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
            rows="4"
            :disabled="loading"
            maxlength="500"
          />
          <div class="flex justify-between items-center mt-1">
            <p v-if="reasonError" class="text-alert text-xs">{{ reasonError }}</p>
            <p class="text-fortress-400 text-xs ml-auto">{{ reason.length }}/500 (min 20 characters)</p>
          </div>
        </div>

        <!-- Approval Info -->
        <div class="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div class="flex gap-3">
            <svg class="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-blue-300">Approval Required</p>
              <p class="text-xs text-blue-200/80 mt-1">
                {{ approvalMessage }}
              </p>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="bg-alert/10 border border-alert/30 rounded-lg p-4">
          <p class="text-sm text-alert">{{ errorMessage }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <p class="text-sm text-green-400">{{ successMessage }}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-fortress-700 flex justify-end gap-3">
        <button
          @click="handleCancel"
          class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 transition-colors"
          :disabled="loading"
        >
          Cancel
        </button>
        <button
          @click="handleSubmit"
          class="px-4 py-2 bg-secure text-white rounded-lg hover:bg-secure-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading || !isFormValid"
        >
          {{ loading ? 'Submitting...' : 'Submit Request' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  triggerQuery: {
    type: String,
    default: null
  },
  triggerFileId: {
    type: Number,
    default: null
  },
  triggerFileName: {
    type: String,
    default: null
  },
  suggestedLevel: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['close', 'success'])

const adminStore = useAdminStore()
const authStore = useAuthStore()

// Form state
const overrideType = ref('department')
const requestedLevel = ref('')
const durationHours = ref('')
const reason = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const reasonError = ref('')

// User info
const currentUser = computed(() => authStore.user)
const currentOrgLevel = computed(() => currentUser.value?.security_level || 'GENERAL')
const currentDeptLevel = computed(() => currentUser.value?.department_security_level || null)
const hasDepartment = computed(() => !!currentUser.value?.department_id)

// Available levels (1-4)
const availableLevels = [
  { value: 1, label: 'Level 1 - General' },
  { value: 2, label: 'Level 2 - Confidential' },
  { value: 3, label: 'Level 3 - Highly Confidential' },
  { value: 4, label: 'Level 4 - Top Secret' }
]

// Approval message based on override type
const approvalMessage = computed(() => {
  if (overrideType.value === 'department') {
    return 'Your department manager will review this request. If not reviewed within 24 hours, it will be escalated to administrators.'
  }
  return 'An administrator will review this request.'
})

// Form validation
const isFormValid = computed(() => {
  return (
    overrideType.value &&
    requestedLevel.value &&
    durationHours.value &&
    reason.value.length >= 20 &&
    (overrideType.value !== 'department' || hasDepartment.value)
  )
})

// Reset on override type change
function handleCancel() {
  emit('close')
}

async function handleSubmit() {
  // Validate
  if (!isFormValid.value) {
    errorMessage.value = 'Please fill in all required fields'
    return
  }

  if (reason.value.length < 20) {
    reasonError.value = 'Reason must be at least 20 characters'
    return
  }

  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  reasonError.value = ''

  try {
    const requestData = {
      override_type: overrideType.value,
      requested_permission_level: parseInt(requestedLevel.value),
      requested_duration_hours: parseInt(durationHours.value),
      reason: reason.value,
      department_id: overrideType.value === 'department' ? currentUser.value?.department_id : null,
      trigger_query: props.triggerQuery,
      trigger_file_id: props.triggerFileId
    }

    const result = await adminStore.createOverrideRequest(requestData)

    if (result.success) {
      successMessage.value = 'Your request has been submitted successfully!'
      
      // Wait a moment to show success message
      setTimeout(() => {
        emit('success', result.request)
        emit('close')
      }, 1500)
    } else {
      errorMessage.value = result.error || 'Failed to submit request'
    }
  } catch (err) {
    console.error('Error submitting override request:', err)
    errorMessage.value = 'An unexpected error occurred. Please try again.'
  } finally {
    loading.value = false
  }
}

// Initialize department override if user has department
onMounted(() => {
  if (!hasDepartment.value) {
    overrideType.value = 'org_wide'
  }
})
</script>

<style scoped>
/* Custom radio button styles */
input[type="radio"]:checked {
  background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3ccircle cx='8' cy='8' r='3'/%3e%3c/svg%3e");
}
</style>
