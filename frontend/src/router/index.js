import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Public routes
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPassword.vue'),
      meta: { public: true }
    },

    // Protected routes with dashboard layout
    {
      path: '/',
      component: () => import('../layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard'
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/Dashboard.vue')
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('../views/Chat.vue')
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/Documents.vue')
        },
        {
          path: 'access-control',
          name: 'access-control',
          component: () => import('../views/AccessControl.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'configuration',
          name: 'configuration',
          component: () => import('../views/Configuration.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'logs',
          name: 'logs',
          component: () => import('../views/ActivityLogs.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/Profile.vue')
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/Settings.vue')
        }
      ]
    },

    // Catch all - 404
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFound.vue')
    }
  ]
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  const isPublic = to.matched.some(record => record.meta.public)

  // Check if route requires authentication
  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login with return URL
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Check if route requires admin
  if (requiresAdmin && !authStore.isAdmin) {
    // Redirect to dashboard if not admin
    next({ name: 'dashboard' })
    return
  }

  // If logged in and trying to access public route, redirect to dashboard
  if (isPublic && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }

  next()
})

export default router
