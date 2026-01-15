<template>
  <div class="min-h-screen flex items-center justify-center bg-fortress-950 px-4 py-8">
    <div class="w-full max-w-md">
      <!-- Logo/Header -->
      <div class="text-center mb-8 md:mb-12">
        <img src="/logo.png" alt="RAG Fortress Logo" class="w-16 h-16 mx-auto mb-4 rounded-xl">
        <h1 class="text-3xl font-bold text-fortress-100 mb-2">RAG Fortress</h1>
        <p class="text-fortress-400">Secure Knowledge Management</p>
      </div>

      <!-- Login Card -->
      <div class="card animate-fade-in">
        <div class="card-body">
          <h2 class="text-2xl font-semibold text-fortress-100 mb-6">Sign In</h2>

          <!-- Demo Mode Backend Wake-up Notice -->
          <div v-if="demoModeEnabled" class="mb-4 p-4 rounded-lg text-sm border bg-info/10 border-info/30 text-info">
            <div class="flex items-start gap-3">
              <svg class="h-5 w-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
              <div>
                <p class="font-semibold mb-1">Demo Mode - Backend Startup Notice</p>
                <p>If your first login attempt fails, please wait a few minutes before retrying. The backend service may be waking up from sleep due to inactivity.</p>
              </div>
            </div>
          </div>

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

      <!-- Demo Credentials (only in demo mode with permission) -->
      <div v-if="showDemoCredentialsPanel" class="mt-6 rounded-2xl border border-secure/40 bg-gradient-to-br from-secure/10 via-fortress-900 to-fortress-950/90 p-6 shadow-xl backdrop-blur">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-xs tracking-[0.2em] uppercase text-secure/80">Demo Mode</p>
            <p class="text-lg font-semibold text-fortress-100">Use the admin credentials below</p>
          </div>
          <span class="text-xs font-medium text-fortress-300">Preview access</span>
        </div>
        <div class="space-y-2 text-sm text-fortress-300">
          <div class="flex items-center justify-between bg-fortress-900/70 px-3 py-2 rounded-lg text-fortress-200">
            <span class="text-xs uppercase tracking-[0.2em] text-fortress-500">Username</span>
            <span class="font-mono text-fortress-100">{{ demoCredentials.username }}</span>
          </div>
          <div class="flex items-center justify-between bg-fortress-900/70 px-3 py-2 rounded-lg text-fortress-200">
            <span class="text-xs uppercase tracking-[0.2em] text-fortress-500">Password</span>
            <span class="font-mono text-fortress-100">{{ '•'.repeat(Math.min(demoCredentials.password.length, 20)) }}</span>
          </div>
        </div>
        <button
          type="button"
          class="mt-4 w-full btn-secondary flex items-center justify-center gap-2"
          @click="fillDemoCredentials"
        >
          <svg class="h-4 w-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14m7-7H5" />
          </svg>
          <span>Use credentials</span>
        </button>
        <p class="mt-3 text-xs text-fortress-400">
          These credentials match the administrator account configured for demos. Use them to explore the experience without needing your own account.
        </p>
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

const demoModeEnabled = import.meta.env.VITE_DEMO_MODE === 'true'
const demoCredentialsVisible = import.meta.env.VITE_SHOW_DEMO_CREDENTIALS === 'true'
const demoCredentials = {
  username: import.meta.env.VITE_DEMO_ADMIN_USERNAME || '',
  password: import.meta.env.VITE_DEMO_ADMIN_PASSWORD || ''
}
const showDemoCredentialsPanel = demoModeEnabled && demoCredentialsVisible

const fillDemoCredentials = () => {
  credentials.value.usernameOrEmail = demoCredentials.username
  credentials.value.password = demoCredentials.password
}

const getErrorDetails = (errorMessage) => {
  if (!errorMessage) {
    return { type: null, title: 'Login Failed', message: errorMessage }
  }

  // Convert to lowercase for case-insensitive matching
  const message = String(errorMessage).toLowerCase()

  // Check for suspended account - includes "account is locked" with optional reason
  if (message.includes('account is locked')) {
    // Extract suspension reason if present (format: "Account is locked (reason)")
    const reasonMatch = errorMessage.match(/\((.*?)\)/)
    const reason = reasonMatch ? reasonMatch[1] : null
    
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
    return {
      type: 'unverified',
      title: 'Email Not Verified',
      message: 'Please verify your email address before logging in.'
    }
  }

  // Default error
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
    if (import.meta.env.DEV) {
      console.log('Login failed')
    }
    const errorDetails = getErrorDetails(result.error)
    error.value = errorDetails.message
    errorType.value = errorDetails.type
    errorTitle.value = errorDetails.title
  }
  
  loading.value = false
}
</script>
