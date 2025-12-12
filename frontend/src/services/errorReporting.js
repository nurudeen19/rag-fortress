/**
 * Error Reporting API Service
 * Handles all error reporting operations (create, list, update, image upload)
 */

import api from './api'

const ERROR_REPORTS_BASE_URL = '/error-reports'
const ADMIN_ERROR_REPORTS_BASE_URL = '/admin/error-reports'

/**
 * User error reporting operations
 */
export const userErrorReporting = {
  /**
   * Create a new error report
   * @param {Object} payload - Error report data
   * @param {string} payload.title - Brief error description
   * @param {string} payload.description - Detailed error description
   * @param {string} payload.category - Error category (llm_error, retrieval_error, etc.)
   * @param {number|null} payload.conversation_id - Optional conversation ID
   * @returns {Promise<Object>} Created error report
   */
  createReport: async (payload) => {
    return api.post(ERROR_REPORTS_BASE_URL, payload)
  },

  /**
   * Get user's error reports with optional filtering
   * @param {Object} options - Query options
   * @param {string|null} options.status - Filter by status
   * @param {number} options.limit - Number of results (1-100)
   * @param {number} options.offset - Pagination offset
   * @returns {Promise<Object>} List of error reports
   */
  getReports: async (options = {}) => {
    const { status = null, limit = 20, offset = 0 } = options
    const params = new URLSearchParams()
    
    if (status) params.append('status', status)
    params.append('limit', limit)
    params.append('offset', offset)
    
    return api.get(`${ERROR_REPORTS_BASE_URL}?${params.toString()}`)
  },

  /**
   * Upload image for error report
   * @param {number} reportId - Error report ID
   * @param {File} file - Image file to upload
   * @returns {Promise<Object>} Upload response with filename
   */
  uploadImage: async (reportId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post(`${ERROR_REPORTS_BASE_URL}/${reportId}/image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

/**
 * Admin error reporting operations
 */
export const adminErrorReporting = {
  /**
   * Get all error reports (admin view)
   * @param {Object} options - Query options
   * @param {string|null} options.status - Filter by status
   * @param {string|null} options.category - Filter by category
   * @param {number} options.limit - Number of results (1-100)
   * @param {number} options.offset - Pagination offset
   * @returns {Promise<Object>} List of all error reports with dashboard metrics
   */
  getReports: async (options = {}) => {
    const { status = null, category = null, limit = 20, offset = 0 } = options
    const params = new URLSearchParams()
    
    if (status) params.append('status', status)
    if (category) params.append('category', category)
    params.append('limit', limit)
    params.append('offset', offset)
    
    return api.get(`${ADMIN_ERROR_REPORTS_BASE_URL}?${params.toString()}`)
  },

  /**
   * Update error report status and notes (admin only)
   * @param {number} reportId - Error report ID
   * @param {Object} payload - Update data
   * @param {string} payload.status - New status (OPEN, INVESTIGATING, RESOLVED, etc.)
   * @param {string|null} payload.admin_notes - Admin notes/comments
   * @param {number|null} payload.assigned_to - Admin user ID to assign to
   * @returns {Promise<Object>} Updated error report
   */
  updateReport: async (reportId, payload) => {
    return api.patch(`${ADMIN_ERROR_REPORTS_BASE_URL}/${reportId}`, payload)
  }
}

/**
 * Error report status and category constants
 */
// Backend enums are lowercase snake_case; keep constants here as single source of truth
export const ERROR_REPORT_STATUS = {
  OPEN: 'open',
  INVESTIGATING: 'investigating',
  ACKNOWLEDGED: 'acknowledged',
  RESOLVED: 'resolved',
  DUPLICATE: 'duplicate',
  NOT_REPRODUCIBLE: 'not_reproducible',
  WONT_FIX: 'wont_fix'
}

export const ERROR_REPORT_CATEGORY = {
  LLM_ERROR: 'llm_error',
  RETRIEVAL_ERROR: 'retrieval_error',
  VALIDATION_ERROR: 'validation_error',
  PERFORMANCE: 'performance',
  UI_UX: 'ui_ux',
  PERMISSIONS: 'permissions',
  DATA_ACCURACY: 'data_accuracy',
  SYSTEM_ERROR: 'system_error',
  OTHER: 'other'
}

export const STATUS_DISPLAY = {
  [ERROR_REPORT_STATUS.OPEN]: { label: 'Open', color: 'blue', icon: 'alert' },
  [ERROR_REPORT_STATUS.INVESTIGATING]: { label: 'Investigating', color: 'yellow', icon: 'search' },
  [ERROR_REPORT_STATUS.ACKNOWLEDGED]: { label: 'Acknowledged', color: 'purple', icon: 'check' },
  [ERROR_REPORT_STATUS.RESOLVED]: { label: 'Resolved', color: 'green', icon: 'checkmark' },
  [ERROR_REPORT_STATUS.DUPLICATE]: { label: 'Duplicate', color: 'gray', icon: 'copy' },
  [ERROR_REPORT_STATUS.NOT_REPRODUCIBLE]: { label: 'Not Reproducible', color: 'gray', icon: 'x' },
  [ERROR_REPORT_STATUS.WONT_FIX]: { label: "Won't Fix", color: 'gray', icon: 'ban' }
}

export const CATEGORY_DISPLAY = {
  [ERROR_REPORT_CATEGORY.LLM_ERROR]: { label: 'LLM Error', icon: 'brain', color: 'red' },
  [ERROR_REPORT_CATEGORY.RETRIEVAL_ERROR]: { label: 'Retrieval Error', icon: 'search', color: 'red' },
  [ERROR_REPORT_CATEGORY.VALIDATION_ERROR]: { label: 'Validation Error', icon: 'alert', color: 'orange' },
  [ERROR_REPORT_CATEGORY.PERFORMANCE]: { label: 'Performance', icon: 'zap', color: 'yellow' },
  [ERROR_REPORT_CATEGORY.UI_UX]: { label: 'UI/UX', icon: 'layout', color: 'blue' },
  [ERROR_REPORT_CATEGORY.PERMISSIONS]: { label: 'Permissions', icon: 'lock', color: 'purple' },
  [ERROR_REPORT_CATEGORY.DATA_ACCURACY]: { label: 'Data Accuracy', icon: 'database', color: 'orange' },
  [ERROR_REPORT_CATEGORY.SYSTEM_ERROR]: { label: 'System Error', icon: 'alert-triangle', color: 'red' },
  [ERROR_REPORT_CATEGORY.OTHER]: { label: 'Other', icon: 'help-circle', color: 'gray' }
}
