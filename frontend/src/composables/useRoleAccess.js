import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

/**
 * Composable for role-based access control on the frontend.
 * 
 * Provides utilities to:
 * - Check if user has a specific role
 * - Check if user has a specific permission (future use)
 * - Get filtered navigation based on user roles
 * 
 * This is a UX/presentation layer - all access control is ultimately enforced
 * by the backend. This prevents showing unusable links and improves UX.
 */
export function useRoleAccess() {
  const authStore = useAuthStore()

  const normalizeRoleName = (role) => {
    if (!role) return null
    if (typeof role === 'string') return role.toLowerCase()
    if (typeof role.name === 'string' && role.name.length > 0) {
      return role.name.toLowerCase()
    }
    if (typeof role.code === 'string' && role.code.length > 0) {
      return role.code.toLowerCase()
    }
    return null
  }

  const normalizedRoles = computed(() => {
    const roles = authStore.user?.roles || []
    const normalized = new Set()
    roles.forEach(role => {
      const name = normalizeRoleName(role)
      if (name) normalized.add(name)
    })
    if (!normalized.size && authStore.isAuthenticated) {
      normalized.add('user')
    }
    return normalized
  })

  /**
   * Check if user has a specific role
   * @param {string|string[]} roleName - Role name(s) to check
   * @returns {boolean} True if user has any of the specified role(s)
   */
  const hasRole = (roleName) => {
    if (!normalizedRoles.value.size) return false
    const roles = Array.isArray(roleName) ? roleName : [roleName]
    return roles.some(r => normalizedRoles.value.has(r.toLowerCase()))
  }

  /**
   * Check if user has a specific permission (for future use)
   * @param {string|string[]} permissionCode - Permission code(s) to check
   * @returns {boolean} True if user has any of the specified permission(s)
   */
  const hasPermission = (permissionCode) => {
    if (!authStore.user?.permissions) return false
    const permissions = Array.isArray(permissionCode) ? permissionCode : [permissionCode]
    return permissions.some(p => authStore.user.permissions.some(perm => perm.code === p))
  }

  /**
   * Check if user is admin
   * @returns {boolean} True if user has admin role
   */
  const isAdmin = computed(() => normalizedRoles.value.has('admin'))

  /**
   * Check if user is manager or admin
   * @returns {boolean} True if user has manager or admin role
   */
  const isManager = computed(() =>
    normalizedRoles.value.has('manager') || normalizedRoles.value.has('admin')
  )

  /**
   * Get navigation items filtered by user role
   * Returns array of navigation objects that user has access to
   * @returns {array} Filtered navigation items
   */
  const getAvailableNav = () => {
    // Base navigation - accessible to all authenticated users
    const nav = [
      {
        name: 'Dashboard',
        path: '/dashboard',
        routeName: 'dashboard',
        icon: 'dashboard',
        roles: ['user', 'manager', 'admin'],
        group: 'main',
      },
      {
        name: 'Chat',
        path: '/chat',
        routeName: 'chat',
        icon: 'chat',
        roles: ['user', 'manager', 'admin'],
        group: 'main',
      },
    ]

    // Documents view - show Knowledge Base for admins, My Uploads for regular users
    if (isAdmin.value) {
      nav.push({
        name: 'Knowledge Base',
        path: '/knowledge-base',
        routeName: 'knowledge-base',
        icon: 'knowledge',
        roles: ['admin'],
        group: 'main',
      })
    } else {
      nav.push({
        name: 'My Uploads',
        path: '/my-uploads',
        routeName: 'my-uploads',
        icon: 'documents',
        roles: ['user', 'manager'],
        group: 'main',
      })
    }

    // Manager/Admin only navigation
    if (isManager.value) {
      nav.push(
        {
          name: 'Users',
          path: '/access-control',
          routeName: 'access-control',
          icon: 'users',
          roles: ['manager', 'admin'],
          group: 'admin',
        },
        {
          name: 'Departments',
          path: '/departments',
          routeName: 'departments',
          icon: 'settings',
          roles: ['admin'],
          group: 'admin',
        },
        {
          name: 'Invitations',
          path: '/invitations',
          routeName: 'invitations',
          icon: 'invitations',
          roles: ['manager', 'admin'],
          group: 'admin',
        }
      )
    }

    // User features - NOT available to admins (admins review these, not submit them)
    if (!isAdmin.value) {
      nav.push(
        {
          name: 'Request Access',
          path: '/request-access',
          routeName: 'request-access',
          icon: 'key',
          roles: ['user', 'manager'],
          group: 'user',
        },
        {
          name: 'Report Error',
          path: '/error-reports',
          routeName: 'error-reports',
          icon: 'alerts',
          roles: ['user', 'manager'],
          group: 'user',
        }
      )
    }

    // Manager only navigation
    if (!isAdmin.value && isManager.value) {
      nav.push({
        name: 'Override Requests',
        path: '/permission-override-requests',
        routeName: 'permission-override-requests',
        icon: 'key',
        roles: ['manager'],
        group: 'admin',
      })
    }

    // Admin only navigation
    if (isAdmin.value) {
      nav.push({
        name: 'Override Requests',
        path: '/permission-override-requests',
        routeName: 'permission-override-requests',
        icon: 'key',
        roles: ['admin'],
        group: 'admin',
      })
      nav.push({
        name: 'Error Reports',
        path: '/error-reports',
        routeName: 'admin-error-reports',
        icon: 'alerts',
        roles: ['admin'],
        group: 'admin',
      })
      nav.push({
        name: 'System Settings',
        path: '/system-settings',
        routeName: 'system-settings',
        icon: 'settings',
        roles: ['admin'],
        group: 'admin',
      })
    }

    // Filter to only items user has role for
    return nav.filter(item =>
      item.roles.some(requiredRole => normalizedRoles.value.has(requiredRole.toLowerCase()))
    )
  }

  /**
   * Get navigation items grouped by category (main, admin, etc)
   * @returns {object} Navigation items grouped by group name
   */
  const getGroupedNav = () => {
    const nav = getAvailableNav()
    const grouped = {}

    nav.forEach(item => {
      if (!grouped[item.group]) {
        grouped[item.group] = []
      }
      grouped[item.group].push(item)
    })

    return grouped
  }

  return {
    // Methods
    hasRole,
    hasPermission,
    getAvailableNav,
    getGroupedNav,
    // Computed
    isAdmin,
    isManager,
  }
}
