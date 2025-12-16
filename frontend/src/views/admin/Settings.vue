<template>
  <div class="h-full flex flex-col">
    <!-- Header with Back Navigation -->
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-3">
        <router-link 
          to="/configuration" 
          class="p-2 hover:bg-fortress-700 rounded-lg transition-colors"
          title="Back to System Settings"
        >
          <svg class="w-5 h-5 text-fortress-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
          </svg>
        </router-link>
        <div>
          <h1 class="text-2xl font-bold text-fortress-100">Application Settings</h1>
          <p class="text-fortress-400 text-sm">Configure system-wide settings for LLM, embeddings, caching, and more.</p>
        </div>
      </div>
      <div class="space-y-3">
        <div class="p-3 bg-info/10 border border-info/30 rounded-lg text-sm text-fortress-300">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-info flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
            <div>
              <strong class="text-info">How it works:</strong> Make changes to any editable setting below. 
              Changes are tracked and shown with a "Reset" button. Click "Save Changes" at the bottom to apply all modifications.
            </div>
          </div>
        </div>
        
        <div class="p-3 bg-warning/10 border border-warning/30 rounded-lg text-sm text-fortress-300">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-warning flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
            </svg>
            <div>
              <strong class="text-warning">Security:</strong> Settings marked with 
              <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-warning/20 text-warning rounded text-xs mx-1">
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                </svg>
                Encrypted
              </span>
              are automatically encrypted in the database and cache. API keys, passwords, and secrets are stored securely and only decrypted when needed.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center h-64">
      <div class="flex flex-col items-center gap-4">
        <svg class="animate-spin h-10 w-10 text-secure" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-fortress-400">Loading settings...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card p-6 bg-error/10 border-error/30">
      <div class="flex items-start gap-3">
        <svg class="w-6 h-6 text-error flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        <div>
          <h3 class="font-semibold text-error mb-1">Failed to load settings</h3>
          <p class="text-fortress-300 text-sm">{{ error }}</p>
          <button @click="loadSettings" class="mt-3 px-4 py-2 bg-error hover:bg-error/90 text-white rounded-lg text-sm font-medium transition-colors">
            Retry
          </button>
        </div>
      </div>
    </div>

    <!-- Settings Content -->
    <div v-else class="flex-1 flex flex-col gap-4">
      <!-- Status Message -->
      <div v-if="statusMessage.text" 
           class="p-4 rounded-lg text-sm flex items-start justify-between gap-3" 
           :class="statusMessage.type === 'success' ? 'bg-secure/20 text-secure border border-secure/30' : 'bg-error/20 text-error border border-error/30'">
        <div class="flex items-start gap-3 flex-1">
          <svg v-if="statusMessage.type === 'success'" class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <svg v-else class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>
          <span class="flex-1">{{ statusMessage.text }}</span>
        </div>
        <button 
          @click="statusMessage = { type: null, text: null }"
          class="p-1 hover:bg-black/10 rounded transition-colors flex-shrink-0"
          title="Dismiss"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <!-- Category Tabs -->
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="category in categories"
          :key="category"
          @click="selectedCategory = category"
          class="px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors"
          :class="selectedCategory === category 
            ? 'bg-secure text-white' 
            : 'bg-fortress-800 text-fortress-300 hover:bg-fortress-700'"
        >
          {{ formatCategoryName(category) }}
        </button>
      </div>

      <!-- Settings Grid -->
      <div class="card p-6 flex-1 overflow-y-auto">
        <div class="space-y-6">
          <div v-for="setting in filteredSettings" :key="setting.id" class="border-b border-fortress-700 last:border-0 pb-6 last:pb-0">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <label class="font-medium text-fortress-100">{{ formatSettingName(setting.key) }}</label>
                  <span v-if="!setting.is_mutable" class="text-xs px-2 py-0.5 bg-fortress-700 text-fortress-300 rounded">Read-only</span>
                  <span v-if="setting.is_sensitive" class="text-xs px-2 py-0.5 bg-warning/20 text-warning rounded flex items-center gap-1" title="This setting is encrypted in the database">
                    <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                    </svg>
                    Encrypted
                  </span>
                  <span class="text-xs px-2 py-0.5 bg-fortress-700 text-fortress-400 rounded font-mono">{{ setting.data_type }}</span>
                </div>
                <p v-if="setting.description" class="text-sm text-fortress-400 mb-3">{{ setting.description }}</p>
                
                <!-- Input field based on data type -->
                <div class="flex items-center gap-3">
                  <!-- Boolean input -->
                  <div v-if="setting.data_type === 'boolean'" class="flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      :id="`setting-${setting.id}`"
                      v-model="editedValues[setting.key]"
                      :disabled="!setting.is_mutable || isSaving"
                      class="w-5 h-5 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure focus:ring-2"
                    />
                    <label :for="`setting-${setting.id}`" class="text-sm text-fortress-300 cursor-pointer">
                      {{ editedValues[setting.key] ? 'Enabled' : 'Disabled' }}
                    </label>
                  </div>

                  <!-- JSON input -->
                  <textarea 
                    v-else-if="setting.data_type === 'json'"
                    v-model="editedValues[setting.key]"
                    :disabled="!setting.is_mutable || isSaving"
                    rows="3"
                    class="w-full px-3 py-2 bg-fortress-800 border border-fortress-600 rounded-lg text-fortress-100 text-sm font-mono disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-secure"
                  ></textarea>

                  <!-- Text/Number/Float input -->
                  <input 
                    v-else
                    :type="setting.is_sensitive && !isEditingPassword[setting.key] ? 'password' : (setting.data_type === 'integer' || setting.data_type === 'float' ? 'number' : 'text')"
                    :step="setting.data_type === 'float' ? '0.1' : '1'"
                    v-model="editedValues[setting.key]"
                    :disabled="!setting.is_mutable || isSaving"
                    :placeholder="setting.is_sensitive ? '••••••••••••••••' : ''"
                    class="flex-1 px-3 py-2 bg-fortress-800 border border-fortress-600 rounded-lg text-fortress-100 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-secure"
                  />
                  <button 
                    v-if="setting.is_sensitive && setting.is_mutable"
                    @click="togglePasswordVisibility(setting.key)"
                    type="button"
                    class="p-2 hover:bg-fortress-700 rounded-lg transition-colors"
                    :title="isEditingPassword[setting.key] ? 'Hide value' : 'Show value'"
                  >
                    <svg v-if="isEditingPassword[setting.key]" class="w-5 h-5 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                    </svg>
                    <svg v-else class="w-5 h-5 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Actions -->
              <div v-if="setting.is_mutable && hasChanged(setting.key, setting.value)" class="flex items-center gap-2">
                <button 
                  @click="resetValue(setting.key, setting.value)"
                  :disabled="isSaving"
                  class="px-3 py-1.5 bg-fortress-700 hover:bg-fortress-600 text-fortress-200 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  title="Reset to original value"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          <!-- No settings message -->
          <div v-if="filteredSettings.length === 0" class="text-center py-12">
            <svg class="w-12 h-12 text-fortress-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <p class="text-fortress-400">No settings found in this category</p>
          </div>
        </div>
      </div>

      <!-- Actions Footer -->
      <div v-if="hasAnyChanges" class="card p-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <svg class="w-5 h-5 text-warning" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
          </svg>
          <span class="text-fortress-200 font-medium">You have unsaved changes</span>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="discardChanges"
            :disabled="isSaving"
            class="px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-200 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            Discard
          </button>
          <button 
            @click="saveChanges"
            :disabled="isSaving"
            class="px-4 py-2 bg-secure hover:bg-secure/90 text-white rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <svg v-if="isSaving" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isSaving ? 'Saving...' : 'Save Changes' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

