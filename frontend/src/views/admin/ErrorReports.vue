<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-fortress-100 mb-2">Error Reports</h1>
      <p class="text-fortress-400">Monitor and manage user-reported errors across the system</p>
    </div>

    <!-- Dashboard Metrics -->
    <div v-if="dashboardMetrics" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card p-4 bg-fortress-800">
        <p class="text-fortress-400 text-sm font-medium mb-1">Total Reports</p>
        <p class="text-2xl font-bold text-fortress-100">{{ dashboardMetrics.total }}</p>
      </div>
      <div class="card p-4 bg-blue-500/10 border-blue-500/30">
        <p class="text-blue-400 text-sm font-medium mb-1">Open</p>
        <p class="text-2xl font-bold text-blue-300">{{ dashboardMetrics.OPEN || 0 }}</p>
      </div>
      <div class="card p-4 bg-yellow-500/10 border-yellow-500/30">
        <p class="text-yellow-400 text-sm font-medium mb-1">Investigating</p>
        <p class="text-2xl font-bold text-yellow-300">{{ dashboardMetrics.INVESTIGATING || 0 }}</p>
      </div>
      <div class="card p-4 bg-green-500/10 border-green-500/30">
        <p class="text-green-400 text-sm font-medium mb-1">Resolved</p>
        <p class="text-2xl font-bold text-green-300">{{ dashboardMetrics.RESOLVED || 0 }}</p>
      </div>
    </div>

    <!-- Filters & Controls -->
    <div class="card p-4 mb-6 bg-fortress-800/50">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Status Filter -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">Filter by Status</label>
          <select 
            v-model="filters.status"
            @change="loadReports"
            class="w-full px-3 py-2 bg-fortress-900 border border-fortress-700 rounded-lg text-fortress-100 text-sm focus:border-secure focus:outline-none transition-colors"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
            <option value="DUPLICATE">Duplicate</option>
            <option value="NOT_REPRODUCIBLE">Not Reproducible</option>
            <option value="WONT_FIX">Won't Fix</option>
          </select>
        </div>

        <!-- Category Filter -->
        <div>
          <label class="block text-sm font-medium text-fortress-300 mb-2">Filter by Category</label>
          <select 
            v-model="filters.category"
            @change="loadReports"
            class="w-full px-3 py-2 bg-fortress-900 border border-fortress-700 rounded-lg text-fortress-100 text-sm focus:border-secure focus:outline-none transition-colors"
          >
            <option value="">All Categories</option>
            <option value="LLM_ERROR">LLM Error</option>
            <option value="RETRIEVAL_ERROR">Retrieval Error</option>
            <option value="VALIDATION_ERROR">Validation Error</option>
            <option value="PERFORMANCE">Performance</option>
            <option value="UI_UX">UI/UX</option>
            <option value="PERMISSIONS">Permissions</option>
            <option value="DATA_ACCURACY">Data Accuracy</option>
            <option value="SYSTEM_ERROR">System Error</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        <!-- Refresh Button -->
        <div class="flex items-end">
          <button
            @click="loadReports"
            :disabled="loading"
            class="w-full px-4 py-2 bg-secure hover:bg-secure/90 disabled:bg-fortress-700 text-white rounded-lg font-medium text-sm transition-colors flex items-center justify-center gap-2"
          >
            <svg v-if="loading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ loading ? 'Loading...' : 'Refresh' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card p-12 text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-secure mx-auto mb-4"></div>
      <p class="text-fortress-400">Loading error reports...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="reports.length === 0" class="card p-12 text-center">
      <svg class="w-16 h-16 text-fortress-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-fortress-300 font-medium mb-1">No Error Reports</p>
      <p class="text-fortress-500 text-sm">No error reports match the current filters</p>
    </div>

    <!-- Reports Table -->
    <div v-else class="card overflow-hidden flex-1 flex flex-col">
      <div class="overflow-x-auto flex-1">
        <table class="w-full">
          <thead class="bg-fortress-800 border-b border-fortress-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-fortress-400 uppercase tracking-wider">
                Title & User
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-fortress-400 uppercase tracking-wider">
                Category
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-fortress-400 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-fortress-400 uppercase tracking-wider">
                Created
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-fortress-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-fortress-700">
            <tr
              v-for="report in reports"
              :key="report.id"
              class="hover:bg-fortress-800/50 transition-colors"
            >
              <!-- Title & User -->
              <td class="px-6 py-4">
                <div>
                  <p class="text-fortress-100 font-medium">{{ report.title }}</p>
                  <p class="text-fortress-500 text-sm">{{ report.user_name || 'Unknown' }}</p>
                </div>
              </td>

              <!-- Category -->
              <td class="px-6 py-4">
                <span :class="getCategoryBadgeClass(report.category)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  {{ getCategoryLabel(report.category) }}
                </span>
              </td>

              <!-- Status -->
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <select
                    :value="report.status"
                    @change="updateReportStatus(report.id, $event.target.value)"
                    :class="getStatusBadgeClass(report.status)"
                    class="px-2 py-1 rounded text-xs font-medium border-0 focus:outline-none focus:ring-2 focus:ring-secure cursor-pointer transition-colors"
                  >
                    <option value="OPEN">Open</option>
                    <option value="INVESTIGATING">Investigating</option>
                    <option value="ACKNOWLEDGED">Acknowledged</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="DUPLICATE">Duplicate</option>
                    <option value="NOT_REPRODUCIBLE">Not Reproducible</option>
                    <option value="WONT_FIX">Won't Fix</option>
                  </select>
                </div>
              </td>

              <!-- Created Date -->
              <td class="px-6 py-4 text-fortress-400 text-sm">
                {{ formatDate(report.created_at) }}
              </td>

              <!-- Actions -->
              <td class="px-6 py-4">
                <button
                  @click="selectedReport = report; showDetailModal = true"
                  class="text-secure hover:text-secure-light text-sm font-medium transition-colors"
                >
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalReports > pagination.limit" class="border-t border-fortress-700 px-6 py-4 flex items-center justify-between bg-fortress-800/50">
        <p class="text-sm text-fortress-400">
          Showing {{ pagination.offset + 1 }} - {{ Math.min(pagination.offset + pagination.limit, totalReports) }} of {{ totalReports }}
        </p>
        <div class="flex gap-2">
          <button
            @click="previousPage"
            :disabled="pagination.offset === 0"
            class="px-3 py-1 bg-fortress-700 hover:bg-fortress-600 disabled:bg-fortress-800 text-fortress-300 disabled:text-fortress-500 rounded text-sm transition-colors"
          >
            Previous
          </button>
          <button
            @click="nextPage"
            :disabled="pagination.offset + pagination.limit >= totalReports"
            class="px-3 py-1 bg-fortress-700 hover:bg-fortress-600 disabled:bg-fortress-800 text-fortress-300 disabled:text-fortress-500 rounded text-sm transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetailModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-fortress-900 rounded-lg border border-fortress-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-fortress-800 border-b border-fortress-700 px-6 py-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-fortress-100">Error Report Details</h2>
          <button
            @click="showDetailModal = false"
            class="text-fortress-400 hover:text-fortress-200 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Modal Content -->
        <div class="p-6 space-y-6">
          <!-- Report Info -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-fortress-400 text-sm font-medium mb-1">Title</p>
              <p class="text-fortress-100">{{ selectedReport.title }}</p>
            </div>
            <div>
              <p class="text-fortress-400 text-sm font-medium mb-1">User</p>
              <p class="text-fortress-100">{{ selectedReport.user_name || 'Unknown' }}</p>
            </div>
            <div>
              <p class="text-fortress-400 text-sm font-medium mb-1">Category</p>
              <span :class="getCategoryBadgeClass(selectedReport.category)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                {{ getCategoryLabel(selectedReport.category) }}
              </span>
            </div>
            <div>
              <p class="text-fortress-400 text-sm font-medium mb-1">Status</p>
              <span :class="getStatusBadgeClass(selectedReport.status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                {{ selectedReport.status }}
              </span>
            </div>
          </div>

          <!-- Description -->
          <div>
            <p class="text-fortress-400 text-sm font-medium mb-2">Description</p>
            <p class="text-fortress-200 whitespace-pre-wrap">{{ selectedReport.description }}</p>
          </div>

          <!-- Admin Notes -->
          <div>
            <p class="text-fortress-400 text-sm font-medium mb-2">Admin Notes</p>
            <textarea
              v-model="adminNotes"
              placeholder="Add notes about this error report..."
              class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 text-sm focus:border-secure focus:outline-none transition-colors"
              rows="4"
            ></textarea>
          </div>

          <!-- Image (if available) -->
          <div v-if="selectedReport.image_url" class="border-t border-fortress-700 pt-6">
            <p class="text-fortress-400 text-sm font-medium mb-3">Attached Image</p>
            <img 
              :src="selectedReport.image_url" 
              :alt="selectedReport.title"
              class="max-w-full max-h-96 rounded-lg border border-fortress-700"
            />
          </div>

          <!-- Metadata -->
          <div class="border-t border-fortress-700 pt-6 grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-fortress-500 mb-1">Created</p>
              <p class="text-fortress-200">{{ formatDateTime(selectedReport.created_at) }}</p>
            </div>
            <div>
              <p class="text-fortress-500 mb-1">Last Updated</p>
              <p class="text-fortress-200">{{ formatDateTime(selectedReport.updated_at) }}</p>
            </div>
            <div v-if="selectedReport.resolved_at">
              <p class="text-fortress-500 mb-1">Resolved</p>
              <p class="text-fortress-200">{{ formatDateTime(selectedReport.resolved_at) }}</p>
            </div>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-fortress-800 border-t border-fortress-700 px-6 py-4 flex gap-3 justify-end">
          <button
            @click="showDetailModal = false"
            class="px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg font-medium transition-colors"
          >
            Close
          </button>
          <button
            @click="saveAdminNotes"
            :disabled="updatingNote"
            class="px-4 py-2 bg-secure hover:bg-secure/90 disabled:bg-fortress-700 text-white rounded-lg font-medium transition-colors"
          >
            {{ updatingNote ? 'Saving...' : 'Save Notes' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="mt-4 p-4 bg-error/20 border border-error/50 rounded-lg text-error">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { adminErrorReporting, CATEGORY_DISPLAY } from '@/services/errorReporting'

// State
const loading = ref(false)
const updatingNote = ref(false)
const error = ref(null)
const reports = ref([])
const selectedReport = ref(null)
const showDetailModal = ref(false)
const adminNotes = ref('')
const totalReports = ref(0)
const dashboardMetrics = ref(null)

const filters = ref({
  status: '',
  category: ''
})

const pagination = ref({
  limit: 20,
  offset: 0
})

// Methods
const loadReports = async () => {
  loading.value = true
  error.value = null
  pagination.value.offset = 0
  
  try {
    const response = await adminErrorReporting.getReports({
      status: filters.value.status || null,
      category: filters.value.category || null,
      limit: pagination.value.limit,
      offset: pagination.value.offset
    })
    
    reports.value = response.items || []
    totalReports.value = response.total || 0
    dashboardMetrics.value = {
      total: response.total,
      ...response.status_counts
    }
  } catch (err) {
    error.value = 'Failed to load error reports'
    console.error('Error loading reports:', err)
  } finally {
    loading.value = false
  }
}

const updateReportStatus = async (reportId, newStatus) => {
  try {
    await adminErrorReporting.updateReport(reportId, {
      status: newStatus,
      admin_notes: null,
      assigned_to: null
    })
    
    // Reload reports
    await loadReports()
  } catch (err) {
    error.value = 'Failed to update report status'
    console.error('Error updating status:', err)
  }
}

const saveAdminNotes = async () => {
  if (!selectedReport.value) return
  
  updatingNote.value = true
  error.value = null
  
  try {
    const response = await adminErrorReporting.updateReport(selectedReport.value.id, {
      status: selectedReport.value.status,
      admin_notes: adminNotes.value,
      assigned_to: null
    })
    
    selectedReport.value = response
    await loadReports()
    showDetailModal.value = false
  } catch (err) {
    error.value = 'Failed to save notes'
    console.error('Error saving notes:', err)
  } finally {
    updatingNote.value = false
  }
}

const nextPage = async () => {
  pagination.value.offset += pagination.value.limit
  await loadReports()
}

const previousPage = async () => {
  pagination.value.offset = Math.max(0, pagination.value.offset - pagination.value.limit)
  await loadReports()
}

const getCategoryLabel = (category) => {
  return CATEGORY_DISPLAY[category]?.label || category
}

const getCategoryBadgeClass = (category) => {
  const display = CATEGORY_DISPLAY[category]
  const colorMap = {
    red: 'bg-red-500/20 text-red-300 border border-red-500/30',
    orange: 'bg-orange-500/20 text-orange-300 border border-orange-500/30',
    yellow: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
    blue: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
    purple: 'bg-purple-500/20 text-purple-300 border border-purple-500/30',
    gray: 'bg-fortress-700 text-fortress-300 border border-fortress-600'
  }
  return colorMap[display?.color] || 'bg-gray-500/20 text-gray-300 border border-gray-500/30'
}

const getStatusBadgeClass = (status) => {
  const statusColorMap = {
    OPEN: 'bg-blue-500/20 text-blue-300',
    INVESTIGATING: 'bg-yellow-500/20 text-yellow-300',
    ACKNOWLEDGED: 'bg-purple-500/20 text-purple-300',
    RESOLVED: 'bg-green-500/20 text-green-300',
    DUPLICATE: 'bg-gray-500/20 text-gray-300',
    NOT_REPRODUCIBLE: 'bg-gray-500/20 text-gray-300',
    WONT_FIX: 'bg-gray-500/20 text-gray-300'
  }
  return statusColorMap[status] || 'bg-gray-500/20 text-gray-300'
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatDateTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Watch modal open/close
const handleModalOpen = () => {
  if (selectedReport.value) {
    adminNotes.value = selectedReport.value.admin_notes || ''
  }
}

watch(() => showDetailModal.value, (newVal) => {
  if (newVal) handleModalOpen()
})

// Lifecycle
onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.card {
  @apply bg-fortress-900 rounded-lg border border-fortress-700;
}
</style>
