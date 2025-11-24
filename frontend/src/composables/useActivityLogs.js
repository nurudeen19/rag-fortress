import { ref, computed } from 'vue'
import api from '../services/api'

// Singleton state - shared across all components
const activityLogs = ref([])
const totalLogs = ref(0)
const hasMore = ref(false)
const loading = ref(false)
const error = ref(null)

/**
 * ActivityLog Response Schema
 * @typedef {Object} ActivityLog
 * @property {number} id - Unique identifier
 * @property {number} user_id - ID of the user who performed the action
 * @property {string} user_name - Name of the user
 * @property {string} user_department - Department of the user
 * @property {string} incident_type - Type of incident (e.g., "document_access_denied", "malicious_query_blocked")
 * @property {string} severity - Severity level ("info", "warning", "critical")
 * @property {string} description - Human-readable description of the event
 * @property {string|null} details - Additional structured details (JSON string)
 * @property {string|null} user_clearance_level - Clearance level of the user (GENERAL, RESTRICTED, CONFIDENTIAL, HIGHLY_CONFIDENTIAL)
 * @property {string|null} required_clearance_level - Required clearance level for the resource
 * @property {boolean|null} access_granted - Whether access was granted
 * @property {string|null} user_query - The user's query (truncated for privacy)
 * @property {string|null} threat_type - Type of threat detected (prompt_injection, sql_injection, etc.)
 * @property {string|null} ip_address - IP address of the request
 * @property {string} created_at - ISO timestamp of when the event occurred
 * @property {string} updated_at - ISO timestamp of when the record was last updated
 */

/**
 * Get Activity Logs Response Schema
 * @typedef {Object} GetActivityLogsResponse
 * @property {boolean} success - Whether the request was successful
 * @property {ActivityLog[]} logs - Array of activity log entries
 * @property {number} total - Total count of logs matching the filters
 * @property {number} limit - Results per page
 * @property {number} offset - Current pagination offset
 * @property {boolean} has_more - Whether more results are available
 * @property {string|null} error - Error message if success is false
 */

/**
 * Composable for managing user activity logs and security monitoring
 */
export function useActivityLogs() {
  /**
   * Get activity logs with optional filters and pagination
   * 
   * @param {Object} options - Query options
   * @param {number|null} options.userId - Filter by user ID (defaults to current user if not provided)
   * @param {string|null} options.incidentType - Filter by incident type
   * @param {string|null} options.severity - Filter by severity (info, warning, critical)
   * @param {number} options.days - Number of days to look back (1-365, default 30)
   * @param {number} options.limit - Results per page (1-500, default 100)
   * @param {number} options.offset - Pagination offset (default 0)
   * 
   * @returns {Promise<GetActivityLogsResponse>} Activity logs with pagination info
   * 
   * @example
   * const logs = await fetchActivityLogs({
   *   incidentType: 'document_access_denied',
   *   severity: 'critical',
   *   days: 7,
   *   limit: 50,
   *   offset: 0
   * })
   */
  const fetchActivityLogs = async (options = {}) => {
    loading.value = true
    error.value = null
    
    const {
      userId = null,
      incidentType = null,
      severity = null,
      days = 30,
      limit = 50,
      offset = 0
    } = options
    
    try {
      // Build query parameters
      const params = {}
      
      // Always pass days and limit
      if (days) params.days = parseInt(days)
      if (limit) params.limit = parseInt(limit)
      if (offset) params.offset = parseInt(offset)
      
      // Pass filters if provided
      if (userId !== null && userId !== undefined) {
        params.user_id = parseInt(userId)
      }
      if (incidentType) {
        params.incident_type = incidentType
      }
      if (severity) {
        params.severity = severity
      }
      
      const response = await api.get('/v1/activity', { params })
      
      if (response.success) {
        activityLogs.value = response.logs || []
        totalLogs.value = response.total || 0
        hasMore.value = response.has_more || false
        return response
      } else {
        throw new Error(response.error || 'Failed to fetch activity logs')
      }
    } catch (err) {
      console.error('Error fetching activity logs:', err)
      error.value = err.response?.error || err.message
      
      // Set empty state on error
      activityLogs.value = []
      totalLogs.value = 0
      hasMore.value = false
      
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * Get available incident types for filtering
   * 
   * @returns {Promise<Object[]>} Array of incident type objects with value, name, and description
   * 
   * @example
   * const types = await fetchIncidentTypes()
   * // Returns: [
   * //   { value: 'document_access_denied', name: 'Document Access Denied', description: '...' },
   * //   { value: 'malicious_query_blocked', name: 'Malicious Query Blocked', description: '...' },
   * //   ...
   * // ]
   */
  const fetchIncidentTypes = async () => {
    try {
      const response = await api.get('/v1/activity/incident-types')
      
      if (response.success) {
        return response.incident_types || []
      } else {
        throw new Error(response.error || 'Failed to fetch incident types')
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
