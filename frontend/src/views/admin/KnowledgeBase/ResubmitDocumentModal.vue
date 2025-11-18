<template>
  <transition name="modal" @enter="onEnter" @leave="onLeave">
    <div v-if="isOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 flex items-center justify-between p-6 border-b border-fortress-700 bg-fortress-800">
          <h2 class="text-xl font-semibold text-fortress-100">Resubmit Document</h2>
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
          <!-- Previous Rejection Reason -->
          <div v-if="document?.rejection_reason" class="bg-alert/10 border border-alert/30 rounded-lg p-4">
            <div class="flex items-start space-x-3">
              <svg class="w-5 h-5 text-alert flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              <div class="flex-1">
                <p class="text-sm font-medium text-alert mb-1">Previous Rejection Reason</p>
                <p class="text-sm text-fortress-300">{{ document.rejection_reason }}</p>
              </div>
            </div>
          </div>

          <!-- File Upload Area -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-3">
              Document <span class="text-fortress-500 text-xs">(choose new file or resubmit same)</span>
            </label>
            
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
                    {{ form.file?.name || document?.file_name || 'Click to upload or drag and drop' }}
                  </p>
                  <p v-if="!form.file && !document?.file_name" class="text-fortress-500 text-sm mt-1">
                    PDF, TXT, DOCX, XLSX, or MD files up to 50MB
                  </p>
                  <p v-else class="text-fortress-400 text-sm mt-1">
                    {{ formatFileSize(form.file?.size || document?.file_size || 0) }}
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
              File Purpose
            </label>
            <textarea
              v-model="form.purpose"
              :placeholder="document?.file_purpose || 'Describe what this document contains...'"
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

          <!-- Info Message -->
          <div class="bg-secure/10 border border-secure/30 rounded-lg p-4">
            <p class="text-sm text-secure">
              ✓ After resubmission, your document will go through approval again. Please address the rejection reason above.
            </p>
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
            <span v-if="!uploading">Resubmit Document</span>
            <span v-else>Resubmitting...</span>
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
  },
  document: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'submit'])

const fileInput = ref(null)
const dragActive = ref(false)
const uploading = ref(false)
const fileError = ref('')

const form = ref({
  file: null,
  purpose: props.document?.file_purpose || '',
  securityLevel: props.document?.security_level || 'internal'
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
  return (form.value.file || props.document?.file_name) && !uploading.value
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
  
  // TODO: API call to resubmit file
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  emit('submit', {
    documentId: props.document?.id,
    file: form.value.file || null,
    purpose: form.value.purpose,
    securityLevel: form.value.securityLevel
  })

  close()
}

const close = () => {
  resetForm()
  emit('close')
}

const resetForm = () => {
  form.value = {
    file: null,
    purpose: props.document?.file_purpose || '',
    securityLevel: props.document?.security_level || 'internal'
  }
  fileError.value = ''
  uploading.value = false
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
