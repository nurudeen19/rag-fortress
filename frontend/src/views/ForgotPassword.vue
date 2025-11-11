<template>
  <div class="min-h-screen bg-fortress-950 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-block p-3 bg-warning/10 rounded-lg mb-4">
          <svg class="w-12 h-12 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-fortress-100">Reset Password</h1>
        <p class="text-fortress-400 mt-2">Enter your email to receive reset instructions</p>
      </div>

      <div class="card">
        <div v-if="success" class="p-4 bg-success/10 border border-success/30 rounded-lg text-success text-sm mb-4">
          Password reset instructions have been sent to your email.
        </div>

        <form v-else @submit.prevent="handleReset" class="space-y-4">
          <div v-if="error" class="p-3 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
            {{ error }}
          </div>

          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-1">Email Address</label>
            <input
              v-model="email"
              type="email"
              class="input"
              placeholder="your@email.com"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary w-full"
            :disabled="loading"
          >
            <span v-if="loading">Sending...</span>
            <span v-else>Send Reset Link</span>
          </button>
        </form>

        <div class="mt-6 text-center text-sm text-fortress-400">
          Remember your password?
          <router-link to="/login" class="text-secure hover:text-secure/80 font-medium">
            Back to login
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const email = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const handleReset = async () => {
  error.value = ''
  loading.value = true

  try {
    await authStore.requestPasswordReset(email.value)
    success.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to send reset email'
  } finally {
    loading.value = false
  }
}
</script>
