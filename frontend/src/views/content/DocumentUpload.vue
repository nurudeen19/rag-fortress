<template>
  <div class="w-full">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-fortress-100 mb-2">Upload Document</h1>
      <p class="text-fortress-400">Add a new document to the knowledge base</p>
    </div>

    <!-- General Instruction Banner -->
    <div class="mb-6 p-4 bg-secure/10 border border-secure/50 rounded-lg">
      <div class="flex gap-3">
        <svg class="w-5 h-5 text-secure flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0zM8 7a1 1 0 000 2h6a1 1 0 000-2H8zm0 3a1 1 0 000 2h6a1 1 0 000-2H8z" clip-rule="evenodd" />
        </svg>
        <div>
          <p class="font-semibold text-secure mb-1">Upload Guidelines</p>
          <p class="text-sm text-fortress-300">Upload documents that contain clear, well-structured content. Avoid images, scanned documents without text, and files with poor formatting. Supported formats: JSON, CSV, Excel, Word, PDF, Text, and Markdown. For best results, ensure documents are clearly formatted with proper headings and sections.</p>
        </div>
      </div>
    </div>

    <!-- Upload Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Form -->
      <div class="lg:col-span-2">
        <div class="card">
          <!-- File Upload Section -->
          <div class="mb-8">
            <label class="block text-lg font-semibold text-fortress-100 mb-4">
              Choose Document
            </label>
            
            <!-- Drag and Drop Area -->
            <div
              @drop.prevent="handleDrop"
              @dragover.prevent="dragActive = true"
              @dragleave.prevent="dragActive = false"
              :class="[
                'relative border-2 border-dashed rounded-lg p-12 transition-all cursor-pointer',
                dragActive
                  ? 'border-secure bg-secure/10 scale-105'
                  : 'border-fortress-600 hover:border-fortress-500 bg-fortress-900/50'
              ]"
              @click="$refs.fileInput?.click()"
            >
              <input
                ref="fileInput"
                type="file"
                @change="handleFileSelect"
                accept=".json,.csv,.xlsx,.xls,.docx,.pdf,.txt,.md"
                class="hidden"
              />
              
              <div class="text-center">
                <svg
                  v-if="!form.file"
                  class="mx-auto h-16 w-16 text-fortress-500 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <svg
                  v-else
                  class="mx-auto h-16 w-16 text-success mb-4"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                </svg>

                <div class="mt-4">
                  <p class="text-fortress-100 font-semibold text-lg">
                    {{ form.file?.name || 'Click to upload or drag and drop' }}
                  </p>
                  <p v-if="!form.file" class="text-fortress-500 text-sm mt-2">
                    JSON, CSV, Excel, Word, PDF, Text, or Markdown files up to 50MB
                  </p>
                  <p v-else class="text-fortress-400 text-sm mt-2">
                    {{ formatFileSize(form.file.size) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- File Error -->
            <div v-if="fileError" class="mt-4 p-4 bg-alert/20 border border-alert/50 rounded-lg">
              <p class="text-alert text-sm font-medium">{{ fileError }}</p>
            </div>

            <!-- File Change Button -->
            <button
              v-if="form.file"
              @click="form.file = null"
              type="button"
              class="mt-4 px-4 py-2 text-sm text-fortress-300 hover:text-fortress-100 hover:bg-fortress-800 rounded-lg transition-colors"
            >
              Choose different file
            </button>
          </div>

          <!-- File Purpose -->
          <div class="mb-8">
            <label class="block text-sm font-semibold text-fortress-300 mb-3">
              File Purpose <span class="text-fortress-500 text-xs">(optional)</span>
            </label>
            <textarea
              v-model="form.purpose"
              placeholder="Describe what this document contains and how it should be used..."
              class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-4 py-3 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure focus:ring-1 focus:ring-secure/50 resize-none"
              rows="4"
            />
            <p class="text-fortress-500 text-xs mt-2">{{ form.purpose.length }}/1000 characters</p>
          </div>

          <!-- Field Selection for Structured Data -->
          <div v-if="isStructuredFile" class="mb-8">
            <div class="flex items-start gap-3 mb-3">
              <div>
                <label class="block text-sm font-semibold text-fortress-300 mb-2">
                  Select Fields <span class="text-fortress-500 text-xs">(optional)</span>
                </label>
                <p class="text-xs text-fortress-500">Choose specific columns/fields to extract. Leave empty to include all data.</p>
              </div>
            </div>

            <div v-if="availableFields.length > 0" class="space-y-2 max-h-48 overflow-y-auto p-4 bg-fortress-900/50 border border-fortress-700 rounded-lg">
              <label v-for="field in availableFields" :key="field" class="flex items-center space-x-3 cursor-pointer hover:bg-fortress-800/50 p-2 rounded transition-colors">
                <input
                  :checked="form.selectedFields.includes(field)"
                  type="checkbox"
                  class="w-4 h-4 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure"
                  @change="toggleField(field)"
                />
                <span class="text-sm text-fortress-300">{{ field }}</span>
              </label>
            </div>
            <div v-else class="p-4 bg-fortress-900/50 border border-fortress-700 rounded-lg text-center">
              <p class="text-fortress-500 text-sm">Upload a JSON, CSV, or Excel file to see available fields</p>
            </div>
          </div>

          <!-- Security Level -->
          <div class="mb-8">
            <label class="block text-sm font-semibold text-fortress-300 mb-3">
              Security Level
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                v-for="level in securityLevels"
                :key="level.value"
                @click="form.securityLevel = level.value"
                :class="[
                  'p-4 rounded-lg border-2 transition-all text-left',
                  form.securityLevel === level.value
                    ? 'border-secure bg-secure/10'
                    : 'border-fortress-600 hover:border-fortress-500 bg-fortress-800'
                ]"
              >
                <p class="font-medium text-fortress-100">{{ level.label }}</p>
                <p class="text-xs text-fortress-400 mt-1">{{ level.description }}</p>
              </button>
            </div>
          </div>

          <!-- Department & Access Control -->
          <div class="mb-8">
            <label class="block text-sm font-semibold text-fortress-300 mb-3">
              Department & Access <span class="text-fortress-500 text-xs">(optional)</span>
            </label>
            <div class="space-y-3">
              <select
                v-model="form.department"
                @change="form.isDepartmentOnly = false"
                class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-4 py-2 text-fortress-100 focus:outline-none focus:border-secure focus:ring-1 focus:ring-secure/50"
              >
                <option value="">No specific department</option>
                <option value="engineering">Engineering</option>
                <option value="product">Product</option>
                <option value="marketing">Marketing</option>
                <option value="finance">Finance</option>
                <option value="hr">Human Resources</option>
                <option value="operations">Operations</option>
              </select>

              <!-- Department-Only Toggle -->
              <label v-if="form.department" class="flex items-start space-x-3 cursor-pointer p-3 bg-fortress-900/50 border border-fortress-700 rounded-lg hover:bg-fortress-900 transition-colors">
                <input
                  v-model="form.isDepartmentOnly"
                  type="checkbox"
                  class="mt-1 w-4 h-4 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure"
                />
                <div>
                  <p class="text-sm font-medium text-fortress-100">Restrict to selected department only</p>
                  <p class="text-xs text-fortress-500 mt-1">Only members of {{ departmentLabel }} will be able to view and use this document</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Terms & Conditions -->
          <div class="mb-8 p-4 bg-fortress-900/50 border border-fortress-700 rounded-lg">
            <label class="flex items-start space-x-3 cursor-pointer">
              <input
                v-model="form.agreeTerms"
                type="checkbox"
                class="mt-1 w-4 h-4 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure"
              />
              <div>
                <p class="text-sm text-fortress-300">
                  I confirm this document is original, legally compliant, and I have rights to share it
                </p>
              </div>
            </label>
          </div>

          <!-- Action Buttons -->
          <div class="flex gap-3 pt-6 border-t border-fortress-700">
            <button
              @click="handleSubmit"
              :disabled="uploading || !form.file || !form.agreeTerms"
              :class="[
                'flex-1 px-6 py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2',
                uploading || !form.file || !form.agreeTerms
                  ? 'bg-fortress-700 text-fortress-500 cursor-not-allowed'
                  : 'bg-secure hover:bg-secure/90 text-white'
              ]"
            >
              <svg v-if="!uploading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19v-7m0 0V5m0 7H5m7 0h7" />
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ uploading ? 'Uploading...' : 'Upload Document' }}
            </button>
            <router-link
              to="/knowledge-base"
              class="px-6 py-3 rounded-lg font-medium text-fortress-300 hover:text-fortress-100 hover:bg-fortress-800 transition-colors"
            >
              Cancel
            </router-link>
          </div>
        </div>
      </div>

      <!-- Sidebar - Info & Tips -->
      <div class="lg:col-span-1">
        <!-- Document Info Card -->
        <div class="card mb-6">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Document Info</h3>
          <div v-if="form.file" class="space-y-3 text-sm">
            <div class="flex justify-between">
              <span class="text-fortress-400">File:</span>
              <span class="text-fortress-100 font-medium truncate">{{ form.file.name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-fortress-400">Size:</span>
              <span class="text-fortress-100">{{ formatFileSize(form.file.size) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-fortress-400">Type:</span>
              <span class="text-fortress-100">{{ getFileType(form.file.type) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-fortress-400">Security:</span>
              <span class="text-fortress-100 capitalize">{{ form.securityLevel }}</span>
            </div>
          </div>
          <div v-else class="text-fortress-500 text-sm">
            Select a file to see details
          </div>
        </div>

        <!-- Requirements Card -->
        <div class="card">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Supported Formats</h3>
          <div class="space-y-4 text-sm">
            <div>
              <p class="font-medium text-secure mb-2">Structured Data</p>
              <ul class="space-y-1 text-fortress-400">
                <li class="flex items-center gap-2">
                  <svg class="w-3 h-3 text-secure" fill="currentColor" viewBox="0 0 8 8">
                    <circle cx="4" cy="4" r="3" />
                  </svg>
                  JSON
                </li>
                <li class="flex items-center gap-2">
                  <svg class="w-3 h-3 text-secure" fill="currentColor" viewBox="0 0 8 8">
                    <circle cx="4" cy="4" r="3" />
                  </svg>
                  CSV
                </li>
                <li class="flex items-center gap-2">
                  <svg class="w-3 h-3 text-secure" fill="currentColor" viewBox="0 0 8 8">
                    <circle cx="4" cy="4" r="3" />
                  </svg>
                  Excel (XLSX, XLS)
                </li>
              </ul>
            </div>
            <div>
              <p class="font-medium text-fortress-300 mb-2">Text Documents</p>
              <ul class="space-y-1 text-fortress-400">
                <li class="flex items-center gap-2">
                  <svg class="w-3 h-3 text-fortress-400" fill="currentColor" viewBox="0 0 8 8">
                    <circle cx="4" cy="4" r="3" />
                  </svg>
                  PDF
                </li>
                <li class="flex items-center gap-2">
                  <svg class="w-3 h-3 text-fortress-400" fill="currentColor" viewBox="0 0 8 8">
                    <circle cx="4" cy="4" r="3" />
                  </svg>
                  Word (DOCX)
                </li>
                <li class="flex items-center gap-2">
                  <svg class="w-3 h-3 text-fortress-400" fill="currentColor" viewBox="0 0 8 8">
                    <circle cx="4" cy="4" r="3" />
                  </svg>
                  Text & Markdown
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Tips Card -->
        <div class="card mt-6">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Tips</h3>
          <ul class="space-y-2 text-sm text-fortress-400">
            <li class="flex items-start gap-2">
              <svg class="w-4 h-4 text-secure flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Max 50MB per file</span>
            </li>
            <li class="flex items-start gap-2">
              <svg class="w-4 h-4 text-secure flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Well-formatted content works best</span>
            </li>
            <li class="flex items-start gap-2">
              <svg class="w-4 h-4 text-secure flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Field selection available for structured data</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = reactive({
  file: null,
  purpose: '',
  securityLevel: 1,  // GENERAL by default
  department: '',
  isDepartmentOnly: false,
  selectedFields: [],
  agreeTerms: false
})

const dragActive = ref(false)
const uploading = ref(false)
const fileError = ref('')
const availableFields = ref([])

// Security levels matching backend SecurityLevel enum
const securityLevels = [
  { value: 1, label: 'General', description: 'No restrictions - organization-wide' },
  { value: 2, label: 'Restricted', description: 'Internal use only' },
  { value: 3, label: 'Confidential', description: 'Restricted access required' },
  { value: 4, label: 'Highly Confidential', description: 'Highly restricted access' }
]

const departments = [
  { id: '', name: 'No specific department' },
  { id: 'engineering', name: 'Engineering' },
  { id: 'product', name: 'Product' },
  { id: 'marketing', name: 'Marketing' },
  { id: 'finance', name: 'Finance' },
  { id: 'hr', name: 'Human Resources' },
  { id: 'operations', name: 'Operations' }
]

// Supported file types with their MIME types
const supportedFormats = {
  structured: {
    'application/json': 'json',
    'text/csv': 'csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.ms-excel': 'xls'
  },
  text: {
    'application/pdf': 'pdf',
    'text/plain': 'txt',
    'text/markdown': 'md',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/msword': 'doc'
  }
}

// Computed
const isStructuredFile = computed(() => {
  if (!form.file) return false
  return Object.keys(supportedFormats.structured).includes(form.file.type)
})

const departmentLabel = computed(() => {
  const dept = departments.find(d => d.id === form.department)
  return dept ? dept.name : form.department
})

// Helper functions
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const getFileType = (mimeType) => {
  if (!mimeType) return 'Unknown'
  
  // Check structured types
  if (supportedFormats.structured[mimeType]) {
    return supportedFormats.structured[mimeType].toUpperCase()
  }
  
  // Check text types
  if (supportedFormats.text[mimeType]) {
    return supportedFormats.text[mimeType].toUpperCase()
  }
  
  return 'File'
}

const getAllowedMimeTypes = () => {
  return [
    ...Object.keys(supportedFormats.structured),
    ...Object.keys(supportedFormats.text)
  ]
}

const extractFieldsFromFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target.result
      
      if (file.type === 'application/json') {
        const data = JSON.parse(content)
        if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
          availableFields.value = Object.keys(data[0])
        } else if (typeof data === 'object') {
          availableFields.value = Object.keys(data)
        }
      } else if (file.type === 'text/csv') {
        const lines = content.split('\n')
        if (lines.length > 0) {
          availableFields.value = lines[0].split(',').map(f => f.trim())
        }
      }
    } catch (error) {
      console.error('Error extracting fields:', error)
      availableFields.value = []
    }
  }
  reader.readAsText(file)
}

