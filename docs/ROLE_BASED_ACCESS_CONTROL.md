# Role-Based Access Control (RBAC) Implementation

## Overview

The frontend now implements a comprehensive role-based access control system that works in conjunction with backend route guards. This document describes how roles are enforced and how to extend the system.

## Architecture

### Two-Layer Enforcement

1. **Route Guards** (Navigation Level)
   - Prevents unauthorized navigation to protected routes
   - Redirects users to dashboard if they lack required roles
   - Applied in `router/index.js` using `meta.requiresRoles`

2. **UI Layer** (Component Level)
   - Hides navigation links users can't access
   - Shows/hides sensitive components and buttons
   - Uses `useRoleAccess()` composable

### System Roles

Currently supported roles (from backend seeding):
- `user` - Regular user with standard access
- `manager` - Manager with team oversight access
- `admin` - Administrator with full access

## Core Components

### 1. Role Access Composable (`composables/useRoleAccess.js`)

The main composable for role checking throughout the application.

**Methods:**
```javascript
// Check if user has specific role(s)
hasRole(roleName: string | string[]): boolean

// Check if user has permission(s) - for future use
hasPermission(permissionCode: string | string[]): boolean

// Get all accessible navigation items based on user roles
getAvailableNav(): array

// Get navigation items grouped by category
getGroupedNav(): object
```

**Computed Properties:**
```javascript
isAdmin: boolean      // True if user has admin role
isManager: boolean    // True if user has manager or admin role
```

**Usage:**
```javascript
import { useRoleAccess } from '@/composables/useRoleAccess'

export default {
  setup() {
    const { hasRole, isAdmin, getAvailableNav } = useRoleAccess()
    
    // Check single role
    if (hasRole('manager')) { /* ... */ }
    
    // Check multiple roles
    if (hasRole(['manager', 'admin'])) { /* ... */ }
    
    // Get filtered navigation
    const nav = getAvailableNav()
  }
}
```

### 2. Router Configuration (`router/index.js`)

Routes are tagged with `meta.requiresRoles` array:

```javascript
{
  path: 'access-control',
  name: 'access-control',
  component: () => import('../views/admin/AccessControl.vue'),
  meta: { requiresRoles: ['manager', 'admin'] }
},
{
  path: 'departments',
  name: 'departments',
  component: () => import('../views/admin/Departments.vue'),
  meta: { requiresRoles: ['manager', 'admin'] }
},
{
  path: 'activity-logs',
  name: 'activity-logs',
  component: () => import('../views/system/ActivityLogs.vue'),
  meta: { requiresRoles: ['admin'] }
}
```

### 3. Route Guard Logic

The `beforeEach` hook checks:
1. Is user authenticated? (if route requires auth)
2. Does user have required roles? (if route specifies `meta.requiresRoles`)
3. Is user trying to access public route while logged in? (redirect to dashboard)

```javascript
router.beforeEach((to, from, next) => {
  // Check authenticated
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  // Check roles
  if (requiresRoles && requiresRoles.length > 0) {
    const userRoles = authStore.user?.roles?.map(r => r.name) || []
    const hasRequiredRole = requiresRoles.some(r => userRoles.includes(r))
    
    if (!hasRequiredRole) {
      next({ name: 'dashboard' })
      return
    }
  }
  
  next()
})
```

### 4. Dashboard Layout Integration

The sidebar dynamically filters navigation items based on user roles:

```vue
<script setup>
import { useRoleAccess } from '@/composables/useRoleAccess'

const { getAvailableNav } = useRoleAccess()

// Reactively computed based on user's current roles
const navigation = computed(() => getAvailableNav())
</script>

<template>
  <!-- Navigation only shows items user has access to -->
  <router-link
    v-for="item in navigation"
    :key="item.name"
    :to="{ name: item.routeName }"
  >
    {{ item.name }}
  </router-link>
</template>
```

## Navigation Structure

### User (user role)
- Dashboard
- Chat
- Documents
- Profile
- Settings

### Manager (manager role)
- All User items
- Users (Access Control)
- Departments
- Invitations

