<template>
  <div class="space-y-4">
    <!-- Empty State -->
    <div v-if="!loading && documents.length === 0" class="text-center py-12 bg-fortress-800/50 rounded-lg border border-fortress-700">
      <svg class="w-12 h-12 mx-auto mb-4 text-fortress-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="text-fortress-300 mb-2">No documents submitted yet</p>
      <p class="text-fortress-500 text-sm mb-4">Start by uploading a document to the knowledge base</p>
      <button
        @click="$emit('upload')"
        class="bg-secure hover:bg-secure/90 px-4 py-2 rounded-lg text-white font-medium transition-colors"
      >
        Upload Document
      </button>
    </div>

    <!-- Documents List -->
    <div v-else class="space-y-3">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="bg-fortress-800 rounded-lg border border-fortress-700 overflow-hidden hover:border-fortress-600 transition-colors"
      >
        <div class="p-4">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <!-- Document Info -->
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  <svg class="w-8 h-8 text-fortress-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="text-fortress-100 font-medium truncate">{{ doc.file_name }}</h3>
                  <div class="flex items-center space-x-2 mt-1 text-xs text-fortress-400">
                    <span>{{ formatFileSize(doc.file_size) }}</span>
                    <span>•</span>
                    <span>{{ formatDate(doc.uploaded_at) }}</span>
                  </div>
                </div>
              </div>

              <!-- Status Badge -->
              <div class="mt-3 flex items-center space-x-2">
                <span
                  :class="[
                    'px-2 py-1 text-xs font-medium rounded-full',
                    doc.status === 'pending' && 'bg-amber-900/30 text-amber-300 border border-amber-700/50',
                    doc.status === 'approved' && 'bg-secure/20 text-secure border border-secure/50',
                    doc.status === 'processed' && 'bg-success/20 text-success border border-success/50',
                    doc.status === 'rejected' && 'bg-alert/20 text-alert border border-alert/50',
                    doc.status === 'failed' && 'bg-alert/20 text-alert border border-alert/50'
                  ]"
                >
                  {{ formatStatus(doc.status) }}
                </span>

                <span v-if="doc.chunks_created" class="text-xs text-fortress-500">
                  {{ doc.chunks_created }} chunks
                </span>
              </div>

              <!-- Additional Info -->
              <div v-if="doc.file_purpose" class="mt-2 text-sm text-fortress-400">
                <p class="italic">{{ doc.file_purpose }}</p>
              </div>

              <!-- Approval Info -->
              <div v-if="doc.approval_reason" class="mt-2 p-2 bg-fortress-900/50 rounded border-l-2 border-success">
                <p class="text-xs text-fortress-400">
                  <span class="font-medium">Approved:</span> {{ doc.approval_reason }}
                </p>
              </div>

              <!-- Rejection Info -->
              <div v-if="doc.rejection_reason" class="mt-2 p-2 bg-fortress-900/50 rounded border-l-2 border-alert">
                <p class="text-xs text-fortress-400">
                  <span class="font-medium">Rejection reason:</span> {{ doc.rejection_reason }}
                </p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center space-x-2 ml-4">
              <button
                v-if="doc.status === 'rejected'"
                @click="$emit('resubmit', doc)"
                class="p-2 rounded text-fortress-400 hover:text-fortress-100 hover:bg-fortress-700 transition-colors"
                title="Resubmit"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>

              <button
                v-if="doc.status === 'pending' || doc.status === 'rejected'"
                @click="$emit('delete', doc.id)"
                class="p-2 rounded text-fortress-400 hover:text-alert hover:bg-alert/10 transition-colors"
                title="Delete"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block">
        <svg class="w-8 h-8 text-secure animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  documents: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['upload', 'delete', 'resubmit'])

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const formatStatus = (status) => {
  const statuses = {
    pending: 'Pending Approval',
    approved: 'Approved',
    processing: 'Processing',
    processed: 'Processed',
    rejected: 'Rejected',
    failed: 'Failed'
  }
  return statuses[status] || status
}
</script>
