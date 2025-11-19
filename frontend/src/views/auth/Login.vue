<template>
  <div class="min-h-screen flex items-center justify-center bg-fortress-950 px-4 py-8">
    <div class="w-full max-w-md">
      <!-- Logo/Header -->
      <div class="text-center mb-8 md:mb-12">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-secure/10 border border-secure/30 rounded-xl mb-4">
          <svg class="w-8 h-8 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-fortress-100 mb-2">RAG Fortress</h1>
        <p class="text-fortress-400">Secure Knowledge Management</p>
      </div>

      <!-- Login Card -->
      <div class="card animate-fade-in">
        <div class="card-body">
          <h2 class="text-2xl font-semibold text-fortress-100 mb-6">Sign In</h2>

          <!-- Error Message -->
          <div v-if="error" :class="[
            'mb-4 p-4 rounded-lg text-sm border',
            errorType === 'suspended' ? 'bg-alert/10 border-alert/30 text-alert' :
            errorType === 'inactive' ? 'bg-alert/10 border-alert/30 text-alert' :
            errorType === 'unverified' ? 'bg-warning/10 border-warning/30 text-warning' :
            'bg-alert/10 border-alert/30 text-alert'
          ]">
            <p class="font-semibold mb-2">{{ errorTitle }}</p>
            <p>{{ error }}</p>
            <p v-if="errorType === 'unverified'" class="text-xs mt-2 opacity-80">
              Check your email for the verification link. Need help? Contact support.
            </p>
          </div>

          <!-- Login Form -->
          <form @submit.prevent="handleLogin" class="space-y-4">
            <!-- Username/Email -->
            <div>
              <label for="usernameOrEmail" class="block text-sm font-medium text-fortress-300 mb-2">
                Username or Email
              </label>
              <input
                id="usernameOrEmail"
                v-model="credentials.usernameOrEmail"
                type="text"
                required
                class="input"
                placeholder="Enter your username or email"
                :disabled="loading"
              />
            </div>

            <!-- Password -->
            <div>
              <label for="password" class="block text-sm font-medium text-fortress-300 mb-2">
                Password
              </label>
              <input
                id="password"
                v-model="credentials.password"
                type="password"
                required
                class="input"
                placeholder="Enter your password"
                :disabled="loading"
              />
            </div>

            <!-- Remember Me & Forgot Password -->
            <div class="flex items-center justify-between text-sm">
              <label class="flex items-center text-fortress-400 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="credentials.rememberMe"
                  class="mr-2 rounded bg-fortress-800 border-fortress-700 text-secure focus:ring-secure focus:ring-offset-fortress-950"
                  :disabled="loading"
                />
                Remember me
              </label>
              <router-link to="/forgot-password" class="text-secure hover:text-secure-light transition-colors">
                Forgot password?
              </router-link>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="loading"
              class="w-full btn-primary flex items-center justify-center"
            >
              <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span v-if="loading">Signing in...</span>
              <span v-else>Sign In</span>
            </button>
          </form>
        </div>
      </div>

      <!-- Footer -->
      <p class="mt-8 text-center text-xs text-fortress-500">
        © 2025 RAG Fortress. Secure by design.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const credentials = ref({
  usernameOrEmail: '',
  password: '',
  rememberMe: false
})

const loading = ref(false)
const error = ref(null)
const errorType = ref(null)
const errorTitle = ref('Login Failed')

const getErrorDetails = (errorMessage) => {
  if (!errorMessage) {
    return { type: null, title: 'Login Failed', message: errorMessage }
  }

  // Convert to lowercase for case-insensitive matching
  const message = String(errorMessage).toLowerCase()
  
  // Debug logging
  console.log('Error message received:', errorMessage)
  console.log('Lowercased message:', message)

  // Check for suspended account - includes "account is locked" with optional reason
  if (message.includes('account is locked')) {
    // Extract suspension reason if present (format: "Account is locked (reason)")
    const reasonMatch = errorMessage.match(/\((.*?)\)/)
    const reason = reasonMatch ? reasonMatch[1] : null
    
    console.log('Detected suspended account, reason:', reason)
    
    return {
      type: 'suspended',
      title: 'Account Suspended',
      message: reason 
        ? `Your account has been suspended. Reason: ${reason}`
        : 'Your account has been suspended. Please contact support if you believe this is an error.'
    }
  }

  // Check for inactive account
  if (message.includes('inactive')) {
    console.log('Detected inactive account')
    return {
      type: 'inactive',
      title: 'Account Deactivated',
      message: 'Your account has been deactivated. Please contact support to reactivate it.'
    }
  }

  // Check for unverified account
  if (message.includes('not verified') || message.includes('unverified')) {
    console.log('Detected unverified account')
    return {
      type: 'unverified',
      title: 'Email Not Verified',
      message: 'Please verify your email address before logging in.'
    }
  }

  // Default error
  console.log('Using default error handling')
  return {
    type: 'generic',
    title: 'Login Failed',
    message: 'Invalid username/email or password. Please try again.'
  }
}

const handleLogin = async () => {
  loading.value = true
  error.value = null
  errorType.value = null
  errorTitle.value = 'Login Failed'
  
  const result = await authStore.login(credentials.value)
  
  if (result.success) {
    // Redirect to dashboard (main entry point)
    router.push('/dashboard')
  } else {
    console.log('Login result:', result)
    const errorDetails = getErrorDetails(result.error)
    console.log('Error details parsed:', errorDetails)
    error.value = errorDetails.message
    errorType.value = errorDetails.type
    errorTitle.value = errorDetails.title
  }
  
  loading.value = false
}
</script>