### Admin (admin role)
- All Manager items
- Activity Logs
- Configuration

## Adding New Role-Protected Routes

### Step 1: Add Route Metadata
```javascript
{
  path: 'new-feature',
  name: 'new-feature',
  component: () => import('../views/NewFeature.vue'),
  meta: { requiresRoles: ['admin'] }  // Add this
}
```

### Step 2: Update Navigation Composable
```javascript
// In useRoleAccess() getAvailableNav()
if (isAdmin.value) {
  nav.push({
    name: 'New Feature',
    path: '/new-feature',
    routeName: 'new-feature',
    icon: 'appropriate-icon',
    roles: ['admin'],
    group: 'admin',
  })
}
```

### Step 3: Optional - Add Component-Level Guards
```vue
<script setup>
import { useRoleAccess } from '@/composables/useRoleAccess'

const { hasRole, isAdmin } = useRoleAccess()
</script>

<template>
  <!-- Only show to admins -->
  <div v-if="isAdmin">
    <button @click="dangerousAction">Delete Everything</button>
  </div>
</template>
```

## Adding New Roles

### 1. Backend (already done)
Roles are managed in `backend/app/seeders/roles_permissions.py`

### 2. Frontend Update
Update `useRoleAccess.js` with new role logic:

```javascript
const isExecutive = computed(() => hasRole(['executive']))

const getAvailableNav = () => {
  // ... existing code ...
  
  if (isExecutive.value) {
    nav.push({
      name: 'Reports',
      path: '/reports',
      routeName: 'reports',
      icon: 'reports',
      roles: ['executive', 'admin'],
      group: 'admin',
    })
  }
  
  return nav.filter(item =>
    item.roles.some(requiredRole => hasRole(requiredRole))
  )
}
```

## Authorization Enforcement

### Backend
All endpoints use `require_role()` dependency:
```python
@router.get("/admin/users")
async def list_users(
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    # Only admins can reach here
```

### Frontend
1. **Route Guard** - Prevents navigation to unauthorized pages
2. **Sidebar Filtering** - Doesn't show links user can't access
3. **API Error Handling** - Backend returns 403 if user tries API call they shouldn't

### Future: Permission-Based Access
Once all features are finalized, add granular permission checks:

```javascript
const canCreateUser = hasPermission('user:create')
const canDeleteDocument = hasPermission('document:delete')
```

See `PERMISSIONS_SYSTEM.md` when implementing fine-grained permissions.

## Testing Role Access

### Test in DevTools Console
```javascript
// Check user roles
authStore.user.roles

// Check if has role
const { useRoleAccess } = require('@/composables/useRoleAccess')
const { hasRole } = useRoleAccess()
hasRole('admin')

// Check available nav
const { getAvailableNav } = useRoleAccess()
getAvailableNav().map(item => item.name)
```

### Test Route Guards
1. Login as user with limited roles
2. Try to access admin URL directly (e.g., `/access-control`)
3. Should redirect to dashboard

## Troubleshooting

### Sidebar Items Not Appearing
- Check user.roles in DevTools
- Verify route metadata has `requiresRoles`
- Check role name spelling (case-sensitive)

### Can Access Route But Sidebar Hidden
- Route guard is working (preventing access)
- Component likely has logic preventing page load
- Check for additional `v-if` checks in component

### API Calls Fail with 403
- Backend route guard is working
- Frontend doesn't check - this is correct
- Backend prevents unauthorized access

## Security Notes

**Important:** Frontend role checks are for UX only. All security enforcement happens on the backend:
- Routes have `require_role()` dependency
- Endpoints verify authorization before returning data
- Frontend checks prevent unnecessary API calls
- Backend always validates permissions

Do not rely on frontend role checks for security. Always validate on backend.

## Migration Path

### Current: Role-Based (What we have now)
- Simple, fast
- Good UX
- Sufficient for current feature set

### Future: Permission-Based
- Fine-grained control
- More scalable
- Will extend current system
- Use `hasPermission()` alongside `hasRole()`

See backend `app/services/user/role_permission_service.py` for permission checking implementation.
