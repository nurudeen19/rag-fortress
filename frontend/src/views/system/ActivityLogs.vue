<template>
  <div>
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-fortress-100 mb-2">Activity Logs</h1>
      <p class="text-fortress-400">Monitor your security events and access patterns</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <svg class="w-8 h-8 text-secure animate-spin mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p class="text-fortress-400">Loading activity logs...</p>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="space-y-8">
      <!-- Key Metrics Grid -->
      <div>
        <h2 class="text-lg font-semibold text-fortress-100 mb-4">Activity Summary</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Total Logs -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Total Events</p>
                  <p class="text-2xl font-bold text-fortress-100">{{ totalLogs.toLocaleString() }}</p>
                  <p class="text-xs text-fortress-400 mt-1">Last {{ filters.days }} days</p>
                </div>
                <div class="w-10 h-10 bg-secure/10 border border-secure/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Critical Incidents -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Critical Events</p>
                  <p class="text-2xl font-bold text-danger">{{ criticalCount }}</p>
                  <p class="text-xs text-fortress-400 mt-1">High severity</p>
                </div>
                <div class="w-10 h-10 bg-danger/10 border border-danger/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Warnings -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Warnings</p>
                  <p class="text-2xl font-bold text-warning">{{ warningCount }}</p>
                  <p class="text-xs text-fortress-400 mt-1">Medium severity</p>
                </div>
                <div class="w-10 h-10 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4v2m0 0v2M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Info Events -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Info Events</p>
                  <p class="text-2xl font-bold text-info">{{ infoCount }}</p>
                  <p class="text-xs text-fortress-400 mt-1">Low severity</p>
                </div>
                <div class="w-10 h-10 bg-info/10 border border-info/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="card">
        <div class="card-body">
          <h3 class="text-lg font-semibold text-fortress-100 mb-4">Filter Logs</h3>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <!-- Incident Type Filter -->
            <div>
              <label class="block text-sm text-fortress-400 mb-2">Incident Type</label>
              <select 
                v-model="filters.incidentType" 
                @change="loadLogs"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:outline-none focus:border-secure transition-colors"
              >
                <option :value="null">All Types</option>
                <option v-for="type in incidentTypes" :key="type.value" :value="type.value">
                  {{ type.name }}
                </option>
              </select>
            </div>

            <!-- Severity Filter -->
            <div>
              <label class="block text-sm text-fortress-400 mb-2">Severity</label>
              <select 
                v-model="filters.severity" 
                @change="loadLogs"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:outline-none focus:border-secure transition-colors"
              >
                <option :value="null">All Levels</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <!-- Days Filter -->
            <div>
              <label class="block text-sm text-fortress-400 mb-2">Time Period</label>
              <select 
                v-model="filters.days" 
                @change="loadLogs"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:outline-none focus:border-secure transition-colors"
              >
                <option :value="7">Last 7 days</option>
                <option :value="30">Last 30 days</option>
                <option :value="90">Last 90 days</option>
                <option :value="365">Last year</option>
              </select>
            </div>

            <!-- Limit Filter -->
            <div>
              <label class="block text-sm text-fortress-400 mb-2">Results Per Page</label>
              <select 
                v-model="filters.limit" 
                @change="loadLogs"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:outline-none focus:border-secure transition-colors"
              >
                <option :value="25">25</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
                <option :value="250">250</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Activity Logs Table -->
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-fortress-100">Recent Activity</h3>
            <button 
              @click="loadLogs" 
              class="px-3 py-1.5 text-sm bg-secure/10 border border-secure/30 text-secure rounded-lg hover:bg-secure/20 transition-colors"
            >
              Refresh
            </button>
          </div>

          <!-- Logs List -->
          <div v-if="activityLogs.length > 0" class="space-y-3">
            <div
              v-for="log in activityLogs"
              :key="log.id"
              class="p-4 bg-fortress-800 border border-fortress-700 rounded-lg hover:border-secure/30 transition-colors"
            >
              <!-- Log Header -->
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span :class="[
                    'px-2 py-0.5 text-xs font-semibold rounded',
                    log.severity === 'critical' ? 'bg-danger/10 text-danger border border-danger/30' :
                    log.severity === 'warning' ? 'bg-warning/10 text-warning border border-warning/30' :
                    'bg-info/10 text-info border border-info/30'
                  ]">
                    {{ log.severity.toUpperCase() }}
                  </span>
                  <span class="text-sm font-medium text-fortress-100">
                    {{ formatIncidentType(log.incident_type) }}
                  </span>
                </div>
                <span class="text-xs text-fortress-500">
                  {{ formatDate(log.created_at) }}
                </span>
              </div>

              <!-- Description -->
              <p class="text-sm text-fortress-300 mb-2">{{ log.description }}</p>

              <!-- Additional Details -->
              <div v-if="log.user_query || log.threat_type || log.details" class="mt-2 pt-2 border-t border-fortress-700">
                <div v-if="log.user_query" class="text-xs text-fortress-400 mb-1">
                  <span class="font-medium">Query:</span> {{ log.user_query }}
                </div>
                <div v-if="log.threat_type" class="text-xs text-fortress-400">
                  <span class="font-medium">Threat:</span> {{ log.threat_type }}
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-12">
            <svg class="w-12 h-12 text-fortress-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-fortress-400">No activity logs found</p>
            <p class="text-sm text-fortress-500 mt-1">Try adjusting your filters</p>
          </div>

          <!-- Pagination -->
          <div v-if="activityLogs.length > 0" class="mt-6 flex items-center justify-between pt-4 border-t border-fortress-700">
            <div class="text-sm text-fortress-400">
              Showing {{ filters.offset + 1 }} - {{ Math.min(filters.offset + filters.limit, totalLogs) }} of {{ totalLogs.toLocaleString() }} results
            </div>
            <div class="flex gap-2">
              <button 
                @click="previousPage" 
                :disabled="filters.offset === 0"
                class="px-3 py-1.5 text-sm bg-fortress-800 border border-fortress-700 text-fortress-100 rounded-lg hover:border-secure/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button 
                @click="nextPage" 
                :disabled="!hasMore"
                class="px-3 py-1.5 text-sm bg-fortress-800 border border-fortress-700 text-fortress-100 rounded-lg hover:border-secure/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useActivityLogs } from '@/composables/useActivityLogs'

const {
  activityLogs,
  totalLogs,
  hasMore,
  loading,
  error,
  fetchActivityLogs,
  fetchIncidentTypes,
  formatIncidentType,
  getSeverityColor,
  formatDate,
  criticalCount,
  warningCount,
  infoCount
} = useActivityLogs()

// Filters
const filters = ref({
  userId: null,
  incidentType: null,
  severity: null,
  days: 30,
  limit: 50,
  offset: 0
})

// Incident types for dropdown
const incidentTypes = ref([])

// Load logs
const loadLogs = async () => {
  try {
    // Reset offset when filters change (except when explicitly paginating)
    if (filters.value.offset === 0) {
      filters.value.offset = 0
    }
    await fetchActivityLogs(filters.value)
  } catch (err) {
    console.error('Error loading activity logs:', err)
  }
}

// Pagination
const nextPage = () => {
  filters.value.offset += filters.value.limit
  loadLogs()
}

const previousPage = () => {
  filters.value.offset = Math.max(0, filters.value.offset - filters.value.limit)
  loadLogs()
}

// Initialize
onMounted(async () => {
  try {
    incidentTypes.value = await fetchIncidentTypes()
    await loadLogs()
  } catch (err) {
    console.error('Error initializing activity logs:', err)
  }
})
</script>