const toggleField = (field) => {
  const index = form.selectedFields.indexOf(field)
  if (index > -1) {
    form.selectedFields.splice(index, 1)
  } else {
    form.selectedFields.push(field)
  }
}

// File handling
const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    validateAndSetFile(file)
  }
}

const handleDrop = (event) => {
  dragActive.value = false
  const file = event.dataTransfer.files?.[0]
  if (file) {
    validateAndSetFile(file)
  }
}

const validateAndSetFile = (file) => {
  fileError.value = ''
  availableFields.value = []
  form.selectedFields = []

  // Check file size
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    fileError.value = `File is too large. Maximum size is 50MB. Your file is ${formatFileSize(file.size)}.`
    return
  }

  // Check file type
  const allowedMimeTypes = getAllowedMimeTypes()
  if (!allowedMimeTypes.includes(file.type)) {
    fileError.value = `File type not supported. Allowed types: JSON, CSV, Excel, PDF, Word, Text, Markdown`
    return
  }

  form.file = file

  // Extract fields if structured format
  if (isStructuredFile.value) {
    extractFieldsFromFile(file)
  }
}

// Validation
const canSubmit = computed(() => {
  return form.file && form.agreeTerms
})

const getValidationErrors = () => {
  const errors = []
  if (!form.file) errors.push('Please select a file')
  if (!form.agreeTerms) errors.push('Please agree to the terms')
  return errors
}

