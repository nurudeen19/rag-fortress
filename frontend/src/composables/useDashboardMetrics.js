import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

export function useDashboardMetrics() {
  const authStore = useAuthStore()
  
  const adminMetrics = ref({
    total_documents: 0,
    pending_documents: 0,
    approved_documents: 0,
    rejected_documents: 0,
    total_jobs: 0,
    jobs_processed: 0,
    jobs_failed: 0,
    jobs_pending: 0,
    jobs_in_progress: 0,
    total_users: 0,
    total_notifications: 0,
    unread_notifications: 0,
    system_health: 'healthy',
  })
  
  const userMetrics = ref({
    my_documents: 0,
    pending_approval: 0,
    approved_documents: 0,
    my_unread_notifications: 0,
    total_documents: 0,
    total_approved_documents: 0,
  })
  
  const isLoading = ref(false)
  const error = ref(null)
  const cacheStatus = ref(null)
  
  async function loadAdminMetrics() {
    if (!authStore.isAdmin) return
    
    isLoading.value = true
    error.value = null
    
    try {
      const response = await api.get('/v1/dashboard/admin/metrics')
      if (response && response.status === 'ok') {
        adminMetrics.value = response.data
        cacheStatus.value = response.cached ? 'cached' : 'fresh'
      }
    } catch (err) {
      error.value = err.message || 'Failed to load admin metrics'
      console.error('Error loading admin metrics:', err)
    } finally {
      isLoading.value = false
    }
  }
  
  async function loadUserMetrics() {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await api.get('/v1/dashboard/user/metrics')
      if (response && response.status === 'ok') {
        userMetrics.value = response.data
      }
    } catch (err) {
      error.value = err.message || 'Failed to load user metrics'
      console.error('Error loading user metrics:', err)
    } finally {
      isLoading.value = false
    }
  }
  
  async function loadMetrics() {
    if (authStore.isAdmin) {
      await loadAdminMetrics()
    } else {
      await loadUserMetrics()
    }
  }
  
  // Compute derived metrics
  const adminComputed = computed(() => ({
    documentApprovalRate: adminMetrics.value.total_documents > 0
      ? Math.round((adminMetrics.value.approved_documents / adminMetrics.value.total_documents) * 100)
      : 0,
    jobSuccessRate: adminMetrics.value.total_jobs > 0
      ? Math.round((adminMetrics.value.jobs_processed / adminMetrics.value.total_jobs) * 100)
      : 0,
    pendingWork: adminMetrics.value.pending_documents + adminMetrics.value.jobs_pending,
  }))
  
  const userComputed = computed(() => ({
    approvalRate: userMetrics.value.my_documents > 0
      ? Math.round((userMetrics.value.approved_documents / userMetrics.value.my_documents) * 100)
      : 0,
    remainingToApprove: userMetrics.value.my_documents - userMetrics.value.approved_documents - userMetrics.value.rejected_documents,
  }))
  
  onMounted(() => {
    loadMetrics()
  })
  
  return {
    adminMetrics,
    userMetrics,
    isLoading,
    error,
    cacheStatus,
    loadMetrics,
    loadAdminMetrics,
    loadUserMetrics,
    adminComputed,
    userComputed,
  }
}
