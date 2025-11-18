<template>
  <div class="space-y-4">
    <!-- Header with Stats -->
    <div class="grid grid-cols-3 gap-3">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-4">
        <div class="flex items-center space-x-3">
          <div class="p-3 bg-secure/20 rounded-lg">
            <svg class="w-6 h-6 text-secure" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fill-rule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 000 2H3a1 1 0 00-1 1v10a1 1 0 001 1h14a1 1 0 001-1V6a1 1 0 00-1-1h-3a1 1 0 000-2h2a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" clip-rule="evenodd" />
            </svg>
          </div>
          <div>
            <p class="text-fortress-500 text-sm">Total Documents</p>
            <p class="text-2xl font-bold text-fortress-100">{{ documents.length }}</p>
          </div>
        </div>
      </div>

      <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-4">
        <div class="flex items-center space-x-3">
          <div class="p-3 bg-success/20 rounded-lg">
            <svg class="w-6 h-6 text-success" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a1 1 0 001 1h14a1 1 0 001-1V6a2 2 0 00-2-2H4zm0 6v4a2 2 0 002 2h12a2 2 0 002-2v-4H4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div>
            <p class="text-fortress-500 text-sm">Total Chunks</p>
            <p class="text-2xl font-bold text-fortress-100">{{ totalChunks }}</p>
          </div>
        </div>
      </div>

      <div class="bg-fortress-800 rounded-lg border border-fortress-700 p-4">
        <div class="flex items-center space-x-3">
          <div class="p-3 bg-fortress-700/50 rounded-lg">
            <svg class="w-6 h-6 text-fortress-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4.5 3a2.5 2.5 0 015 0h5a2.5 2.5 0 015 0v2a1 1 0 01-.125 4.002.999.999 0 00-.875.998v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5a.999.999 0 00-.875-.998A1 1 0 014.5 5V3z" />
            </svg>
          </div>
          <div>
            <p class="text-fortress-500 text-sm">Total Storage</p>
            <p class="text-2xl font-bold text-fortress-100">{{ formatTotalStorage() }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Search/Filter -->
    <div class="flex items-center space-x-2 bg-fortress-800 rounded-lg p-3 border border-fortress-700">
      <svg class="w-5 h-5 text-fortress-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search documents by name or description..."
        class="flex-1 bg-transparent text-fortress-100 placeholder-fortress-500 focus:outline-none"
      />
    </div>

    <!-- Empty State -->
    <div v-if="!loading && documents.length === 0" class="text-center py-12 bg-fortress-800/50 rounded-lg border border-fortress-700">
      <svg class="w-12 h-12 mx-auto mb-4 text-fortress-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="text-fortress-300 mb-2">Knowledge base is empty</p>
      <p class="text-fortress-500 text-sm">Approved documents will appear here</p>
    </div>

    <!-- Documents Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="doc in filteredDocuments"
        :key="doc.id"
        class="bg-fortress-800 rounded-lg border border-fortress-700 overflow-hidden hover:border-fortress-600 transition-colors cursor-pointer group"
      >
        <div class="p-4">
          <!-- Document Icon and Title -->
          <div class="flex items-start space-x-3 mb-3">
            <div class="flex-shrink-0">
              <svg class="w-8 h-8 text-fortress-500 group-hover:text-secure transition-colors" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 012-2h6a1 1 0 01.707.293l6 6a1 1 0 01.293.707v7a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-fortress-100 font-semibold truncate group-hover:text-secure transition-colors">
                {{ doc.file_name }}
              </h3>
              <p class="text-xs text-fortress-500 mt-1">{{ formatFileSize(doc.file_size) }}</p>
            </div>
          </div>

          <!-- Document Stats -->
          <div class="grid grid-cols-2 gap-3 mb-3 text-sm">
            <div>
              <p class="text-fortress-500 text-xs">Chunks</p>
              <p class="text-fortress-100 font-medium">{{ doc.chunks_created }}</p>
            </div>
            <div>
              <p class="text-fortress-500 text-xs">Processed</p>
              <p class="text-fortress-100 font-medium">{{ formatDate(doc.uploaded_at) }}</p>
            </div>
          </div>

          <!-- Uploaded By -->
          <div class="py-2 px-2 bg-fortress-900/50 rounded text-xs">
            <p class="text-fortress-500">By <span class="text-fortress-300 font-medium">{{ doc.uploaded_by }}</span></p>
          </div>

          <!-- Approval Note -->
          <div v-if="doc.approval_reason" class="mt-3 p-2 bg-success/10 rounded border border-success/30">
            <p class="text-xs text-success">{{ doc.approval_reason }}</p>
          </div>
        </div>

        <!-- Hover Preview -->
        <div class="bg-fortress-900/50 border-t border-fortress-700 px-4 py-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <p class="text-xs text-fortress-400">
            <span class="font-medium">Security:</span> {{ formatSecurityLevel(doc.security_level) }}
          </p>
        </div>
      </div>
    </div>

    <!-- No Results -->
    <div v-if="searchQuery && filteredDocuments.length === 0" class="text-center py-8 text-fortress-400">
      <p>No documents match your search</p>
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

const searchQuery = ref('')

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return props.documents
  
  const query = searchQuery.value.toLowerCase()
  return props.documents.filter(doc =>
    doc.file_name.toLowerCase().includes(query) ||
    (doc.approval_reason && doc.approval_reason.toLowerCase().includes(query))
  )
})

const totalChunks = computed(() => {
  return props.documents.reduce((sum, doc) => sum + (doc.chunks_created || 0), 0)
})

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatTotalStorage = () => {
  const total = props.documents.reduce((sum, doc) => sum + (doc.file_size || 0), 0)
  return formatFileSize(total)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
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
