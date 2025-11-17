<template>
  <div class="min-h-screen bg-fortress-950 flex items-center justify-center px-4 py-8 md:py-12">
    <div class="w-full max-w-md">
      <div class="text-center mb-8 md:mb-12">
        <div class="inline-block p-3 bg-secure/10 rounded-lg mb-4">
          <svg class="w-12 h-12 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-fortress-100">Create New Password</h1>
        <p class="text-fortress-400 mt-2">Enter your new password below</p>
      </div>

      <div class="card">
        <div class="card-body space-y-6">
          <!-- Loading state while verifying token -->
          <div v-if="verifying" class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secure"></div>
          </div>

          <!-- Token verification failed -->
          <div v-else-if="tokenInvalid" class="space-y-4">
            <div class="p-4 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
              {{ tokenError }}
            </div>
            <router-link 
              to="/forgot-password" 
              class="btn btn-primary w-full text-center"
            >
              Request New Reset Link
            </router-link>
          </div>

          <!-- Form for entering new password -->
          <form v-else @submit.prevent="handleResetPassword" class="space-y-6">
            <div v-if="error" class="p-4 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
              {{ error }}
            </div>

            <div v-if="success" class="p-4 bg-success/10 border border-success/30 rounded-lg text-success text-sm">
              {{ successMessage }}
            </div>

            <!-- Password field -->
            <div v-if="!success">
              <label class="block text-sm font-medium text-fortress-300 mb-2">New Password</label>
              <div class="relative">
                <input
                  v-model="newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  class="input pr-10"
                  placeholder="Enter new password"
                  required
                  minlength="8"
                />
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-fortress-400 hover:text-fortress-300"
                  @click="showPassword = !showPassword"
                >
                  <svg v-if="showPassword" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                    <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                  </svg>
                  <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-5.68 1.74L3.707 2.293zM12.168 6.889a4 4 0 010 5.656l-2.121-2.121a2 2 0 00-2.828 2.828l2.121 2.121a4 4 0 01-5.656-5.656l1.414-1.414a6 6 0 018.485 8.485l-1.414 1.414a6 6 0 01-8.485-8.485l1.414-1.414z" clip-rule="evenodd"/>
                  </svg>
                </button>
              </div>
              <p class="mt-2 text-xs text-fortress-400">
                At least 8 characters, with uppercase, lowercase, number, and special character
              </p>
            </div>

            <!-- Confirm password field -->
            <div v-if="!success">
              <label class="block text-sm font-medium text-fortress-300 mb-2">Confirm Password</label>
              <div class="relative">
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  class="input pr-10"
                  placeholder="Confirm password"
                  required
                  minlength="8"
                />
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-fortress-400 hover:text-fortress-300"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <svg v-if="showConfirmPassword" class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                    <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                  </svg>
                  <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-5.68 1.74L3.707 2.293zM12.168 6.889a4 4 0 010 5.656l-2.121-2.121a2 2 0 00-2.828 2.828l2.121 2.121a4 4 0 01-5.656-5.656l1.414-1.414a6 6 0 018.485 8.485l-1.414 1.414a6 6 0 01-8.485-8.485l1.414-1.414z" clip-rule="evenodd"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Submit button -->
            <button
              v-if="!success"
              type="submit"
              class="btn btn-primary w-full"
              :disabled="loading"
            >
              <span v-if="loading">Resetting Password...</span>
              <span v-else>Reset Password</span>
            </button>

            <!-- Success redirect button -->
            <router-link
              v-else
              to="/login"
              class="btn btn-primary w-full text-center"
            >
              Back to Login
            </router-link>
          </form>

          <div class="pt-4 border-t border-fortress-700 text-center text-sm text-fortress-400">
            Remember your password?
            <router-link to="/login" class="text-secure hover:text-secure/80 font-medium transition-colors">
              Back to login
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// State
const token = ref(route.query.token || '')
const verifying = ref(true)
const tokenInvalid = ref(false)
const tokenError = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref(false)
const successMessage = ref('')

// Verify token when component mounts
onMounted(async () => {
  if (!token.value) {
    tokenInvalid.value = true
    tokenError.value = 'No reset token provided. Please use the link from your email.'
    verifying.value = false
    return
  }

  console.log('Verifying token:', token.value)
  try {
    await authStore.verifyResetToken(token.value)
    console.log('Token verification successful')
    verifying.value = false
  } catch (err) {
    console.error('Token verification error:', err)
    verifying.value = false
    tokenInvalid.value = true
    tokenError.value = err.response?.data?.detail || 'Invalid or expired reset token'
  }
})

const handleResetPassword = async () => {
  error.value = ''
  
  // Validate passwords match
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true

  try {
    await authStore.confirmPasswordReset(token.value, newPassword.value, confirmPassword.value)
    success.value = true
    successMessage.value = 'Password reset successful! Redirecting to login...'
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to reset password'
  } finally {
    loading.value = false
  }
}
</script>
