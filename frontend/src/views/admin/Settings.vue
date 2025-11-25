<template>
  <div class="h-full flex flex-col">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-fortress-100 mb-2">Application Settings</h1>
      <p class="text-fortress-400">Configure system-wide settings for LLM, embeddings, caching, and more.</p>
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
           class="p-4 rounded-lg text-sm flex items-start gap-3" 
           :class="statusMessage.type === 'success' ? 'bg-secure/20 text-secure border border-secure/30' : 'bg-error/20 text-error border border-error/30'">
        <svg v-if="statusMessage.type === 'success'" class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <svg v-else class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        <span>{{ statusMessage.text }}</span>
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
                    :type="setting.data_type === 'integer' || setting.data_type === 'float' ? 'number' : 'text'"
                    :step="setting.data_type === 'float' ? '0.1' : '1'"
                    v-model="editedValues[setting.key]"
                    :disabled="!setting.is_mutable || isSaving"
                    class="flex-1 px-3 py-2 bg-fortress-800 border border-fortress-600 rounded-lg text-fortress-100 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-secure"
                  />
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

function hasChanged(key, originalValue) {
  const edited = editedValues.value[key]
  if (edited === undefined) return false
  
  // Convert boolean strings to actual booleans for comparison
  if (typeof edited === 'boolean') {
    const originalBool = originalValue.toLowerCase() === 'true'
    return edited !== originalBool
  }
  
  return String(edited) !== String(originalValue)
}

function resetValue(key, originalValue) {
  const setting = settings.value.find(s => s.key === key)
  if (setting.data_type === 'boolean') {
    editedValues.value[key] = originalValue.toLowerCase() === 'true'
  } else {
    editedValues.value[key] = originalValue
  }
}

function discardChanges() {
  settings.value.forEach(setting => {
    if (setting.data_type === 'boolean') {
      editedValues.value[setting.key] = setting.value.toLowerCase() === 'true'
    } else {
      editedValues.value[setting.key] = setting.value
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
    
    // Clear message after 5 seconds
    setTimeout(() => {
      statusMessage.value = { type: null, text: null }
    }, 5000)
    
  } catch (err) {
    const errorMessage = err.response?.data?.detail || 'Failed to save settings'
    statusMessage.value = { type: 'error', text: errorMessage }
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
    
    // Initialize edited values
    settings.value.forEach(setting => {
      if (setting.data_type === 'boolean') {
        editedValues.value[setting.key] = setting.value.toLowerCase() === 'true'
      } else {
        editedValues.value[setting.key] = setting.value
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
