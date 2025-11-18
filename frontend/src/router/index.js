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
          component: () => import('../views/system/Dashboard.vue'),
          meta: { requiresRoles: ['user', 'manager', 'admin'] }
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('../views/content/Chat.vue'),
          meta: { requiresRoles: ['user', 'manager', 'admin'] }
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/content/Documents.vue'),
          meta: { requiresRoles: ['user', 'manager', 'admin'] }
        },
        {
          path: 'access-control',
          name: 'access-control',
          component: () => import('../views/admin/AccessControl.vue'),
          meta: { requiresRoles: ['manager', 'admin'] }
        },
        {
          path: 'access-control/user/:userId',
          name: 'user-detail',
          component: () => import('../views/admin/UserDetail.vue'),
          meta: { requiresRoles: ['manager', 'admin'] }
        },
        {
          path: 'invitations',
          name: 'invitations',
          component: () => import('../views/admin/Invitations.vue'),
          meta: { requiresRoles: ['manager', 'admin'] }
        },
        {
          path: 'departments',
          name: 'departments',
          component: () => import('../views/admin/Departments.vue'),
          meta: { requiresRoles: ['manager', 'admin'] }
        },
        {
          path: 'configuration',
          name: 'configuration',
          component: () => import('../views/admin/Configuration.vue'),
          meta: { requiresRoles: ['admin'] }
        },
        {
          path: 'activity-logs',
          name: 'activity-logs',
          component: () => import('../views/system/ActivityLogs.vue'),
          meta: { requiresRoles: ['admin'] }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/users/Profile.vue'),
          meta: { requiresRoles: ['user', 'manager', 'admin'] }
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/users/Settings.vue'),
          meta: { requiresRoles: ['user', 'manager', 'admin'] }
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

// Navigation guard for role-based access control
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresRoles = to.matched.find(record => record.meta.requiresRoles)?.meta?.requiresRoles
  const isPublic = to.matched.some(record => record.meta.public)

  console.log(`[Router Guard] Navigating to: ${to.path}`, {
    requiresAuth,
    requiresRoles,
    isPublic,
    isAuthenticated: authStore.isAuthenticated,
    userRoles: authStore.user?.roles?.map(r => r.name) || [],
  })

  // Wait for auth initialization
  if (!authStore.initialized) {
    if (authStore.token && authStore.user) {
      authStore.initialized = true
    } else if (!authStore.token) {
      authStore.initialized = true
    }
  }

  // Check if route requires authentication
  if (requiresAuth && !authStore.isAuthenticated) {
    console.log(`[Router Guard] Not authenticated, redirecting to login`)
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Check if route requires specific roles
  if (requiresRoles && requiresRoles.length > 0) {
    const userRoles = authStore.user?.roles?.map(r => r.name) || []
    const hasRequiredRole = requiresRoles.some(requiredRole => userRoles.includes(requiredRole))

    if (!hasRequiredRole) {
      console.log(`[Router Guard] Insufficient role privileges. Required: ${requiresRoles}, User has: ${userRoles}`)
      // Redirect to dashboard if user doesn't have required role
      next({ name: 'dashboard' })
      return
    }
  }

  // If logged in and trying to access public route, redirect to dashboard
  if (isPublic && authStore.isAuthenticated) {
    console.log(`[Router Guard] Logged in, redirecting from public route to dashboard`)
    next({ name: 'dashboard' })
    return
  }

  console.log(`[Router Guard] Access granted`)
  next()
})

// Error handler for navigation failures
router.onError((error) => {
  console.error('[Router Error]', error)
})

export default router
