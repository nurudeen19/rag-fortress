import { ref, computed } from 'vue'
import axios from 'axios'

// Singleton state - shared across all components
const activityLogs = ref([])
const totalLogs = ref(0)
const hasMore = ref(false)
const loading = ref(false)
const error = ref(null)

/**
 * Composable for managing user activity logs and security monitoring
 */
export function useActivityLogs() {
  /**
   * Get activity logs with optional filters and pagination
   * @param {Object} options - Query options
   * @param {number} options.userId - Filter by user ID
   * @param {string} options.incidentType - Filter by incident type
   * @param {string} options.severity - Filter by severity (info, warning, critical)
   * @param {number} options.days - Number of days to look back (default 30)
   * @param {number} options.limit - Results per page (default 100)
   * @param {number} options.offset - Pagination offset (default 0)
   */
  const fetchActivityLogs = async (options = {}) => {
    loading.value = true
    error.value = null
    
    const {
      userId = null,
      incidentType = null,
      severity = null,
      days = 30,
      limit = 100,
      offset = 0
    } = options
    
    try {
      const params = { days, limit, offset }
      if (userId !== null) params.user_id = userId
      if (incidentType) params.incident_type = incidentType
      if (severity) params.severity = severity
      
      const response = await axios.get('/api/v1/activity', { params })
      
      if (response.data.success) {
        activityLogs.value = response.data.logs
        totalLogs.value = response.data.total
        hasMore.value = response.data.has_more
        return response.data
      } else {
        throw new Error(response.data.error || 'Failed to fetch activity logs')
      }
    } catch (err) {
      console.error('Error fetching activity logs:', err)
      error.value = err.response?.data?.error || err.message
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Get available incident types
   */
  const fetchIncidentTypes = async () => {
    try {
      const response = await axios.get('/api/v1/activity/incident-types')
      
      if (response.data.success) {
        return response.data.incident_types
      } else {
        throw new Error(response.data.error || 'Failed to fetch incident types')
      }
    } catch (err) {
      console.error('Error fetching incident types:', err)
      throw err
    }
  }
  
  /**
   * Format incident type for display
   * @param {string} incidentType - Incident type value
   */
  const formatIncidentType = (incidentType) => {
    const types = {
      'document_access_granted': 'Access Granted',
      'document_access_denied': 'Access Denied',
      'malicious_query_blocked': 'Malicious Query Blocked',
      'query_validation_failed': 'Query Validation Failed',
      'insufficient_clearance': 'Insufficient Clearance',
      'clearance_override_used': 'Override Used',
      'bulk_document_request': 'Bulk Request',
      'sensitive_data_access': 'Sensitive Data Access',
      'suspicious_activity': 'Suspicious Activity',
      'access_pattern_anomaly': 'Access Anomaly'
    }
    return types[incidentType] || incidentType
  }
  
  /**
   * Get severity badge color
   * @param {string} severity - Severity level (info, warning, critical)
   */
  const getSeverityColor = (severity) => {
    const colors = {
      'info': 'blue',
      'warning': 'yellow',
      'critical': 'red'
    }
    return colors[severity] || 'gray'
  }
  
  /**
   * Format date for display
   * @param {string} dateString - ISO date string
   */
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString()
  }
  
  // Computed properties
  const hasCriticalIncidents = computed(() => 
    activityLogs.value.some(log => log.severity === 'critical')
  )
  const criticalCount = computed(() => 
    activityLogs.value.filter(log => log.severity === 'critical').length
  )
  const warningCount = computed(() => 
    activityLogs.value.filter(log => log.severity === 'warning').length
  )
  const infoCount = computed(() => 
    activityLogs.value.filter(log => log.severity === 'info').length
  )
  
  return {
    // State
    activityLogs,
    totalLogs,
    hasMore,
    loading,
    error,
    
    // Actions
    fetchActivityLogs,
    fetchIncidentTypes,
    
    // Helpers
    formatIncidentType,
    getSeverityColor,
    formatDate,
    
    // Computed
    hasCriticalIncidents,
    criticalCount,
    warningCount,
    infoCount
  }
}
