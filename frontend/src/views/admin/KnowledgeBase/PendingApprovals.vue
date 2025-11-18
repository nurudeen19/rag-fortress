<template>
  <div class="space-y-4">
    <!-- Empty State -->
    <div v-if="!loading && documents.length === 0" class="text-center py-12 bg-fortress-800/50 rounded-lg border border-fortress-700">
      <svg class="w-12 h-12 mx-auto mb-4 text-fortress-600" fill="currentColor" viewBox="0 0 20 20">
        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
        <path fill-rule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 000 2H3a1 1 0 00-1 1v10a1 1 0 001 1h14a1 1 0 001-1V6a1 1 0 00-1-1h-3a1 1 0 000-2h2a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" clip-rule="evenodd" />
      </svg>
      <p class="text-fortress-300 mb-2">No pending documents</p>
      <p class="text-fortress-500 text-sm">All submitted documents have been reviewed</p>
    </div>

    <!-- Pending Documents -->
    <div v-else class="space-y-3">
      <!-- Search/Filter Header -->
      <div class="flex items-center space-x-2 bg-fortress-800 rounded-lg p-3 border border-fortress-700">
        <svg class="w-5 h-5 text-fortress-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by file name or uploader..."
          class="flex-1 bg-transparent text-fortress-100 placeholder-fortress-500 focus:outline-none"
        />
      </div>

      <!-- Documents List -->
      <div v-for="doc in filteredDocuments" :key="doc.id" class="bg-fortress-800 rounded-lg border border-fortress-700 overflow-hidden">
        <div class="p-4">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <!-- Document Header -->
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
                    <span>Uploaded {{ formatDate(doc.uploaded_at) }}</span>
                  </div>
                </div>
              </div>

              <!-- Document Details -->
              <div class="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p class="text-fortress-500 text-xs">Uploaded By</p>
                  <p class="text-fortress-100 font-medium">{{ doc.uploaded_by }}</p>
                </div>
                <div>
                  <p class="text-fortress-500 text-xs">Security Level</p>
                  <span
                    :class="[
                      'inline-block px-2 py-1 rounded text-xs font-medium',
                      doc.security_level === 'internal' && 'bg-fortress-700/50 text-fortress-300',
                      doc.security_level === 'confidential' && 'bg-amber-900/30 text-amber-300',
                      doc.security_level === 'restricted' && 'bg-alert/20 text-alert'
                    ]"
                  >
                    {{ formatSecurityLevel(doc.security_level) }}
                  </span>
                </div>
              </div>

              <!-- File Purpose -->
              <div v-if="doc.file_purpose" class="mt-3 p-3 bg-fortress-900/50 rounded border border-fortress-700">
                <p class="text-xs text-fortress-500 mb-1">File Purpose</p>
                <p class="text-fortress-200">{{ doc.file_purpose }}</p>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-col items-end space-y-2 ml-4">
              <button
                @click="$emit('approve', doc.id)"
                class="px-3 py-2 bg-success/20 text-success hover:bg-success/30 rounded-lg font-medium text-sm transition-colors border border-success/50"
              >
                Approve
              </button>
              <button
                @click="$emit('show-reject', doc)"
                class="px-3 py-2 bg-alert/20 text-alert hover:bg-alert/30 rounded-lg font-medium text-sm transition-colors border border-alert/50"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- No Results -->
      <div v-if="searchQuery && filteredDocuments.length === 0" class="text-center py-8 text-fortress-400">
        <p>No documents match your search</p>
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
import { ref, computed } from 'vue'

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

defineEmits(['approve', 'show-reject'])

const searchQuery = ref('')

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return props.documents
  
  const query = searchQuery.value.toLowerCase()
  return props.documents.filter(doc =>
    doc.file_name.toLowerCase().includes(query) ||
    doc.uploaded_by.toLowerCase().includes(query)
  )
})

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
}

const formatSecurityLevel = (level) => {
  const levels = {
    internal: 'Internal',
    confidential: 'Confidential',
    restricted: 'Restricted'
  }
  return levels[level] || level
}
</script>
