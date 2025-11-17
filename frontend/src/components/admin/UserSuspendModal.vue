<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
      <!-- Header -->
      <div class="p-6 border-b border-fortress-700">
        <h2 class="text-xl font-bold text-fortress-100">Suspend User</h2>
        <p class="text-sm text-fortress-400 mt-1">{{ user.full_name }} ({{ user.email }})</p>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">
            Suspension Reason (Optional)
          </label>
          <textarea
            v-model="reason"
            placeholder="e.g., Policy violation, pending review..."
            class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
            rows="4"
          />
        </div>

        <div class="bg-alert/10 border border-alert/30 rounded-lg p-3">
          <p class="text-sm text-alert">
            <strong>Warning:</strong> This user will be unable to access their account. They can be unsuspended later.
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-fortress-700 flex justify-end gap-2">
        <button
          @click="$emit('close')"
          :disabled="loading"
          class="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          @click="handleSuspend"
          :disabled="loading"
          class="btn bg-alert/20 text-alert hover:bg-alert/30 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Suspending...' : 'Suspend User' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['confirm', 'close'])

const reason = ref('')
const loading = ref(false)

async function handleSuspend() {
  loading.value = true
  try {
    emit('confirm', reason.value)
  } finally {
    loading.value = false
  }
}
</script>
