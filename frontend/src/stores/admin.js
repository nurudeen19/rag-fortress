import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAdminStore = defineStore('admin', () => {
  // State
  const users = ref([])
  const selectedUser = ref(null)
  const roles = ref([])
  const permissions = ref([])
  const loading = ref(false)
  const error = ref(null)
  const totalUsers = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)

  // Getters
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => !!error.value)

  // Actions - Users
  async function fetchUsers(page = 1, filters = {}) {
    loading.value = true
    error.value = null

    try {
      const offset = (page - 1) * pageSize.value
      const response = await api.get('/v1/admin/users', {
        params: {
          limit: pageSize.value,
          offset,
          active_only: filters.activeOnly !== false,
          department_id: filters.departmentId || undefined,
        }
      })

      users.value = response.users || []
      totalUsers.value = response.total || 0
      currentPage.value = page

      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch users'
      console.error('Error fetching users:', err)
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function fetchUserDetails(userId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get(`/v1/admin/users/${userId}`)
      selectedUser.value = response
      return { success: true, user: response }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch user details'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function suspendUser(userId, reason = '') {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/v1/admin/users/${userId}/suspend`, {
        reason
      })

      // Update local user
      const userIndex = users.value.findIndex(u => u.id === userId)
      if (userIndex !== -1) {
        users.value[userIndex].is_suspended = true
        if (reason) users.value[userIndex].suspension_reason = reason
      }

      return { success: true, message: response.message }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to suspend user'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function unsuspendUser(userId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/v1/admin/users/${userId}/unsuspend`)

      // Update local user
      const userIndex = users.value.findIndex(u => u.id === userId)
      if (userIndex !== -1) {
        users.value[userIndex].is_suspended = false
        users.value[userIndex].suspension_reason = null
      }

      return { success: true, message: response.message }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to unsuspend user'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function inviteUser(email, roleId, invitationLinkTemplate) {
    loading.value = true
    error.value = null

    try {
      const payload = {
        email,
        role_id: roleId
      }
      
      // Include invitation link template if provided
      if (invitationLinkTemplate) {
        payload.invitation_link_template = invitationLinkTemplate
      }
      
      const response = await api.post('/v1/admin/users/invite', payload)

      return { success: true, message: response.message }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to send invite'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // Actions - Roles
  async function fetchRoles() {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/v1/admin/roles')
      roles.value = response.roles || []
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch roles'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function assignRoleToUser(userId, roleId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post(`/v1/admin/users/${userId}/roles`, {
        role_id: roleId
      })
      return { success: true, message: response.message }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to assign role'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function revokeRoleFromUser(userId, roleId) {
    loading.value = true
    error.value = null

    try {
      const response = await api.delete(`/v1/admin/users/${userId}/roles/${roleId}`)
      return { success: true, message: response.message }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to revoke role'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function fetchUserRoles(userId) {
    try {
      const response = await api.get(`/v1/admin/users/${userId}/roles`)
      return { success: true, roles: response || [] }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch user roles'
      return { success: false, error: error.value }
    }
  }

  // Actions - Permissions
  async function fetchPermissions(resource = null) {
    loading.value = true
    error.value = null

    try {
      const response = await api.get('/v1/admin/permissions', {
        params: resource ? { resource } : {}
      })
      permissions.value = response || []
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch permissions'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // Utility
  function clearError() {
    error.value = null
  }

  function clearSelection() {
    selectedUser.value = null
  }

  return {
    // State
    users,
    selectedUser,
    roles,
    permissions,
    loading,
    error,
    totalUsers,
    currentPage,
    pageSize,
    // Getters
    isLoading,
    hasError,
    // Actions
    fetchUsers,
    fetchUserDetails,
    suspendUser,
    unsuspendUser,
    inviteUser,
    fetchRoles,
    assignRoleToUser,
    revokeRoleFromUser,
    fetchUserRoles,
    fetchPermissions,
    clearError,
    clearSelection,
  }
})
