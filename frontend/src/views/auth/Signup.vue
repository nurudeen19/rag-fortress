<template>
  <div class="min-h-screen bg-gradient-to-br from-fortress-950 via-fortress-900 to-fortress-950 flex items-center justify-center px-4 py-8">
    <div class="w-full max-w-2xl">
      <!-- Header Section -->
      <div class="text-center mb-12">
        <div class="inline-flex p-4 bg-gradient-to-br from-secure/20 to-secure/10 rounded-2xl mb-6 border border-secure/30">
          <svg class="w-10 h-10 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
          </svg>
        </div>
        <h1 class="text-4xl font-bold text-fortress-100 mb-3">Create Your Account</h1>
        <p class="text-fortress-400 text-base">Complete your profile to get started</p>
      </div>

      <!-- Main Card -->
      <div class="bg-gradient-to-b from-fortress-900 to-fortress-950 rounded-2xl border border-fortress-800 shadow-2xl overflow-hidden">
        <div class="px-10 py-12">
          <!-- Loading State -->
          <div v-if="verifying" class="flex justify-center items-center py-16">
            <div class="space-y-4 text-center">
              <div class="inline-block">
                <div class="animate-spin rounded-full h-12 w-12 border-2 border-fortress-700 border-t-secure"></div>
              </div>
              <p class="text-fortress-400 text-sm">Verifying your invitation...</p>
            </div>
          </div>

          <!-- Token Invalid State -->
          <div v-else-if="tokenInvalid" class="space-y-6">
            <div class="p-4 bg-alert/10 border border-alert/30 rounded-xl text-alert text-sm flex items-start gap-3">
              <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="font-medium">Invalid Invitation</p>
                <p class="text-xs mt-1">{{ tokenError }}</p>
              </div>
            </div>
            <router-link 
              to="/login" 
              class="btn btn-primary w-full text-center py-3"
            >
              Back to Login
            </router-link>
          </div>

          <!-- Form Section -->
          <form v-else @submit.prevent="handleSignup" class="space-y-7">
            <!-- Form Fields Section -->
            <div v-if="!success" class="space-y-6">
              <!-- Error Alert -->
              <div v-if="error" class="p-4 bg-alert/10 border border-alert/30 rounded-xl text-alert text-sm flex items-start gap-3">
                <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                </svg>
                <span>{{ error }}</span>
              </div>

              <!-- Email (Read-only) -->
              <div class="space-y-2.5">
                <label class="block text-sm font-semibold text-fortress-200">Email Address</label>
                <input
                  v-model="email"
                  type="email"
                  class="w-full px-4 py-3 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100 disabled:opacity-60 disabled:cursor-not-allowed focus:border-secure focus:outline-none transition-colors"
                  disabled
                />
                <p class="text-xs text-fortress-500">Invited to this email address</p>
              </div>

              <!-- Name Row -->
              <div class="grid grid-cols-2 gap-6">
                <!-- First Name -->
                <div class="space-y-2.5">
                  <label class="block text-sm font-semibold text-fortress-200">First Name</label>
                  <input
                    v-model="firstName"
                    type="text"
                    class="w-full px-4 py-3 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure/30 transition-colors"
                    placeholder="John"
                    required
                  />
                </div>

                <!-- Last Name -->
                <div class="space-y-2.5">
                  <label class="block text-sm font-semibold text-fortress-200">Last Name</label>
                  <input
                    v-model="lastName"
                    type="text"
                    class="w-full px-4 py-3 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure/30 transition-colors"
                    placeholder="Doe"
                    required
                  />
                </div>
              </div>

              <!-- Username -->
              <div class="space-y-2.5">
                <label class="block text-sm font-semibold text-fortress-200">Username</label>
                <input
                  v-model="username"
                  type="text"
                  class="w-full px-4 py-3 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure/30 transition-colors"
                  placeholder="johndoe123"
                  required
                  minlength="3"
                />
                <p class="text-xs text-fortress-500">3+ characters, alphanumeric and underscores</p>
              </div>

              <!-- Password -->
              <div class="space-y-2.5">
                <label class="block text-sm font-semibold text-fortress-200">Password</label>
                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    class="w-full px-4 py-3 pr-12 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure/30 transition-colors"
                    placeholder="••••••••"
                    required
                    minlength="8"
                  />
                  <button
                    type="button"
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-fortress-500 hover:text-fortress-300 transition-colors"
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
                <p class="text-xs text-fortress-500">8+ characters with uppercase, lowercase, numbers, and special chars</p>
              </div>

              <!-- Confirm Password -->
              <div class="space-y-2.5">
                <label class="block text-sm font-semibold text-fortress-200">Confirm Password</label>
                <div class="relative">
                  <input
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    class="w-full px-4 py-3 pr-12 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure/30 transition-colors"
                    placeholder="••••••••"
                    required
                    minlength="8"
                  />
                  <button
                    type="button"
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-fortress-500 hover:text-fortress-300 transition-colors"
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

              <!-- Role Badge -->
              <div class="p-5 bg-gradient-to-br from-secure/10 to-secure/5 border border-secure/30 rounded-xl">
                <p class="text-xs font-medium text-fortress-500 uppercase tracking-wide mb-3">Your Role</p>
                <div class="inline-flex items-center gap-2 px-3 py-2 bg-secure/20 border border-secure/40 rounded-full">
                  <div class="w-2 h-2 bg-secure rounded-full"></div>
                  <p class="text-sm font-semibold text-secure">{{ roleName }}</p>
                </div>
              </div>
            </div>

            <!-- Success Alert -->
            <div v-else class="p-4 bg-success/10 border border-success/30 rounded-xl text-success text-sm flex items-start gap-3">
              <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              <div>
                <p class="font-medium">Success!</p>
                <p class="text-xs mt-1">{{ successMessage }}</p>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="space-y-3 pt-4 border-t border-fortress-700/50">
              <button
                v-if="!success"
                type="submit"
                class="w-full px-4 py-3 bg-gradient-to-r from-secure to-secure/80 hover:from-secure/90 hover:to-secure/70 disabled:opacity-60 disabled:cursor-not-allowed text-fortress-950 font-bold rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
                :disabled="loading"
              >
                <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ loading ? 'Creating Account...' : 'Create Account' }}
              </button>

              <router-link
                v-else
                to="/login"
                class="block w-full px-4 py-3 bg-gradient-to-r from-secure to-secure/80 hover:from-secure/90 hover:to-secure/70 text-fortress-950 font-bold rounded-lg transition-all duration-200 text-center"
              >
                Proceed to Login
              </router-link>

              <p v-if="!success" class="text-xs text-center text-fortress-500">
                Already have an account?
                <router-link to="/login" class="text-secure hover:text-secure/80 font-medium transition-colors">
                  Log In
                </router-link>
              </p>
            </div>
          </form>
        </div>

        <!-- Footer -->
        <div class="px-10 py-6 border-t border-fortress-800 bg-fortress-950/50">
          <p class="text-center text-sm text-fortress-400">
            Already have an account?
            <router-link to="/login" class="text-secure hover:text-secure/80 font-semibold transition-colors">
              Sign in
            </router-link>
          </p>
        </div>
      </div>

      <!-- Footer Info -->
      <div class="mt-10 text-center text-xs text-fortress-500">
        <p>By signing up, you agree to our Terms of Service</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import api from '../../services/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// State
