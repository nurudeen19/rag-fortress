```vue
<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-fortress-900 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-fortress-700 sticky top-0 bg-fortress-900">
        <h2 class="text-xl font-bold text-fortress-100">User Details</h2>
        <button
          @click="$emit('close')"
          class="text-fortress-400 hover:text-fortress-100 transition-colors"
        >
          ✕
        </button>
      </div>

      <!-- Content -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secure mx-auto mb-2"></div>
          <p class="text-fortress-400">Loading user details...</p>
        </div>
      </div>

      <div v-else-if="user" class="p-6 space-y-6">
        <!-- User Info -->
        <div>
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">User Information</h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm text-fortress-400">Name</label>
              <p class="text-fortress-100">{{ user.full_name }}</p>
            </div>
            <div>
              <label class="text-sm text-fortress-400">Email</label>
              <p class="text-fortress-100">{{ user.email }}</p>
            </div>
            <div>
              <label class="text-sm text-fortress-400">Username</label>
              <p class="text-fortress-100">@{{ user.username }}</p>
            </div>
            <div>
              <label class="text-sm text-fortress-400">ID</label>
              <p class="text-fortress-100">#{{ user.id }}</p>
            </div>
          </div>
        </div>

        <!-- Account Status -->
        <div>
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Account Status</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-fortress-800/50 rounded">
              <span class="text-fortress-300">Active</span>
              <span :class="['px-3 py-1 rounded text-sm', user.is_active ? 'bg-success/20 text-success' : 'bg-alert/20 text-alert']">
                {{ user.is_active ? 'Yes' : 'No' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-fortress-800/50 rounded">
              <span class="text-fortress-300">Verified</span>
              <span :class="['px-3 py-1 rounded text-sm', user.is_verified ? 'bg-success/20 text-success' : 'bg-alert/20 text-alert']">
                {{ user.is_verified ? 'Yes' : 'No' }}
              </span>
            </div>
            <div class="flex items-center justify-between p-3 bg-fortress-800/50 rounded">
              <span class="text-fortress-300">Suspended</span>
              <span :class="['px-3 py-1 rounded text-sm', user.is_suspended ? 'bg-alert/20 text-alert' : 'bg-success/20 text-success']">
                {{ user.is_suspended ? 'Yes' : 'No' }}
              </span>
            </div>
            <div v-if="user.suspension_reason" class="p-3 bg-alert/10 border border-alert/30 rounded">
              <p class="text-sm text-fortress-400">Suspension Reason:</p>
              <p class="text-alert">{{ user.suspension_reason }}</p>
            </div>
          </div>
        </div>

        <!-- Roles -->
        <div>
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Roles</h3>
          <div v-if="userRoles.length > 0" class="space-y-2">
            <div
              v-for="role in userRoles"
              :key="role.id"
              class="flex items-center justify-between p-3 bg-fortress-800/50 rounded"
            >
              <div>
                <p class="text-fortress-100 font-medium">{{ role.name }}</p>
                <p class="text-sm text-fortress-400">{{ role.description }}</p>
              </div>
              <button
                @click="removeRole(role.id)"
                :disabled="operationLoading"
                class="text-alert hover:text-alert/80 disabled:opacity-50 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
          <p v-else class="text-fortress-400 text-sm">No roles assigned</p>

          <!-- Add Role -->
          <div class="mt-4 p-4 bg-fortress-800/50 rounded">
            <div class="flex gap-2">
              <select v-model="selectedRoleId" class="input flex-1">
                <option value="">Select a role to add...</option>
                <option
                  v-for="role in availableRoles"
                  :key="role.id"
                  :value="role.id"
                >
                  {{ role.name }}
                </option>
              </select>
              <button
                @click="addRole"
                :disabled="!selectedRoleId || operationLoading"
                class="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add
              </button>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div v-if="!user.is_system">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Actions</h3>
          <div class="space-y-2">
            <button
              v-if="!user.is_suspended"
              @click="suspendUserAction"
              :disabled="operationLoading"
              class="w-full btn bg-alert/20 text-alert hover:bg-alert/30 disabled:opacity-50"
            >
              {{ operationLoading ? 'Suspending...' : 'Suspend User' }}
            </button>
            <button
              v-else
              @click="unsuspendUserAction"
              :disabled="operationLoading"
              class="w-full btn bg-success/20 text-success hover:bg-success/30 disabled:opacity-50"
            >
              {{ operationLoading ? 'Unsuspending...' : 'Unsuspend User' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-fortress-700 flex justify-end gap-2 sticky bottom-0 bg-fortress-900">
        <button @click="$emit('close')" class="btn btn-secondary">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'

const props = defineProps({
  userId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['close', 'refresh'])

const adminStore = useAdminStore()
const loading = ref(false)
const operationLoading = ref(false)
const user = ref(null)
const userRoles = ref([])
const selectedRoleId = ref('')

const availableRoles = computed(() => {
  if (!userRoles.value) return adminStore.roles
  const assignedIds = new Set(userRoles.value.map(r => r.id))
  return adminStore.roles.filter(r => !assignedIds.has(r.id))
})

async function loadUserDetails() {
  loading.value = true
  try {
    const result = await adminStore.fetchUserDetails(props.userId)
    if (result.success) {
      user.value = result.user
      await loadUserRoles()
    }
  } finally {
    loading.value = false
  }
}

async function loadUserRoles() {
  const result = await adminStore.fetchUserRoles(props.userId)
  if (result.success) {
    userRoles.value = result.roles
  }
}

async function addRole() {
  if (!selectedRoleId.value) return

  operationLoading.value = true
  try {
    const result = await adminStore.assignRoleToUser(props.userId, parseInt(selectedRoleId.value))
    if (result.success) {
      await loadUserRoles()
      selectedRoleId.value = ''
    }
  } finally {
    operationLoading.value = false
  }
}

async function removeRole(roleId) {
  operationLoading.value = true
  try {
    const result = await adminStore.revokeRoleFromUser(props.userId, roleId)
    if (result.success) {
      await loadUserRoles()
    }
  } finally {
    operationLoading.value = false
  }
}

async function suspendUserAction() {
  operationLoading.value = true
  try {
    const result = await adminStore.suspendUser(props.userId)
    if (result.success) {
      await loadUserDetails()
    }
  } finally {
    operationLoading.value = false
  }
}

async function unsuspendUserAction() {
  operationLoading.value = true
  try {
    const result = await adminStore.unsuspendUser(props.userId)
    if (result.success) {
      await loadUserDetails()
    }
  } finally {
    operationLoading.value = false
  }
}

onMounted(() => {
  loadUserDetails()
})
</script>
```