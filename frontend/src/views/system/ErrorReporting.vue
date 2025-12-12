<template>
  <div class="min-h-screen bg-fortress-950">
    <div class="max-w-3xl mx-auto p-6">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-fortress-100 mb-2">Report an Error</h1>
        <p class="text-fortress-400">
          Help us improve by reporting issues you encounter. Include as much detail as possible to help us resolve the problem faster.
        </p>
      </div>

      <!-- Admin Info Message -->
      <div v-if="authStore.isAdmin" class="card p-8 border border-blue-500/30 bg-blue-500/10 mb-6">
        <div class="flex items-start gap-4">
          <svg class="w-8 h-8 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="text-xl font-semibold text-blue-300 mb-2">Administrator Access</h3>
            <p class="text-fortress-200 mb-3">
              As an administrator, you review and resolve error reports submitted by users. 
              You cannot submit error reports yourself.
            </p>
            <p class="text-fortress-300 text-sm">
              To view and manage error reports from users, please visit the Admin Dashboard.
            </p>
            <button
              @click="router.push('/admin')"
              class="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
            >
              Go to Admin Dashboard
            </button>
          </div>
        </div>
      </div>

      <!-- Form Card -->
      <div v-else class="card p-8 border border-fortress-700 mb-6">
        <form @submit.prevent="submitReport" class="space-y-6">
          <!-- Title Input -->
          <div>
            <label for="title" class="block text-sm font-medium text-fortress-300 mb-2">
              Error Title *
            </label>
            <input
              id="title"
              v-model="form.title"
              type="text"
              placeholder="Brief description of the error"
              maxlength="255"
              required
              class="w-full px-4 py-2 bg-fortress-900 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure transition-colors"
            />
            <p class="text-fortress-500 text-xs mt-1">{{ form.title.length }}/255 characters</p>
          </div>

          <!-- Category Selection -->
          <div>
            <label for="category" class="block text-sm font-medium text-fortress-300 mb-2">
              Error Category *
            </label>
            <select
              id="category"
              v-model="form.category"
              required
              class="w-full px-4 py-2 bg-fortress-900 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure transition-colors"
            >
              <option value="">Select a category...</option>
              <option value="llm_error">LLM Error - Issues with AI responses</option>
              <option value="retrieval_error">Retrieval Error - Document search problems</option>
              <option value="validation_error">Validation Error - Input validation failures</option>
              <option value="performance">Performance - Slow response or timeout</option>
              <option value="ui_ux">UI/UX - Interface or usability issues</option>
              <option value="permissions">Permissions - Access control problems</option>
              <option value="data_accuracy">Data Accuracy - Incorrect data or results</option>
              <option value="system_error">System Error - General system failures</option>
              <option value="other">Other - Miscellaneous issues</option>
            </select>
          </div>

          <!-- Description Textarea -->
          <div>
            <label for="description" class="block text-sm font-medium text-fortress-300 mb-2">
              Description *
            </label>
            <textarea
              id="description"
              v-model="form.description"
              placeholder="Please provide detailed information about the error, including:&#10;- What were you trying to do?&#10;- What error did you see?&#10;- When did it happen?&#10;- Can you reproduce it?"
              maxlength="2000"
              required
              rows="6"
              class="w-full px-4 py-2 bg-fortress-900 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure focus:outline-none focus:ring-1 focus:ring-secure transition-colors resize-none"
            ></textarea>
            <p class="text-fortress-500 text-xs mt-1">{{ form.description.length }}/2000 characters</p>
          </div>

          <!-- File Upload -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">
              Attach Screenshot (Optional)
            </label>
            <div
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleFileDrop"
              :class="[
                'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
                isDragging 
                  ? 'border-secure bg-secure/10' 
                  : 'border-fortress-700 hover:border-fortress-600 bg-fortress-900/50'
              ]"
            >
              <div v-if="!form.image" class="space-y-3">
                <svg class="mx-auto h-12 w-12 text-fortress-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                <div>
                  <p class="text-fortress-300 font-medium mb-1">Drop your image here or click to select</p>
                  <p class="text-fortress-500 text-sm">PNG, JPEG, GIF, or WebP (Max 5MB)</p>
                </div>
                <input
                  type="file"
                  accept="image/*"
                  @change="handleFileSelect"
                  class="hidden"
                  ref="fileInput"
                />
                <button
                  type="button"
                  @click="$refs.fileInput?.click()"
                  class="inline-block px-4 py-2 bg-fortress-800 hover:bg-fortress-700 text-fortress-100 rounded-lg text-sm font-medium transition-colors"
                >
                  Browse Files
                </button>
              </div>

              <!-- Image Preview -->
              <div v-else class="space-y-3">
                <img
                  :src="form.imagePreview"
                  :alt="form.image.name"
                  class="max-w-xs max-h-64 mx-auto rounded-lg border border-fortress-700"
                />
                <p class="text-fortress-300 text-sm">
                  {{ form.image.name }} ({{ (form.image.size / 1024).toFixed(2) }} KB)
                </p>
                <button
                  type="button"
                  @click="removeImage"
                  class="inline-block px-4 py-2 bg-error/20 hover:bg-error/30 text-error rounded-lg text-sm font-medium transition-colors"
                >
                  Remove Image
                </button>
              </div>
            </div>
          </div>

          <!-- Submit Buttons -->
          <div class="flex gap-3 justify-end pt-4">
            <button
              type="button"
              @click="resetForm"
              class="px-6 py-2 bg-fortress-800 hover:bg-fortress-700 text-fortress-100 rounded-lg font-medium transition-colors"
            >
              Clear
            </button>
            <button
              type="submit"
              :disabled="submitting || !form.title || !form.category || !form.description"
              class="px-6 py-2 bg-secure hover:bg-secure/90 disabled:bg-fortress-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <svg v-if="submitting" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ submitting ? 'Submitting...' : 'Submit Report' }}</span>
            </button>
          </div>

          <!-- Error Messages -->
          <div v-if="formError" class="mt-4 p-4 bg-error/20 border border-error/50 rounded-lg text-error text-sm">
            {{ formError }}
          </div>
        </form>
      </div>

      <!-- Success Message -->
      <div v-if="showSuccess" class="card p-6 bg-green-500/10 border border-green-500/30">
        <div class="flex items-start gap-4">
          <svg class="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <div>
            <h3 class="font-semibold text-green-400 mb-1">Error Report Submitted Successfully</h3>
            <p class="text-green-300 text-sm mb-3">
              Thank you for reporting this issue. We've received your report and will review it shortly. You can track the status in your error reports history.
            </p>
            <button
              @click="viewReports"
              class="text-green-300 hover:text-green-200 text-sm font-medium underline transition-colors"
            >
              View Your Reports
            </button>
          </div>
        </div>
      </div>

      <!-- Info Box -->
      <div class="mt-8 card p-6 bg-fortress-800/30 border-fortress-700">
        <div class="flex items-start gap-4">
          <svg class="w-6 h-6 text-info flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <div>
            <h3 class="font-semibold text-fortress-100 mb-2">Tips for Better Reports</h3>
            <ul class="text-fortress-400 text-sm space-y-1">
              <li>✓ Be specific about what you were doing when the error occurred</li>
              <li>✓ Include error messages or codes if visible</li>
              <li>✓ Attach a screenshot to help us understand the issue</li>
              <li>✓ Mention if you can reproduce the error consistently</li>
              <li>✓ Include any relevant document IDs or conversation references</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { userErrorReporting } from '@/services/errorReporting'

