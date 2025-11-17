import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => {
    if (!user.value) return false
    // Check if user has admin role
    return user.value.roles?.some(role => role.name === 'admin') || false
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
      
      // Store token and user data
      token.value = response.token
      user.value = {
        id: response.user_id,
        username: response.username,
        email: response.email,
        first_name: response.first_name,
        last_name: response.last_name,
        is_verified: response.is_verified,
        is_active: response.is_active,
      }
      
      // Persist token
      localStorage.setItem('token', response.token)
      
      // Fetch full user profile (with roles)
      await fetchProfile()
      
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
    if (!token.value) return
    
    try {
      const response = await api.get('/v1/auth/me')
      user.value = {
        ...user.value,
        ...response,
      }
    } catch (err) {
      console.error('Failed to fetch profile:', err)
      // Token might be invalid, logout
      if (err.response?.status === 401) {
        logout()
      }
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
      // Handle different error response formats
      let errorMessage = 'Password reset failed'
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message
      } else if (err.message) {
        errorMessage = err.message
      }
      
      error.value = errorMessage
      console.error('Password reset error:', {
        status: err.response?.status,
        data: err.response?.data,
        message: errorMessage
      })
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    
    try {
      await api.post('/v1/auth/logout')
    } catch (err) {
      console.error('Logout API call failed:', err)
    } finally {
      // Clear local state regardless of API call result
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  // Initialize: fetch profile if token exists
  if (token.value) {
    fetchProfile()
  }

  return {
    // State
    user,
    token,
    loading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
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
