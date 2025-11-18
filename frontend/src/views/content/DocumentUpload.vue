<template>
  <div class="w-full">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-fortress-100 mb-2">Upload Document</h1>
      <p class="text-fortress-400">Add a new document to the knowledge base</p>
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
                accept=".pdf,.txt,.docx,.xlsx,.md"
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
                    PDF, TXT, DOCX, XLSX, or MD files up to 50MB
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

          <!-- Security Level -->
          <div class="mb-8">
            <label class="block text-sm font-semibold text-fortress-300 mb-3">
              Security Level
            </label>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
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

          <!-- Department -->
          <div class="mb-8">
            <label class="block text-sm font-semibold text-fortress-300 mb-3">
              Department <span class="text-fortress-500 text-xs">(optional)</span>
            </label>
            <select
              v-model="form.department"
              class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-4 py-2 text-fortress-100 focus:outline-none focus:border-secure focus:ring-1 focus:ring-secure/50"
            >
              <option value="">Select a department</option>
              <option value="engineering">Engineering</option>
              <option value="product">Product</option>
              <option value="marketing">Marketing</option>
              <option value="finance">Finance</option>
              <option value="hr">Human Resources</option>
            </select>
          </div>

          <!-- Processing Settings -->
          <div class="mb-8 p-4 bg-fortress-900/50 border border-fortress-700 rounded-lg">
            <h3 class="text-sm font-semibold text-fortress-100 mb-4">Processing Options</h3>
            
            <div class="space-y-3">
              <label class="flex items-start space-x-3 cursor-pointer">
                <input
                  v-model="form.enableOCR"
                  type="checkbox"
                  class="mt-1 w-4 h-4 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure"
                />
                <div>
                  <p class="text-sm font-medium text-fortress-100">Enable OCR</p>
                  <p class="text-xs text-fortress-500">Extract text from scanned images</p>
                </div>
              </label>

              <label class="flex items-start space-x-3 cursor-pointer">
                <input
                  v-model="form.enableExtraction"
                  type="checkbox"
                  class="mt-1 w-4 h-4 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure"
                />
                <div>
                  <p class="text-sm font-medium text-fortress-100">Enable Data Extraction</p>
                  <p class="text-xs text-fortress-500">Extract structured data from document</p>
                </div>
              </label>

              <label class="flex items-start space-x-3 cursor-pointer">
                <input
                  v-model="form.makePublic"
                  type="checkbox"
                  class="mt-1 w-4 h-4 rounded bg-fortress-700 border-fortress-600 text-secure focus:ring-secure"
                />
                <div>
                  <p class="text-sm font-medium text-fortress-100">Make Public</p>
                  <p class="text-xs text-fortress-500">Allow all users to view this document</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Terms -->
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
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Requirements</h3>
          <ul class="space-y-2 text-sm text-fortress-400">
            <li class="flex items-start gap-2">
              <svg class="w-4 h-4 text-success flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>File max 50MB</span>
            </li>
            <li class="flex items-start gap-2">
              <svg class="w-4 h-4 text-success flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Supported formats: PDF, TXT, DOCX, XLSX, MD</span>
            </li>
            <li class="flex items-start gap-2">
              <svg class="w-4 h-4 text-success flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Agree to terms</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = reactive({
  file: null,
  purpose: '',
  securityLevel: 'internal',
  department: '',
  enableOCR: false,
  enableExtraction: true,
  makePublic: false,
  agreeTerms: false
})

const dragActive = ref(false)
const uploading = ref(false)
const fileError = ref('')

const securityLevels = [
  { value: 'public', label: 'Public', description: 'Visible to all' },
  { value: 'internal', label: 'Internal', description: 'Staff only' },
  { value: 'confidential', label: 'Confidential', description: 'Restricted access' }
]

const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const getFileType = (mimeType) => {
  if (!mimeType) return 'Unknown'
  const types = {
    'application/pdf': 'PDF',
    'text/plain': 'Text',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel',
    'text/markdown': 'Markdown'
  }
  return types[mimeType] || 'File'
}

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

  // Check file size
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    fileError.value = `File is too large. Maximum size is 50MB. Your file is ${formatFileSize(file.size)}.`
    return
  }

  // Check file type
  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/markdown'
  ]

  if (!allowedTypes.includes(file.type)) {
    fileError.value = `File type not supported. Allowed types: PDF, TXT, DOCX, XLSX, MD`
    return
  }

  form.file = file
}

const handleSubmit = async () => {
  if (!form.file || !form.agreeTerms) {
    fileError.value = 'Please select a file and agree to terms'
    return
  }

  uploading.value = true

  try {
    // Simulate upload processing
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Create FormData for multipart upload
    const formData = new FormData()
    formData.append('file', form.file)
    formData.append('purpose', form.purpose)
    formData.append('securityLevel', form.securityLevel)
    formData.append('department', form.department)
    formData.append('enableOCR', form.enableOCR)
    formData.append('enableExtraction', form.enableExtraction)
    formData.append('makePublic', form.makePublic)

    // TODO: Call your backend API here
    // const response = await fetch('/api/documents/upload', {
    //   method: 'POST',
    //   body: formData
    // })

    console.log('Upload data:', Object.fromEntries(formData))

    // Show success message and redirect
    uploading.value = false
    router.push('/knowledge-base')
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