// State
const isLoading = ref(true)
const isSaving = ref(false)
const error = ref(null)
const settings = ref([])
const categories = ref([])
const selectedCategory = ref(null)
const editedValues = ref({})
const statusMessage = ref({ type: null, text: null })
const isEditingPassword = ref({})

// Computed
const filteredSettings = computed(() => {
  if (!selectedCategory.value) return []
  return settings.value.filter(s => s.category === selectedCategory.value)
})

const hasAnyChanges = computed(() => {
  return settings.value.some(setting => hasChanged(setting.key, setting.value))
})

// Methods
function formatCategoryName(category) {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatSettingName(key) {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function togglePasswordVisibility(key) {
  isEditingPassword.value[key] = !isEditingPassword.value[key]
}

function hasChanged(key, originalValue) {
  const edited = editedValues.value[key]
  if (edited === undefined) return false
  
  // Handle null original values
  const safeOriginalValue = originalValue || ''
  
  // Convert boolean strings to actual booleans for comparison
  if (typeof edited === 'boolean') {
    const originalBool = safeOriginalValue.toLowerCase() === 'true'
    return edited !== originalBool
  }
  
  return String(edited) !== String(safeOriginalValue)
}

function resetValue(key, originalValue) {
  const setting = settings.value.find(s => s.key === key)
  if (setting.data_type === 'boolean') {
    editedValues.value[key] = originalValue ? originalValue.toLowerCase() === 'true' : false
  } else {
    editedValues.value[key] = originalValue || ''
  }
}

function discardChanges() {
  settings.value.forEach(setting => {
    if (setting.data_type === 'boolean') {
      editedValues.value[setting.key] = setting.value ? setting.value.toLowerCase() === 'true' : false
    } else {
      editedValues.value[setting.key] = setting.value || ''
    }
  })
  
  statusMessage.value = { type: 'success', text: 'Changes discarded' }
  setTimeout(() => {
    statusMessage.value = { type: null, text: null }
  }, 3000)
}

async function saveChanges() {
  isSaving.value = true
  statusMessage.value = { type: null, text: null }
  
  try {
    // Collect changed settings
    const updates = []
    settings.value.forEach(setting => {
      if (hasChanged(setting.key, setting.value)) {
        let newValue = editedValues.value[setting.key]
        
        // Convert to string for API
        if (typeof newValue === 'boolean') {
          newValue = newValue ? 'true' : 'false'
        } else {
          newValue = String(newValue)
        }
        
        updates.push({ key: setting.key, value: newValue })
      }
    })
    
    if (updates.length === 0) {
      statusMessage.value = { type: 'success', text: 'No changes to save' }
      return
    }
    
    // Bulk update
    const response = await api.put('/v1/settings', { updates })
    
    if (response.error_count > 0) {
      statusMessage.value = { 
        type: 'error', 
        text: `Saved ${response.success_count} settings, ${response.error_count} errors` 
      }
    } else {
      statusMessage.value = { 
        type: 'success', 
        text: `Successfully saved ${response.success_count} setting(s)` 
      }
    }
    
    // Reload settings to get fresh data
    await loadSettings()
    
    // Clear SUCCESS message after 5 seconds, keep ERROR messages visible
    setTimeout(() => {
      if (statusMessage.value.type === 'success') {
        statusMessage.value = { type: null, text: null }
      }
    }, 5000)
    
  } catch (err) {
    console.error('Settings save error:', err)
    console.error('Error response:', err.response)
    
    const errorMessage = err.response?.data?.detail || err.message || 'Failed to save settings'
    statusMessage.value = { type: 'error', text: errorMessage }
    
    // Don't auto-clear error messages - let user dismiss them
    // setTimeout(() => {
    //   statusMessage.value = { type: null, text: null }
    // }, 10000)
  } finally {
    isSaving.value = false
  }
}

async function loadSettings() {
  isLoading.value = true
  error.value = null
  
  try {
    // Load all settings
    const settingsData = await api.get('/v1/settings')
    settings.value = settingsData
    
    // Load categories
    const categoriesData = await api.get('/v1/settings/categories')
    categories.value = categoriesData
    
    // Set initial category
    if (categories.value.length > 0 && !selectedCategory.value) {
      selectedCategory.value = categories.value[0]
    }
    
    // Initialize edited values and password visibility
    settings.value.forEach(setting => {
      if (setting.data_type === 'boolean') {
        editedValues.value[setting.key] = setting.value ? setting.value.toLowerCase() === 'true' : false
      } else {
        editedValues.value[setting.key] = setting.value || ''
      }
      
      // Initialize password visibility (hidden by default for sensitive settings)
      if (setting.is_sensitive) {
        isEditingPassword.value[setting.key] = false
      }
    })
    
  } catch (err) {
    error.value = err.response?.data?.detail || 'An error occurred while loading settings'
  } finally {
    isLoading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.5) 100%);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.5rem;
}
</style>
