<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
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
            Email Address
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
            Assign Role
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
import { ref } from 'vue'

const props = defineProps({
  roles: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['invite', 'close'])

const email = ref('')
const selectedRoleId = ref('')
const loading = ref(false)
const emailError = ref('')
const roleError = ref('')

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
    emit('invite', {
      email: email.value,
      roleId: parseInt(selectedRoleId.value)
    })
  } finally {
    loading.value = false
  }
}
</script>
