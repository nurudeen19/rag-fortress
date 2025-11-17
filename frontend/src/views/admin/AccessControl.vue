<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-fortress-100">Access Control</h1>
      <div class="flex gap-2">
        <button
          @click="activeTab = 'users'"
          :class="[
            'px-4 py-2 rounded-lg transition-colors',
            activeTab === 'users'
              ? 'bg-secure text-white'
              : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
          ]"
        >
          Users
        </button>
        <button
          @click="activeTab = 'roles'"
          :class="[
            'px-4 py-2 rounded-lg transition-colors',
            activeTab === 'roles'
              ? 'bg-secure text-white'
              : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'
          ]"
        >
          Roles
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="adminStore.error" class="mb-4 p-4 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
      {{ adminStore.error }}
      <button @click="adminStore.clearError()" class="ml-2 hover:underline">×</button>
    </div>

    <!-- Users Tab -->
    <div v-if="activeTab === 'users'" class="flex-1 flex flex-col gap-4">
      <!-- Header with Filters and Actions -->
      <div class="flex gap-2 items-center justify-between">
        <div class="flex gap-2 items-center flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search users..."
            class="input flex-1"
            @keyup.enter="handleSearch"
          />
          <button @click="handleSearch" class="btn btn-primary">Search</button>
          <button @click="resetFilters" class="btn btn-secondary">Reset</button>
        </div>
        <button @click="showInviteModal = true" class="btn btn-primary">
          + Invite User
        </button>
      </div>

      <!-- Users Table -->
      <div v-if="!adminStore.isLoading" class="flex-1 card overflow-hidden flex flex-col">
        <div v-if="adminStore.users.length === 0" class="text-center py-8 text-fortress-400">
          No users found
        </div>

        <div v-else class="overflow-x-auto flex-1">
          <table class="w-full">
            <thead class="sticky top-0 bg-fortress-800 border-b border-fortress-700">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Name</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Email</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-fortress-300 uppercase tracking-wider">Verified</th>
                <th class="px-6 py-3 text-right text-xs font-semibold text-fortress-300 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-fortress-700">
              <tr v-for="user in adminStore.users" :key="user.id" class="hover:bg-fortress-800/50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div 
                    @click="navigateToUser(user.id)"
                    class="cursor-pointer hover:text-secure transition-colors"
                  >
                    <div class="font-medium text-fortress-100">{{ user.full_name }}</div>
                    <div class="text-xs text-fortress-400">@{{ user.username }}</div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-fortress-300">
                  {{ user.email }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span 
                    v-if="user.is_suspended"
                    class="px-3 py-1 bg-alert/20 text-alert text-xs rounded-full font-medium"
                  >
                    Suspended
                  </span>
                  <span 
                    v-else-if="user.is_active"
                    class="px-3 py-1 bg-success/20 text-success text-xs rounded-full font-medium"
                  >
                    Active
                  </span>
                  <span 
                    v-else
                    class="px-3 py-1 bg-fortress-700 text-fortress-300 text-xs rounded-full font-medium"
                  >
                    Inactive
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span 
                    v-if="user.is_verified"
                    class="px-3 py-1 bg-success/20 text-success text-xs rounded-full"
                  >
                    ✓ Verified
                  </span>
                  <span 
                    v-else
                    class="px-3 py-1 bg-fortress-700 text-fortress-300 text-xs rounded-full"
                  >
                    Pending
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                  <div class="flex justify-end gap-2">
                    <button
                      @click="openSuspendModal(user)"
                      v-if="!user.is_suspended"
                      :disabled="isCurrentUser(user.id)"
                      :class="[
                        'px-3 py-1 text-xs rounded transition-colors',
                        isCurrentUser(user.id)
                          ? 'bg-fortress-700 text-fortress-500 cursor-not-allowed opacity-50'
                          : 'bg-alert/10 text-alert hover:bg-alert/20'
                      ]"
                      :title="isCurrentUser(user.id) ? 'Cannot suspend your own account' : 'Suspend user'"
                    >
                      Suspend
                    </button>
                    <button
                      @click="unsuspendUser(user.id)"
                      v-else
                      :disabled="isCurrentUser(user.id)"
                      :class="[
                        'px-3 py-1 text-xs rounded transition-colors',
                        isCurrentUser(user.id)
                          ? 'bg-fortress-700 text-fortress-500 cursor-not-allowed opacity-50'
                          : 'bg-success/10 text-success hover:bg-success/20'
                      ]"
                      :title="isCurrentUser(user.id) ? 'Cannot unsuspend your own account' : 'Unsuspend user'"
                    >
                      Unsuspend
                    </button>
                    <button
                      @click="navigateToUser(user.id)"
                      class="px-3 py-1 text-xs bg-secure/10 text-secure hover:bg-secure/20 rounded transition-colors"
                      title="View details"
                    >
                      Details
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else class="flex-1 card flex items-center justify-center">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secure mx-auto mb-2"></div>
          <p class="text-fortress-400">Loading users...</p>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="adminStore.users.length > 0" class="flex items-center justify-between text-sm text-fortress-400">
        <span>Page {{ adminStore.currentPage }} of {{ totalPages }}</span>
        <div class="flex gap-2">
          <button
            @click="previousPage"
            :disabled="adminStore.currentPage === 1"
            class="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            @click="nextPage"
            :disabled="adminStore.currentPage === totalPages"
            class="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Suspend Modal -->
    <UserSuspendModal 
      v-if="suspendModal.show"
      :user="suspendModal.user"
      @confirm="confirmSuspend"
      @close="suspendModal.show = false"
    />

    <!-- Invite Modal -->
    <UserInviteModal
      v-if="showInviteModal"
      :roles="adminStore.roles"
      @invite="handleInviteUser"
      @close="showInviteModal = false"
    />

    <!-- Roles Tab -->
    <div v-if="activeTab === 'roles'" class="flex-1 card overflow-auto">
      <div v-if="!adminStore.isLoading" class="space-y-4">
        <div v-if="adminStore.roles.length === 0" class="text-center py-8 text-fortress-400">
          No roles found
        </div>

        <div
          v-for="role in adminStore.roles"
          :key="role.id"
          class="p-4 bg-fortress-800/50 rounded-lg"
        >
          <div class="flex items-start justify-between mb-3">
            <div>
              <div class="flex items-center gap-2">
                <h3 class="font-semibold text-fortress-100">{{ role.name }}</h3>
                <span v-if="role.is_system" class="px-2 py-1 bg-secure/20 text-secure text-xs rounded">
                  System
                </span>
              </div>
              <p class="text-sm text-fortress-400 mt-1">{{ role.description }}</p>
            </div>
          </div>

          <!-- Permissions -->
          <div v-if="role.permissions && role.permissions.length > 0" class="mt-3">
            <p class="text-xs uppercase text-fortress-500 mb-2">Permissions</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="permission in role.permissions"
                :key="permission.id"
                class="px-2 py-1 bg-fortress-700 text-fortress-300 text-xs rounded"
              >
                {{ permission.code }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else class="flex items-center justify-center py-8">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secure mx-auto mb-2"></div>
          <p class="text-fortress-400">Loading roles...</p>
        </div>
      </div>
    </div>

    <!-- User Detail Page - removed modal, now using dedicated route -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'
import { useAuthStore } from '../../stores/auth'
import UserSuspendModal from '../../components/admin/UserSuspendModal.vue'
import UserInviteModal from '../../components/admin/UserInviteModal.vue'

const router = useRouter()
const adminStore = useAdminStore()
const authStore = useAuthStore()
const activeTab = ref('users')
const searchQuery = ref('')
const showInviteModal = ref(false)
const suspendModal = ref({
  show: false,
  user: null
})

const totalPages = computed(() => {
  return Math.ceil(adminStore.totalUsers / adminStore.pageSize)
})

function isCurrentUser(userId) {
  return authStore.user?.id === userId
}

async function loadUsers() {
  const filters = {
    activeOnly: true,
  }
  await adminStore.fetchUsers(adminStore.currentPage, filters)
}

async function loadRoles() {
  await adminStore.fetchRoles()
}

function handleSearch() {
  adminStore.currentPage = 1
  loadUsers()
}

function resetFilters() {
  searchQuery.value = ''
  adminStore.currentPage = 1
  loadUsers()
}

function navigateToUser(userId) {
  router.push({ name: 'user-detail', params: { userId } })
}

function nextPage() {
  if (adminStore.currentPage < totalPages.value) {
    adminStore.currentPage++
    loadUsers()
  }
}

function previousPage() {
  if (adminStore.currentPage > 1) {
    adminStore.currentPage--
    loadUsers()
  }
}

function openSuspendModal(user) {
  // Prevent admins from suspending their own account
  if (isCurrentUser(user.id)) {
    adminStore.error = 'You cannot suspend your own account'
    return
  }
  suspendModal.value = {
    show: true,
    user
  }
}

async function confirmSuspend(reason) {
  await adminStore.suspendUser(suspendModal.value.user.id, reason)
  suspendModal.value.show = false
  await loadUsers()
}

async function unsuspendUser(userId) {
  // Prevent admins from unsuspending their own account
  if (isCurrentUser(userId)) {
    adminStore.error = 'You cannot unsuspend your own account'
    return
  }
  await adminStore.unsuspendUser(userId)
  await loadUsers()
}

async function handleInviteUser(inviteData) {
  // Call API to send invite
  const result = await adminStore.inviteUser(inviteData.email, inviteData.roleId)
  if (result.success) {
    showInviteModal.value = false
    await loadUsers()
  }
}

onMounted(async () => {
  await loadUsers()
  await loadRoles()
})
</script>

<style scoped>
table {
  border-collapse: collapse;
}

thead tr {
  border-bottom: 2px solid rgba(0, 0, 0, 0.1);
}

tbody tr {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.15) !important;
}

th {
  font-weight: 600;
  letter-spacing: 0.05em;
}

td {
  vertical-align: middle;
}
</style>
