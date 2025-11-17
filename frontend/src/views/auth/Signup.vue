<template>
  <div class="min-h-screen bg-fortress-950 flex items-center justify-center px-4 py-8 md:py-12">
    <div class="w-full max-w-md">
      <div class="text-center mb-8 md:mb-12">
        <div class="inline-block p-3 bg-secure/10 rounded-lg mb-4">
          <svg class="w-12 h-12 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-fortress-100">Complete Your Profile</h1>
        <p class="text-fortress-400 mt-2">You've been invited to join. Set up your account.</p>
      </div>

      <div class="card min-h-64">
        <div class="card-body space-y-6 flex flex-col">
          <!-- Loading state while verifying token -->
          <div v-if="verifying" class="flex justify-center py-8 flex-1 items-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secure"></div>
          </div>

          <!-- Token verification failed -->
          <div v-else-if="tokenInvalid" class="space-y-4 flex-1 flex flex-col">
            <div class="p-4 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
              {{ tokenError }}
            </div>
            <div class="flex-1"></div>
            <router-link 
              to="/login" 
              class="btn btn-primary w-full text-center"
            >
              Back to Login
            </router-link>
          </div>

          <!-- Form for completing profile -->
          <form v-else @submit.prevent="handleSignup" class="space-y-6 flex flex-col">
            <div v-if="error" class="p-4 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
              {{ error }}
            </div>

            <div v-if="success" class="p-4 bg-success/10 border border-success/30 rounded-lg text-success text-sm">
              {{ successMessage }}
            </div>

            <div v-if="!success">
              <!-- Email display (read-only from invitation) -->
              <div>
                <label class="block text-sm font-medium text-fortress-300 mb-2">Email Address</label>
                <input
                  v-model="email"
                  type="email"
                  class="input bg-fortress-700"
                  disabled
                />
                <p class="mt-1 text-xs text-fortress-400">Invited to this email address</p>
              </div>

              <!-- First Name -->
              <div>
                <label class="block text-sm font-medium text-fortress-300 mb-2">First Name</label>
                <input
                  v-model="firstName"
                  type="text"
                  class="input"
                  placeholder="Enter first name"
                  required
                />
              </div>

              <!-- Last Name -->
              <div>
                <label class="block text-sm font-medium text-fortress-300 mb-2">Last Name</label>
                <input
                  v-model="lastName"
                  type="text"
                  class="input"
                  placeholder="Enter last name"
                  required
                />
              </div>

              <!-- Username -->
              <div>
                <label class="block text-sm font-medium text-fortress-300 mb-2">Username</label>
                <input
                  v-model="username"
                  type="text"
                  class="input"
                  placeholder="Choose a username"
                  required
                  minlength="3"
                />
                <p class="mt-1 text-xs text-fortress-400">Alphanumeric and underscores only</p>
              </div>

              <!-- Password -->
              <div>
                <label class="block text-sm font-medium text-fortress-300 mb-2">Password</label>
                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    class="input pr-10"
                    placeholder="Create a strong password"
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

              <!-- Confirm Password -->
              <div>
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

              <!-- Role Display -->
              <div class="p-3 bg-fortress-800/50 rounded-lg">
                <p class="text-xs text-fortress-400 mb-1">Your Role</p>
                <p class="text-sm font-medium text-secure">{{ roleName }}</p>
              </div>
            </div>

            <!-- Submit button -->
            <button
              v-if="!success"
              type="submit"
              class="btn btn-primary w-full"
              :disabled="loading"
            >
              <span v-if="loading">Creating Account...</span>
              <span v-else>Complete Setup</span>
            </button>

            <!-- Success redirect button -->
            <router-link
              v-else
              to="/login"
              class="btn btn-primary w-full text-center"
            >
              Go to Login
            </router-link>
          </form>

          <div class="pt-4 border-t border-fortress-700 text-center text-sm text-fortress-400 mt-auto">
            Already have an account?
            <router-link to="/login" class="text-secure hover:text-secure/80 font-medium transition-colors">
              Sign in
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
