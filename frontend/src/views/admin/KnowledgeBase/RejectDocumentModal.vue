<template>
  <transition name="modal" @enter="onEnter" @leave="onLeave">
    <div v-if="isOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-md shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-fortress-700">
          <h2 class="text-xl font-semibold text-fortress-100">Reject Document</h2>
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
        <div class="p-6 space-y-4">
          <!-- Document Info -->
          <div v-if="document" class="bg-fortress-900/50 rounded-lg border border-fortress-700 p-4">
            <div class="flex items-start space-x-3">
              <svg class="w-8 h-8 text-fortress-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
              </svg>
              <div class="flex-1 min-w-0">
                <p class="text-fortress-300 font-medium truncate">{{ document.file_name }}</p>
                <p class="text-fortress-500 text-sm mt-1">
                  Submitted by {{ document.uploaded_by_name || `User #${document.uploaded_by_id}` }}
                </p>
              </div>
            </div>
          </div>

          <!-- Rejection Reason -->
          <div>
            <label class="block text-sm font-medium text-fortress-300 mb-3">
              Rejection Reason <span class="text-alert">*</span>
            </label>
            <textarea
              v-model="form.reason"
              placeholder="Please provide a clear reason for rejection so the uploader can resubmit correctly..."
              class="w-full bg-fortress-700 border border-fortress-600 rounded-lg px-4 py-3 text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-alert resize-none"
              rows="4"
            />
            <div class="flex items-center justify-between mt-1">
              <p class="text-xs text-fortress-500">
                Be constructive to help users improve their submissions
              </p>
              <p class="text-xs text-fortress-400">
                {{ form.reason.length }}/500
              </p>
            </div>
          </div>

          <!-- Common Reasons -->
          <div>
            <p class="text-xs text-fortress-500 mb-2">Quick reasons:</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="reason in commonReasons"
                :key="reason"
                @click="form.reason = reason"
                class="text-xs px-3 py-1 bg-fortress-700 hover:bg-fortress-600 text-fortress-300 rounded-lg transition-colors border border-fortress-600"
              >
                {{ reason }}
              </button>
            </div>
          </div>

          <!-- Notify Uploader -->
          <div class="flex items-center space-x-3">
            <input
              v-model="form.notifyUploader"
              type="checkbox"
              class="w-4 h-4 rounded border-fortress-600 text-secure focus:ring-secure cursor-pointer"
            />
            <label class="text-sm text-fortress-300 cursor-pointer">
              Send notification to uploader
            </label>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end space-x-3 p-6 border-t border-fortress-700 bg-fortress-900/50">
          <button
            @click="close"
            class="px-6 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            @click="submit"
            :disabled="!form.reason.trim() || rejecting"
            :class="[
              'px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2',
              form.reason.trim() && !rejecting
                ? 'bg-alert hover:bg-alert/90 text-white'
                : 'bg-fortress-700 text-fortress-500 cursor-not-allowed'
            ]"
          >
            <span v-if="!rejecting">Reject Document</span>
            <span v-else>Rejecting...</span>
            <svg v-if="rejecting" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
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

const rejecting = ref(false)

const form = ref({
  reason: '',
  notifyUploader: true
})

const commonReasons = [
  'File contains sensitive information',
  'File format not supported',
  'Poor document quality',
  'Content not relevant',
  'Duplicate submission'
]

const submit = async () => {
  if (!form.value.reason.trim()) return

  rejecting.value = true
  
  // TODO: API call to reject document
  await new Promise(resolve => setTimeout(resolve, 800))
  
  emit('submit', {
    documentId: document.value?.id,
    reason: form.value.reason,
    notifyUploader: form.value.notifyUploader
  })

  close()
}

const close = () => {
  resetForm()
  emit('close')
}

const resetForm = () => {
  form.value = {
    reason: '',
    notifyUploader: true
  }
  rejecting.value = false
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