// Submit
const handleSubmit = async () => {
  const errors = getValidationErrors()
  if (errors.length > 0) {
    fileError.value = errors.join(', ')
    return
  }

  uploading.value = true

  try {
    // Simulate upload processing
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Create FormData for multipart upload
    const formData = new FormData()
    formData.append('file', form.file)
    formData.append('file_purpose', form.purpose)
    formData.append('security_level', form.securityLevel)
    formData.append('department_id', form.department)
    formData.append('is_department_only', form.isDepartmentOnly)
    
    // Add field selection for structured data
    if (form.selectedFields.length > 0) {
      formData.append('field_selection', JSON.stringify(form.selectedFields))
    }

    // TODO: Call your backend API here
    // const response = await fetch('/api/v1/files/upload', {
    //   method: 'POST',
    //   body: formData,
    //   headers: {
    //     'Authorization': `Bearer ${token}`
    //   }
    // })
    // const data = await response.json()

    console.log('Upload data:', {
      file: form.file.name,
      purpose: form.purpose,
      security_level: form.securityLevel,
      department: form.department,
      is_department_only: form.isDepartmentOnly,
      selected_fields: form.selectedFields,
      file_type: form.file.type
    })

    // Show success message and redirect
    uploading.value = false
    router.push('/knowledge-base?status=pending')
  } catch (error) {
    console.error('Upload error:', error)
    fileError.value = error.message || 'Upload failed'
    uploading.value = false
  }
}
</script>

<style scoped>
.card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.5) 100%);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.5rem;
  padding: 1.5rem;
}
</style>
