<template>
  <div class="min-h-screen bg-fortress-950 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-block p-3 bg-secure/10 rounded-lg mb-4">
          <svg class="w-12 h-12 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-fortress-100">Create Account</h1>
        <p class="text-fortress-400 mt-2">Join the Fortress</p>
      </div>

      <div class="card">
        <form @submit.prevent="handleRegister" class="space-y-4">
          <div v-if="error" class="p-3 bg-alert/10 border border-alert/30 rounded-lg text-alert text-sm">
            {{ error }}
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-1">First Name</label>
              <input
                v-model="form.firstName"
                type="text"
                class="input"
                placeholder="John"
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-1">Last Name</label>
              <input
                v-model="form.lastName"
                type="text"
                class="input"
                placeholder="Doe"
                required
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-1">Username</label>
            <input
              v-model="form.username"
              type="text"
              class="input"
              placeholder="johndoe"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-1">Email</label>
            <input
              v-model="form.email"
              type="email"
              class="input"
              placeholder="john@company.com"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-1">Department</label>
            <select v-model="form.department" class="input" required>
              <option value="">Select department...</option>
              <option value="engineering">Engineering</option>
              <option value="hr">Human Resources</option>
              <option value="finance">Finance</option>
              <option value="legal">Legal</option>
              <option value="sales">Sales</option>
              <option value="marketing">Marketing</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-1">Password</label>
            <input
              v-model="form.password"
              type="password"
              class="input"
              placeholder="••••••••"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-1">Confirm Password</label>
            <input
              v-model="form.confirmPassword"
              type="password"
              class="input"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary w-full"
            :disabled="loading"
          >
            <span v-if="loading">Creating Account...</span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <div class="mt-6 text-center text-sm text-fortress-400">
          Already have an account?
          <router-link to="/login" class="text-secure hover:text-secure/80 font-medium">
            Sign in
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const form = ref({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  department: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')

const handleRegister = async () => {
  error.value = ''

  if (form.value.password !== form.value.confirmPassword) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true
  try {
    await authStore.register({
      first_name: form.value.firstName,
      last_name: form.value.lastName,
      username: form.value.username,
      email: form.value.email,
      department: form.value.department,
      password: form.value.password
    })
    router.push('/login?registered=true')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
