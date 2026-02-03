import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  // State - user data only (no tokens in localStorage)
  // Tokens are stored in httpOnly cookies (secure, XSS-safe)
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const initialized = ref(false)

  // Getters
  const isAuthenticated = computed(() => {
    return !!user.value
  })
  const isAdmin = computed(() => {
    if (!user.value) return false
    // Check if user has admin role
    return user.value.roles?.some(role => role.name === 'admin') || false
  })
  const isManager = computed(() => {
    if (!user.value) return false
    // Check if user has manager or department_manager role
    return user.value.roles?.some(role => 
      role.name === 'manager' || role.name === 'department_manager'
    ) || false
  })
  const isDepartmentManager = computed(() => {
    if (!user.value) return false
    // Check if user has department assigned and manager/department_manager role
    return user.value.department_id && isManager.value
  })
  const fullName = computed(() => {
    if (!user.value) return ''
    return `${user.value.first_name} ${user.value.last_name}`
  })

  // Actions
  async function login(credentials) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/v1/auth/login', {
        username_or_email: credentials.usernameOrEmail,
        password: credentials.password
      })
      
      // Store user data only (tokens are in httpOnly cookies)
      user.value = {
        id: response.user.id,
        username: response.user.username,
        email: response.user.email,
        first_name: response.user.first_name,
        last_name: response.user.last_name,
        full_name: response.user.full_name,
        is_verified: response.user.is_verified,
        is_active: response.user.is_active,
        department_id: response.user.department_id || null,
        roles: response.user.roles || [],
        // Clearance levels
        security_level: response.user.security_level || null,
        org_clearance_value: response.user.org_clearance_value || null,
        department_security_level: response.user.department_security_level || null,
        dept_clearance_value: response.user.dept_clearance_value || null,
      }
      
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function register(userData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/v1/auth/register', {
        username: userData.username,
        email: userData.email,
        first_name: userData.firstName,
        last_name: userData.lastName,
        password: userData.password,
        department_id: userData.departmentId || null
      })
      
      // Registration successful but user needs to verify email
      return { success: true, user: response }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Registration failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function fetchProfile() {
    try {
      const response = await api.get('/v1/auth/me')
      user.value = {
        ...user.value,
        ...response,
      }
      return { success: true }
    } catch (err) {
      console.error('Failed to fetch profile:', err)
      // If 401 during manual refresh (not initialization), clear state
      // During initialization, let router handle redirect
      if (err.response?.status === 401 && initialized.value) {
        user.value = null
      }
      return { success: false, error: err }
    }
  }

  async function updateProfile(profileData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.put('/v1/auth/me', {
        first_name: profileData.firstName,
        last_name: profileData.lastName,
        email: profileData.email,
      })
      
      user.value = { ...user.value, ...response }
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Update failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function changePassword(passwordData) {
    loading.value = true
    error.value = null
    
    try {
      await api.post('/v1/auth/me/password', {
        old_password: passwordData.oldPassword,
        new_password: passwordData.newPassword,
      })
      
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Password change failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function requestPasswordReset(email, resetLinkTemplate = null) {
    loading.value = true
    error.value = null
    
    try {
      const payload = { email }
      if (resetLinkTemplate) {
        payload.reset_link_template = resetLinkTemplate
      }
      const response = await api.post('/v1/auth/password-reset', payload)
      return { success: true, message: response.message }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Request failed'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  async function verifyResetToken(token) {
    try {
      const response = await api.get('/v1/auth/password-reset/verify', {
        params: { token }
      })
      return { success: true, message: response.message }
    } catch (err) {
      throw err
    }
  }

  async function confirmPasswordReset(token, newPassword, confirmPassword) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/v1/auth/password-reset-confirm', {
        reset_token: token,
        new_password: newPassword,
        confirm_password: confirmPassword
      })
      return { success: true, message: response.message }
    } catch (err) {
      // Extract error message from structured response format
      // Backend returns: { error: { type, message, details } }
      let errorMessage = 'Password reset failed'
      
      if (err.response?.data?.error?.message) {
        errorMessage = err.response.data.error.message
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.response?.data?.error && typeof err.response.data.error === 'string') {
        errorMessage = err.response.data.error
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message
      } else if (err.message) {
        errorMessage = err.message
      }
      
      error.value = errorMessage
      if (import.meta.env.DEV) {
        console.error('Password reset error:', {
          status: err.response?.status,
          message: errorMessage
        })
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      // Call backend logout to clear httpOnly cookies
      await api.post('/v1/auth/logout')
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      // Clear user state (cookies are cleared by backend)
      user.value = null
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  // Initialize: try to fetch profile (will work if httpOnly cookie exists)
  fetchProfile().finally(() => {
    initialized.value = true
  })

  return {
    // State
    user,
    loading,
    error,
    initialized,
    // Getters
    isAuthenticated,
    isAdmin,
    isManager,
    isDepartmentManager,
    fullName,
    // Actions
    login,
    register,
    fetchProfile,
    updateProfile,
    changePassword,
    requestPasswordReset,
    verifyResetToken,
    confirmPasswordReset,
    logout,
    clearError,
  }
})
