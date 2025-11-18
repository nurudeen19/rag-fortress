<template>
  <transition name="modal" @enter="onEnter" @leave="onLeave">
    <div v-if="isOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 flex items-center justify-between p-6 border-b border-fortress-700 bg-fortress-800">
          <h2 class="text-xl font-semibold text-fortress-100">Upload Document</h2>
          <button
            @click="close"
            class="p-1 hover:bg-fortress-700 rounded-lg transition-colors"
          >
            <svg class="w-6 h-6 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Content -->
        <div class="p-6 space-y-6">
          <!-- File Upload Area -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-3">
              Choose Document
            </label>
            
            <!-- Drag and Drop Area -->
            <div
              @drop.prevent="handleDrop"
              @dragover.prevent="dragActive = true"
              @dragleave.prevent="dragActive = false"
              :class="[
                'relative border-2 border-dashed rounded-lg p-8 transition-colors cursor-pointer',
                dragActive
                  ? 'border-secure bg-secure/10'
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
                  class="mx-auto h-12 w-12 text-fortress-500 mb-2"
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
                  class="mx-auto h-12 w-12 text-success mb-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                </svg>

                <div class="mt-2">
                  <p class="text-fortress-100 font-medium">
                    {{ form.file?.name || 'Click to upload or drag and drop' }}
                  </p>
                  <p v-if="!form.file" class="text-fortress-500 text-sm mt-1">
                    PDF, TXT, DOCX, XLSX, or MD files up to 50MB
                  </p>
                  <p v-else class="text-fortress-400 text-sm mt-1">
                    {{ formatFileSize(form.file.size) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- File Error -->
            <div v-if="fileError" class="mt-2 p-3 bg-alert/20 border border-alert/50 rounded-lg">
              <p class="text-alert text-sm">{{ fileError }}</p>
            </div>
          </div>

          <!-- File Purpose -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">
              File Purpose <span class="text-fortress-500 text-xs">(optional)</span>
            </label>
            <textarea
              v-model="form.purpose"
              placeholder="Describe what this document contains and how it should be used..."
              class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-4 py-3 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure resize-none"
              rows="3"
            />
            <p class="text-xs text-fortress-500 mt-1">
              {{ form.purpose.length }}/500 characters
            </p>
          </div>

          <!-- Security Level -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">
              Security Level
            </label>
            <div class="grid grid-cols-3 gap-3">
              <button
                v-for="level in securityLevels"
                :key="level.value"
                @click="form.securityLevel = level.value"
                :class="[
                  'p-3 rounded-lg border-2 transition-colors text-center',
                  form.securityLevel === level.value
                    ? 'border-secure bg-secure/20'
                    : 'border-fortress-700 bg-fortress-900/50 hover:border-fortress-600'
                ]"
              >
                <p class="font-medium text-sm text-fortress-100">{{ level.label }}</p>
                <p class="text-xs text-fortress-500 mt-1">{{ level.description }}</p>
              </button>
            </div>
          </div>

          <!-- Department (Optional) -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-2">
              Department <span class="text-fortress-500 text-xs">(optional)</span>
            </label>
            <select
              v-model="form.department"
              class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-4 py-2 text-fortress-100 focus:outline-none focus:border-secure"
            >
              <option value="">Select a department...</option>
              <option value="general">General</option>
              <option value="engineering">Engineering</option>
              <option value="product">Product</option>
              <option value="operations">Operations</option>
              <option value="finance">Finance</option>
            </select>
          </div>

          <!-- Terms -->
          <div class="flex items-start space-x-3">
            <input
              v-model="form.agreeTerms"
              type="checkbox"
              class="w-4 h-4 rounded border-fortress-600 text-secure focus:ring-secure cursor-pointer mt-1"
            />
            <label class="text-sm text-fortress-400 cursor-pointer">
              I confirm that this document is appropriate for upload and complies with security policies
            </label>
          </div>
        </div>

        <!-- Footer -->
        <div class="sticky bottom-0 flex items-center justify-end space-x-3 p-6 border-t border-fortress-700 bg-fortress-800">
          <button
            @click="close"
            class="px-6 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            @click="submit"
            :disabled="!canSubmit"
            :class="[
              'px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2',
              canSubmit
                ? 'bg-secure hover:bg-secure/90 text-white'
                : 'bg-fortress-700 text-fortress-500 cursor-not-allowed'
            ]"
          >
            <span v-if="!uploading">Upload Document</span>
            <span v-else>Uploading...</span>
            <svg v-if="uploading" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'submit'])

const fileInput = ref(null)
const dragActive = ref(false)
const uploading = ref(false)
const fileError = ref('')

const form = ref({
  file: null,
  purpose: '',
  securityLevel: 'internal',
  department: '',
  agreeTerms: false
})

const securityLevels = [
  {
    value: 'internal',
    label: 'Internal',
    description: 'Team accessible'
  },
  {
    value: 'confidential',
    label: 'Confidential',
    description: 'Limited access'
  },
  {
    value: 'restricted',
    label: 'Restricted',
    description: 'Admin only'
  }
]

const canSubmit = computed(() => {
  return form.value.file && form.value.agreeTerms && !uploading.value
})

const handleFileSelect = (event) => {
  const files = event.target.files
  if (files?.length) {
    validateAndSetFile(files[0])
  }
}

const handleDrop = (event) => {
  dragActive.value = false
  const files = event.dataTransfer.files
  if (files?.length) {
    validateAndSetFile(files[0])
  }
}

const validateAndSetFile = (file) => {
  fileError.value = ''
  
  // Check file size (50MB max)
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    fileError.value = `File is too large. Maximum size is 50MB (your file: ${formatFileSize(file.size)})`
    form.value.file = null
    return
  }

  // Check file type
  const allowedTypes = ['.pdf', '.txt', '.docx', '.xlsx', '.md']
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowedTypes.includes(fileExtension)) {
    fileError.value = `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`
    form.value.file = null
    return
  }

  form.value.file = file
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const submit = async () => {
  if (!canSubmit.value) return

  uploading.value = true
  
  // TODO: API call to upload file
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  emit('submit', {
    file: form.value.file,
    purpose: form.value.purpose,
    securityLevel: form.value.securityLevel,
    department: form.value.department
  })

  resetForm()
  uploading.value = false
  emit('close')
}

const close = () => {
  resetForm()
  emit('close')
}

const resetForm = () => {
  form.value = {
    file: null,
    purpose: '',
    securityLevel: 'internal',
    department: '',
    agreeTerms: false
  }
  fileError.value = ''
}

const onEnter = (el) => {
  el.style.opacity = '0'
  setTimeout(() => {
    el.style.transition = 'opacity 0.2s ease'
    el.style.opacity = '1'
  }, 10)
}

const onLeave = (el) => {
  el.style.transition = 'opacity 0.2s ease'
  el.style.opacity = '0'
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