const router = useRouter()
const authStore = useAuthStore()

// State
const form = ref({
  title: '',
  category: '',
  description: '',
  image: null,
  imagePreview: null
})

const submitting = ref(false)
const formError = ref(null)
const showSuccess = ref(false)
const isDragging = ref(false)
const fileInput = ref(null)

// Methods
const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    processFile(file)
  }
}

const handleFileDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file) {
    processFile(file)
  }
}

const processFile = (file) => {
  // Validate file type
  const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    formError.value = 'Only PNG, JPEG, GIF, and WebP images are allowed'
    return
  }

  // Validate file size (5MB)
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    formError.value = 'File size exceeds 5MB limit'
    return
  }

  form.value.image = file
  formError.value = null

  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.imagePreview = e.target.result
  }
  reader.readAsDataURL(file)
}

const removeImage = () => {
  form.value.image = null
  form.value.imagePreview = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const resetForm = (preserveSuccess = false) => {
  form.value = {
    title: '',
    category: '',
    description: '',
    image: null,
    imagePreview: null
  }
  formError.value = null
  if (!preserveSuccess) {
    showSuccess.value = false
  }
}

const submitReport = async () => {
  submitting.value = true
  formError.value = null

  try {
    // Create error report
    const response = await userErrorReporting.createReport({
      title: form.value.title,
      category: form.value.category,
      description: form.value.description,
      conversation_id: null
    })

    const reportId = response.id

    // Upload image if present
    if (form.value.image) {
      try {
        await userErrorReporting.uploadImage(reportId, form.value.image)
      } catch (err) {
        console.error('Error uploading image:', err)
        // Don't fail the entire submission if image upload fails
      }
    }

    // Show success and keep message on screen
    showSuccess.value = true
    resetForm(true)
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Failed to submit error report. Please try again.'
    console.error('Error submitting report:', err)
  } finally {
    submitting.value = false
  }
}

const viewReports = () => {
  router.push({ name: 'error-reports' })
}
</script>

<style scoped>
.card {
  @apply bg-fortress-900 rounded-lg;
}
</style>