const token = ref(route.query.token || '')
const verifying = ref(true)
const tokenInvalid = ref(false)
const tokenError = ref('')
const email = ref('')
const firstName = ref('')
const lastName = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const roleName = ref('')
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
    tokenError.value = 'No invitation token provided. Please use the link from your email.'
    verifying.value = false
    return
  }

  try {
    // Verify the invitation token with backend
    const response = await api.get('/v1/auth/signup/verify-invite', {
      params: { token: token.value }
    })
    
    // Token is valid, extract invitation details
    if (response.email) {
      email.value = response.email
    }
    if (response.role_name) {
      roleName.value = response.role_name
    }
    
    verifying.value = false
  } catch (err) {
    verifying.value = false
    tokenInvalid.value = true
    
    let errorMessage = 'Invalid or expired invitation link'
    if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail
    } else if (err.response?.data?.error?.message) {
      errorMessage = err.response.data.error.message
    } else if (err.response?.data?.message) {
      errorMessage = err.response.data.message
    }
    
    tokenError.value = errorMessage
  }
})

const handleSignup = async () => {
  error.value = ''
  
  // Validate passwords match
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }

  // Validate required fields
  if (!firstName.value || !lastName.value || !username.value) {
    error.value = 'All fields are required'
    return
  }

  loading.value = true

  try {
    // Call signup/complete-profile endpoint with token
    const response = await api.post('/v1/auth/signup', {
      username: username.value,
      email: email.value,
      first_name: firstName.value,
      last_name: lastName.value,
      password: password.value,
      invite_token: token.value
    })
    
    success.value = true
    successMessage.value = 'Account created successfully! Redirecting to login...'
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err) {
    let errorMessage = 'Failed to create account'
    
    if (err.response?.data?.error?.message) {
      errorMessage = err.response.data.error.message
    } else if (err.response?.data?.detail) {
      errorMessage = err.response.data.detail
    } else if (err.response?.data?.message) {
      errorMessage = err.response.data.message
    }
    
    error.value = errorMessage
  } finally {
    loading.value = false
  }
}
</script>
