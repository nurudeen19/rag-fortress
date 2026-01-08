import axios from 'axios'

// Cookie configuration from environment
const COOKIE_ACCESS_TOKEN_MAX_AGE = parseInt(import.meta.env.VITE_COOKIE_ACCESS_TOKEN_MAX_AGE || '1800')
const COOKIE_REFRESH_TOKEN_MAX_AGE = parseInt(import.meta.env.VITE_COOKIE_REFRESH_TOKEN_MAX_AGE || '604800')

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  withCredentials: true,  // Enable sending httpOnly cookies
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Cookies are sent automatically with withCredentials: true
    // No need to manually add Authorization header
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config
    
    // Handle 401 Unauthorized - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => {
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        // Try to refresh the access token
        await api.post('/v1/auth/refresh')
        isRefreshing = false
        processQueue(null)
        
        // Retry the original request
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed - redirect to login
        isRefreshing = false
        processQueue(refreshError)
        
        // Dynamic import to avoid circular dependency
        const { default: router } = await import('../router')
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
        
        return Promise.reject(refreshError)
      }
    }
    
    // Log 403 Forbidden errors (demo mode, permissions, etc.)
    if (error.response?.status === 403) {
      console.error('403 Forbidden:', error.response.data)
    }
    
    // General error logging
    console.error('API Error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })
    
    return Promise.reject(error)
  }
)

export default api
