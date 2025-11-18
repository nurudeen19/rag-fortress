import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Public routes
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/auth/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/auth/ForgotPassword.vue'),
      meta: { public: true }
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('../views/auth/ResetPassword.vue'),
      meta: { public: true }
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/auth/Signup.vue'),
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
          component: () => import('../views/system/Dashboard.vue')
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('../views/content/Chat.vue')
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/content/Documents.vue')
        },
        {
          path: 'access-control',
          name: 'access-control',
          component: () => import('../views/admin/AccessControl.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'access-control/user/:userId',
          name: 'user-detail',
          component: () => import('../views/admin/UserDetail.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'invitations',
          name: 'invitations',
          component: () => import('../views/admin/Invitations.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'departments',
          name: 'departments',
          component: () => import('../views/admin/Departments.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'configuration',
          name: 'configuration',
          component: () => import('../views/admin/Configuration.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'logs',
          name: 'logs',
          component: () => import('../views/system/ActivityLogs.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/users/Profile.vue')
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/users/Settings.vue')
        }
      ]
    },

    // Catch all - 404
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/system/NotFound.vue')
    }
  ]
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  const isPublic = to.matched.some(record => record.meta.public)

  console.log(`[Router Guard] Navigating to: ${to.path} (name: ${to.name})`, {
    requiresAuth,
    requiresAdmin,
    isPublic,
    isAuthenticated: authStore.isAuthenticated,
    isAdmin: authStore.isAdmin,
  })

  // Wait for auth initialization
  if (!authStore.initialized) {
    // If we have a token and user in localStorage, we're ready
    if (authStore.token && authStore.user) {
      authStore.initialized = true
    } else if (!authStore.token) {
      // No token, no need to wait
      authStore.initialized = true
    }
  }

  // Check if route requires authentication
  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login with return URL
    console.log(`[Router Guard] Not authenticated, redirecting to login`)
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Check if route requires admin
  if (requiresAdmin && !authStore.isAdmin) {
    // Redirect to dashboard if not admin
    console.log(`[Router Guard] Not admin, redirecting to dashboard. isAdmin: ${authStore.isAdmin}`)
    next({ name: 'dashboard' })
    return
  }

  // If logged in and trying to access public route, redirect to dashboard
  if (isPublic && authStore.isAuthenticated) {
    console.log(`[Router Guard] Logged in, redirecting from public route to dashboard`)
    next({ name: 'dashboard' })
    return
  }

  console.log(`[Router Guard] Allowing navigation`)
  next()
})

// Error handler for navigation failures
router.onError((error) => {
  console.error('[Router Error]', error)
})

export default router
