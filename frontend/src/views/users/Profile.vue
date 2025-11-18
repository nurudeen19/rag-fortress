<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-start">
      <div>
        <h1 class="text-3xl font-bold text-fortress-100">My Profile</h1>
        <p class="text-fortress-400 mt-1">View and manage your profile information</p>
      </div>
      <button
        v-if="!isEditing"
        @click="isEditing = true"
        class="px-4 py-2 bg-secure text-white rounded-lg hover:bg-secure/90 transition-colors font-medium"
      >
        Edit Profile
      </button>
      <div v-else class="flex gap-2">
        <button
          @click="handleCancel"
          class="px-4 py-2 bg-fortress-800 text-fortress-300 rounded-lg hover:bg-fortress-700 transition-colors font-medium"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          :disabled="saving"
          class="px-4 py-2 bg-secure text-white rounded-lg hover:bg-secure/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="p-4 bg-alert/10 border border-alert/30 rounded-xl text-alert text-sm flex items-start gap-3">
      <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
      </svg>
      <div>
        <p class="font-medium">Error</p>
        <p class="text-xs mt-1">{{ error }}</p>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="p-4 bg-secure/10 border border-secure/30 rounded-xl text-secure text-sm flex items-start gap-3">
      <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
      </svg>
      <div>
        <p class="font-medium">Success</p>
        <p class="text-xs mt-1">{{ successMessage }}</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="text-center">
        <div class="inline-block w-12 h-12 mb-4 border-2 border-fortress-700 border-t-secure rounded-full animate-spin"></div>
        <p class="text-fortress-400">Loading profile...</p>
      </div>
    </div>

    <!-- Profile Content -->
    <div v-else-if="profile" class="space-y-6">
      <!-- Account Section -->
      <div class="bg-fortress-900 rounded-xl border border-fortress-800 p-6 space-y-6">
        <div>
          <h2 class="text-xl font-semibold text-fortress-100 mb-4 flex items-center gap-2">
            <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Account Information
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Username (Read-only) -->
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">Username</label>
              <div class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
                {{ profile.username }}
              </div>
              <p class="text-xs text-fortress-500 mt-1">Cannot be changed</p>
            </div>

            <!-- Email (Read-only) -->
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">Email</label>
              <div class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
                {{ profile.email }}
              </div>
              <p class="text-xs text-fortress-500 mt-1">Verified: {{ profile.is_verified ? '✓' : '✗' }}</p>
            </div>

            <!-- First Name (Editable) -->
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">First Name</label>
              <input
                v-if="isEditing"
                v-model="form.first_name"
                type="text"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
              />
              <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
                {{ profile.first_name }}
              </div>
            </div>

            <!-- Last Name (Editable) -->
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">Last Name</label>
              <input
                v-if="isEditing"
                v-model="form.last_name"
                type="text"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
              />
              <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
                {{ profile.last_name }}
              </div>
            </div>
          </div>
        </div>

        <!-- Status Information -->
        <div class="border-t border-fortress-700 pt-6">
          <h3 class="text-sm font-medium text-fortress-300 mb-3">Account Status</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full" :class="profile.is_active ? 'bg-success' : 'bg-alert'"></div>
              <span class="text-sm text-fortress-300">
                {{ profile.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full" :class="profile.is_suspended ? 'bg-alert' : 'bg-success'"></div>
              <span class="text-sm text-fortress-300">
                {{ profile.is_suspended ? 'Suspended' : 'Not Suspended' }}
              </span>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 rounded-full" :class="profile.is_verified ? 'bg-success' : 'bg-alert'"></div>
              <span class="text-sm text-fortress-300">
                {{ profile.is_verified ? 'Email Verified' : 'Email Not Verified' }}
              </span>
            </div>
          </div>
          <div v-if="profile.is_suspended && profile.suspension_reason" class="mt-4 p-3 bg-alert/10 border border-alert/30 rounded-lg">
            <p class="text-xs font-medium text-alert mb-1">Suspension Reason</p>
            <p class="text-xs text-fortress-300">{{ profile.suspension_reason }}</p>
          </div>
        </div>
      </div>

      <!-- Organization Section (Read-only) -->
      <div class="bg-fortress-900 rounded-xl border border-fortress-800 p-6 space-y-4">
        <h2 class="text-xl font-semibold text-fortress-100 flex items-center gap-2">
          <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5.5M9 21H3.5M21 19v2h2M1 19v2"/>
          </svg>
          Organization
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Department (Read-only) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">Department</label>
            <div class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
              {{ profile.department?.name || 'Not assigned' }}
            </div>
            <p class="text-xs text-fortress-500 mt-1">Admin controlled</p>
          </div>

          <!-- Roles (Read-only) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">Roles</label>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="role in profile.roles"
                :key="role.id"
                class="px-3 py-1 bg-secure/10 border border-secure/30 text-secure rounded-full text-xs font-medium"
              >
                {{ role.name }}
              </span>
              <span v-if="!profile.roles.length" class="text-fortress-500 text-sm">No roles assigned</span>
            </div>
            <p class="text-xs text-fortress-500 mt-1">Admin controlled</p>
          </div>
        </div>
      </div>

      <!-- Professional Section (Editable) -->
      <div class="bg-fortress-900 rounded-xl border border-fortress-800 p-6 space-y-4">
        <h2 class="text-xl font-semibold text-fortress-100 flex items-center gap-2">
          <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.728 0-7.333-.57-10.759-1.697m0 0a23.97 23.97 0 003.674-5.652m0 0h.01m0 0A23.971 23.971 0 0112 3c3.728 0 7.333.57 10.759 1.697m0 0a23.97 23.97 0 00-3.674-5.652m0 0h.01"/>
          </svg>
          Professional Information
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Job Title (Editable) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">Job Title</label>
            <input
              v-if="isEditing"
              v-model="form.job_title"
              type="text"
              placeholder="e.g., Senior Engineer"
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
            />
            <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
              {{ profile.job_title || 'Not specified' }}
            </div>
          </div>

          <!-- Location (Editable) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">Location</label>
            <input
              v-if="isEditing"
              v-model="form.location"
              type="text"
              placeholder="e.g., San Francisco, CA"
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
            />
            <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
              {{ profile.location || 'Not specified' }}
            </div>
          </div>

          <!-- Phone Number (Editable) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">Phone Number</label>
            <input
              v-if="isEditing"
              v-model="form.phone_number"
              type="tel"
              placeholder="e.g., +1 (555) 123-4567"
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
            />
            <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100">
              {{ profile.phone_number || 'Not specified' }}
            </div>
          </div>

          <!-- Avatar URL (Editable) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">Avatar URL</label>
            <input
              v-if="isEditing"
              v-model="form.avatar_url"
              type="url"
              placeholder="https://example.com/avatar.jpg"
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
            />
            <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100 truncate">
              {{ profile.avatar_url || 'Not specified' }}
            </div>
          </div>
        </div>

        <!-- About (Editable) -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">About</label>
          <textarea
            v-if="isEditing"
            v-model="form.about"
            placeholder="Tell us about yourself..."
            rows="4"
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
          ></textarea>
          <div v-else class="px-3 py-2 bg-fortress-800/50 border border-fortress-700 rounded-lg text-fortress-100 whitespace-pre-wrap">
            {{ profile.about || 'Not specified' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const profile = ref(null)
const loading = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const error = ref('')
const successMessage = ref('')

const form = ref({
  first_name: '',
  last_name: '',
  phone_number: '',
  location: '',
  job_title: '',
  about: '',
  avatar_url: ''
})

const loadProfile = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await api.get('/v1/auth/me')
    
    // Response from api.get already extracts response.data due to interceptor
    if (response && response.id) {
      profile.value = response
      // Initialize form with current data
      form.value = {
        first_name: profile.value.first_name || '',
        last_name: profile.value.last_name || '',
        phone_number: profile.value.phone_number || '',
        location: profile.value.location || '',
        job_title: profile.value.job_title || '',
        about: profile.value.about || '',
        avatar_url: profile.value.avatar_url || ''
      }
    } else {
      error.value = 'Failed to load profile'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load profile'
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  error.value = ''
  successMessage.value = ''
  
  try {
    const response = await api.put('/v1/auth/me', form.value)
    
    // Response from api.put already extracts response.data due to interceptor
    if (response && response.id) {
      profile.value = response
      isEditing.value = false
      successMessage.value = 'Profile updated successfully'
      // Auto-hide success message
      setTimeout(() => {
        successMessage.value = ''
      }, 3000)
    } else {
      error.value = 'Failed to update profile'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.response?.data?.error || 'Failed to update profile'
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  isEditing.value = false
  // Reset form to current profile data
  if (profile.value) {
    form.value = {
      first_name: profile.value.first_name || '',
      last_name: profile.value.last_name || '',
      phone_number: profile.value.phone_number || '',
      location: profile.value.location || '',
      job_title: profile.value.job_title || '',
      about: profile.value.about || '',
      avatar_url: profile.value.avatar_url || ''
    }
  }
}

onMounted(() => {
  loadProfile()
})
</script>
