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
      <!-- Filters -->
      <div class="flex gap-2 items-center">
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

      <!-- Users List -->
      <div v-if="!adminStore.isLoading" class="flex-1 card overflow-auto">
        <div class="space-y-2">
          <div v-if="adminStore.users.length === 0" class="text-center py-8 text-fortress-400">
            No users found
          </div>

          <div
            v-for="user in adminStore.users"
            :key="user.id"
            class="p-4 bg-fortress-800/50 rounded-lg hover:bg-fortress-800 cursor-pointer transition-colors"
            @click="selectUser(user.id)"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="font-semibold text-fortress-100">{{ user.full_name }}</span>
                  <span v-if="user.is_suspended" class="px-2 py-1 bg-alert/20 text-alert text-xs rounded">
                    Suspended
                  </span>
                  <span v-if="user.is_verified" class="px-2 py-1 bg-success/20 text-success text-xs rounded">
                    Verified
                  </span>
                </div>
                <div class="text-sm text-fortress-400">
                  {{ user.email }} · @{{ user.username }}
                </div>
              </div>
              <div class="text-right text-sm text-fortress-400">
                ID: {{ user.id }}
              </div>
            </div>
          </div>
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

    <!-- User Detail Modal -->
    <UserDetailModal
      v-if="selectedUserId"
      :user-id="selectedUserId"
      @close="adminStore.clearSelection()"
      @refresh="loadUsers"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '../stores/admin'
import UserDetailModal from '../components/UserDetailModal.vue'

const adminStore = useAdminStore()
const activeTab = ref('users')
const selectedUserId = ref(null)
const searchQuery = ref('')

const totalPages = computed(() => {
  return Math.ceil(adminStore.totalUsers / adminStore.pageSize)
})

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

function selectUser(userId) {
  selectedUserId.value = userId
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

onMounted(async () => {
  await loadUsers()
  await loadRoles()
})
</script>
