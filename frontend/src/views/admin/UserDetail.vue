```vue
<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 pb-4 border-b border-fortress-700">
      <div class="flex items-center gap-3">
        <router-link to="/access-control" class="text-fortress-400 hover:text-fortress-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </router-link>
        <h1 class="text-2xl font-bold text-fortress-100">User Details</h1>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="adminStore.isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-secure mx-auto mb-3"></div>
        <p class="text-fortress-400">Loading user details...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="adminStore.error" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-alert mb-4">{{ adminStore.error }}</p>
        <router-link to="/access-control" class="btn btn-primary">Back to Access Control</router-link>
      </div>
    </div>

    <!-- Content -->
    <div v-else-if="user" class="flex-1 overflow-auto">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left Column: Basic Info -->
        <div class="lg:col-span-2 space-y-6">
          <!-- User Information -->
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-fortress-100 mb-4">User Information</h2>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="text-xs uppercase text-fortress-500">Username</label>
                <p class="text-fortress-100 font-medium">{{ user.username }}</p>
              </div>
              <div>
                <label class="text-xs uppercase text-fortress-500">Email</label>
                <p class="text-fortress-100 font-medium">{{ user.email }}</p>
              </div>
              <div>
                <label class="text-xs uppercase text-fortress-500">First Name</label>
                <p class="text-fortress-100 font-medium">{{ user.first_name || '-' }}</p>
              </div>
              <div>
                <label class="text-xs uppercase text-fortress-500">Last Name</label>
                <p class="text-fortress-100 font-medium">{{ user.last_name || '-' }}</p>
              </div>
              <div class="col-span-2">
                <label class="text-xs uppercase text-fortress-500">Full Name</label>
                <p class="text-fortress-100 font-medium">{{ user.full_name || '-' }}</p>
              </div>
            </div>
          </div>

          <!-- Status Information -->
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-fortress-100 mb-4">Status</h2>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <label class="text-fortress-400">Active</label>
                <span :class="[
                  'px-3 py-1 rounded-full text-xs font-medium',
                  user.is_active 
                    ? 'bg-success/20 text-success' 
                    : 'bg-alert/20 text-alert'
                ]">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <label class="text-fortress-400">Verified</label>
                <span :class="[
                  'px-3 py-1 rounded-full text-xs font-medium',
                  user.is_verified 
                    ? 'bg-success/20 text-success' 
                    : 'bg-alert/20 text-alert'
                ]">
                  {{ user.is_verified ? 'Verified' : 'Not Verified' }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <label class="text-fortress-400">Suspended</label>
                <span :class="[
                  'px-3 py-1 rounded-full text-xs font-medium',
                  user.is_suspended 
                    ? 'bg-alert/20 text-alert' 
                    : 'bg-success/20 text-success'
                ]">
                  {{ user.is_suspended ? 'Suspended' : 'Active' }}
                </span>
              </div>
              <div v-if="user.suspension_reason" class="mt-3 p-3 bg-alert/10 border border-alert/30 rounded text-alert text-sm">
                <p class="font-semibold mb-1">Suspension Reason:</p>
                <p>{{ user.suspension_reason }}</p>
              </div>
            </div>
          </div>

          <!-- Roles -->
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-fortress-100 mb-4">Roles</h2>
            <div v-if="user.roles && user.roles.length > 0" class="space-y-2">
              <div
                v-for="role in user.roles"
                :key="role.id"
                class="p-3 bg-fortress-800/50 rounded-lg flex items-center justify-between"
              >
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-fortress-100">{{ role.name }}</span>
                    <span v-if="role.is_system" class="px-2 py-1 bg-secure/20 text-secure text-xs rounded">
                      System
                    </span>
                  </div>
                  <p class="text-sm text-fortress-400 mt-1">{{ role.description }}</p>
                </div>
                <button
                  @click="revokeRole(role.id)"
                  class="ml-2 p-2 hover:bg-alert/20 text-alert rounded transition-colors"
                  title="Revoke role"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div v-else class="text-fortress-400 text-sm">
              No roles assigned
            </div>
          </div>
        </div>

        <!-- Right Column: Actions -->
        <div class="space-y-4">
          <!-- Quick Actions -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-fortress-100 mb-4">Actions</h3>
            <div class="space-y-3">
              <button
                v-if="!user.is_suspended"
                @click="suspendUser"
                class="w-full px-4 py-2 bg-alert/20 hover:bg-alert/30 text-alert rounded-lg transition-colors text-sm font-medium"
              >
                Suspend User
              </button>
              <button
                v-else
                @click="unsuspendUser"
                class="w-full px-4 py-2 bg-success/20 hover:bg-success/30 text-success rounded-lg transition-colors text-sm font-medium"
              >
                Unsuspend User
              </button>
            </div>
          </div>

          <!-- Assign Role -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-fortress-100 mb-4">Assign Role</h3>
            <div class="space-y-3">
              <select
                v-model="selectedRoleToAssign"
                class="w-full input text-sm"
              >
                <option value="">Select a role...</option>
                <option
                  v-for="role in availableRoles"
                  :key="role.id"
                  :value="role.id"
                >
                  {{ role.name }}
                </option>
              </select>
              <button
                @click="assignRole"
                :disabled="!selectedRoleToAssign"
                class="w-full px-4 py-2 bg-secure hover:bg-secure/80 disabled:bg-fortress-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
              >
                Assign Role
              </button>
            </div>
          </div>

          <!-- Department Manager Roles -->
          <div class="card p-6">
            <h3 class="text-lg font-semibold text-fortress-100 mb-4">Manager Roles</h3>
            <div v-if="userManagedDepartments.length > 0" class="space-y-2">
              <div
                v-for="dept in userManagedDepartments"
                :key="dept.id"
                class="p-3 bg-fortress-800/50 rounded-lg flex items-center justify-between"
              >
                <div>
                  <div class="font-medium text-fortress-100">{{ dept.name }}</div>
                  <p class="text-xs text-fortress-400 mt-1">{{ dept.code }}</p>
                </div>
                <button
                  @click="removeManager(dept.id)"
                  class="ml-2 p-2 hover:bg-alert/20 text-alert rounded transition-colors"
                  title="Remove as manager"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div v-else class="text-fortress-400 text-sm">
              Not a manager of any departments
            </div>
            <div v-if="availableDepartments.length > 0" class="mt-4 pt-4 border-t border-fortress-700">
              <p class="text-xs uppercase text-fortress-500 mb-2">Add as Manager</p>
              <select
                v-model="selectedDeptToManage"
                class="w-full input text-sm mb-2"
              >
                <option value="">Select a department...</option>
                <option
                  v-for="dept in availableDepartments"
                  :key="dept.id"
                  :value="dept.id"
                >
                  {{ dept.name }}
                </option>
              </select>
              <button
                @click="setAsManager"
                :disabled="!selectedDeptToManage"
                class="w-full px-4 py-2 bg-secure hover:bg-secure/80 disabled:bg-fortress-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-sm font-medium"
              >
                Set as Manager
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <p class="text-fortress-400 mb-4">User not found</p>
        <router-link to="/access-control" class="btn btn-primary">Back to Access Control</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'
import api from '../../services/api'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const userId = parseInt(route.params.userId)
const selectedRoleToAssign = ref('')
const selectedDeptToManage = ref('')
const departments = ref([])
const userManagedDepartments = computed(() => {
  return departments.value.filter(d => d.manager_id === userId)
})
const availableDepartments = computed(() => {
  return departments.value.filter(d => d.manager_id !== userId)
})
const user = computed(() => adminStore.selectedUser)

const availableRoles = computed(() => {
  if (!adminStore.roles || !user.value) return []
  // Filter out roles that user already has
  const userRoleIds = new Set((user.value.roles || []).map(r => r.id))
  return adminStore.roles.filter(role => !userRoleIds.has(role.id))
})

async function loadUserDetails() {
  await adminStore.fetchUserDetails(userId)
  if (!adminStore.roles || adminStore.roles.length === 0) {
    await adminStore.fetchRoles()
  }
}

async function loadDepartments() {
  try {
    const response = await api.get('/v1/admin/departments')
    departments.value = response.departments || []
  } catch (err) {
    console.error('Failed to load departments:', err)
  }
}

async function assignRole() {
  if (!selectedRoleToAssign.value) return
  
  const result = await adminStore.assignRoleToUser(userId, selectedRoleToAssign.value)
  if (result.success) {
    await loadUserDetails()
    selectedRoleToAssign.value = ''
  }
}

async function revokeRole(roleId) {
  if (!confirm('Are you sure you want to revoke this role?')) return
  
  const result = await adminStore.revokeRoleFromUser(userId, roleId)
  if (result.success) {
    await loadUserDetails()
  }
}

async function setAsManager() {
  if (!selectedDeptToManage.value) return
  
  try {
    await api.post(`/v1/admin/departments/${selectedDeptToManage.value}/manager`, {
      user_id: userId
    })
    selectedDeptToManage.value = ''
    await loadDepartments()
  } catch (err) {
    console.error('Failed to set as manager:', err)
  }
}

async function removeManager(deptId) {
  if (!confirm('Are you sure you want to remove this user as manager?')) return
  
  try {
    await api.delete(`/v1/admin/departments/${deptId}/manager`)
    await loadDepartments()
  } catch (err) {
    console.error('Failed to remove manager:', err)
  }
}

async function suspendUser() {
  const reason = prompt('Enter suspension reason (optional):')
  if (reason === null) return
  
  const result = await adminStore.suspendUser(userId, reason)
  if (result.success) {
    await loadUserDetails()
  }
}

async function unsuspendUser() {
  if (!confirm('Are you sure you want to unsuspend this user?')) return
  
  const result = await adminStore.unsuspendUser(userId)
  if (result.success) {
    await loadUserDetails()
  }
}

onMounted(() => {
  loadUserDetails()
  loadDepartments()
})
</script>
```