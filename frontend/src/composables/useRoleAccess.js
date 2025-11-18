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

  /**
   * Check if user has a specific role
   * @param {string|string[]} roleName - Role name(s) to check
   * @returns {boolean} True if user has any of the specified role(s)
   */
  const hasRole = (roleName) => {
    if (!authStore.user?.roles) return false
    const roles = Array.isArray(roleName) ? roleName : [roleName]
    return roles.some(r => authStore.user.roles.some(userRole => userRole.name === r))
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
  const isAdmin = computed(() => hasRole('admin'))

  /**
   * Check if user is manager or admin
   * @returns {boolean} True if user has manager or admin role
   */
  const isManager = computed(() => hasRole(['manager', 'admin']))

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
        badge: '2',
      },
      {
        name: 'Knowledge Base',
        path: '/knowledge-base',
        routeName: 'knowledge-base',
        icon: 'knowledge',
        roles: ['user', 'manager', 'admin'],
        group: 'main',
      },
    ]

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
          roles: ['manager', 'admin'],
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

    // Admin only navigation
    if (isAdmin.value) {
      nav.push({
        name: 'Activity Logs',
        path: '/activity-logs',
        routeName: 'activity-logs',
        icon: 'logs',
        roles: ['admin'],
        group: 'admin',
      })
    }

    // Filter to only items user has role for
    return nav.filter(item =>
      item.roles.some(requiredRole => hasRole(requiredRole))
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
