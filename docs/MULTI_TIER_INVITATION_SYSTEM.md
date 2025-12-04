# Multi-Tier Invitation System Implementation

**Implementation Date:** December 4, 2025  
**Status:** ✅ Complete - Ready for Testing

## Overview

Implemented a comprehensive multi-tier invitation system that allows both **Admins** and **Department Managers** to invite users with role-based authorization and security clearance assignment.

## Architecture

### Authorization Tiers

1. **Admins**
   - Can invite users to any department
   - Can assign any clearance level (1-4)
   - No restrictions on invitation permissions

2. **Department Managers**
   - Can only invite to their own department
   - Cannot exceed their own clearance levels
   - Organization clearance limited to their `org_level_permission`
   - Department clearance limited to their `department_level_permission`

### Security Clearance Levels

| Value | Label | Description |
|-------|-------|-------------|
| 1 | GENERAL | Public/General access |
| 2 | RESTRICTED | Limited access |
| 3 | CONFIDENTIAL | Confidential information |
| 4 | HIGHLY_CONFIDENTIAL | Top-level classified |

## Backend Implementation

### 1. Authorization Logic (`backend/app/handlers/users.py`)

**Helper Functions:**
- `can_invite_user(inviter_clearance, target_dept_id)`: Checks if inviter can invite to target department
- `validate_clearance_limits(requested_org, requested_dept, inviter_org_max, inviter_dept_max, is_admin)`: Validates clearance levels

**Handler Updates:**
- `handle_invite_user()`: Now includes authorization checks before creating invitation
  - Gets inviter clearance from cache
  - Validates department access
  - Validates clearance limits
  - Passes clearances to invitation service

### 2. Security Dependency (`backend/app/core/security.py`)

**New Dependency:**
```python
async def require_admin_or_department_manager(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> User
```
- Checks if user is admin OR department manager
- Returns user if authorized, raises 403 otherwise

### 3. Route Updates (`backend/app/routes/users.py`)

**Updated Endpoint:**
- `POST /api/v1/admin/users/invite`
  - Replaced `require_role("admin")` with `require_admin_or_department_manager`
  - Now accepts `org_level_permission` and `department_level_permission`

**New Endpoint:**
- `GET /api/v1/admin/users/me/invitation-limits`
  - Returns user's invitation permissions
  - Provides clearance level options
  - Indicates allowed departments

### 4. Schemas (`backend/app/schemas/user.py`)

**Updated:**
- `UserInviteRequest`: Added `org_level_permission` and `department_level_permission` fields

**New Schemas:**
- `ClearanceLevelOption`: Clearance level dropdown option
- `InvitationLimitsResponse`: Response schema for invitation limits endpoint

### 5. Models & Services

**Model Updates:**
- `UserInvitation`: Added `org_level_permission` and `department_level_permission` columns

**Service Updates:**
- `InvitationService.create_invitation()`: Accepts and stores clearance parameters

**Cache Updates:**
- `user_clearance_cache.py`: Expanded to include:
  - `is_admin`: Whether user has admin role
  - `is_department_manager`: Whether user manages a department
  - `org_clearance_value`: User's org clearance limit (1-4)
  - `dept_clearance_value`: User's dept clearance limit (1-4)

## Frontend Implementation

### 1. Invitation Modal (`frontend/src/components/admin/UserInviteModal.vue`)

**New Features:**
- Organization clearance dropdown (required)
- Department clearance dropdown (optional, shown when department selected)
- Clearance levels filtered by user's maximum allowed values
- Department dropdown auto-filled and disabled for managers
- Loads invitation limits on mount

**New Refs:**
```javascript
orgLevelPermission: ref(1)
deptLevelPermission: ref(null)
invitationLimits: ref(null)
```

**New Computed Properties:**
- `availableOrgLevels`: Filters org clearance options by user's max
- `availableDeptLevels`: Filters dept clearance options by user's max
- `availableDepartments`: Shows only departments user can invite to

**New Methods:**
- `loadInvitationLimits()`: Fetches user's invitation permissions from API

### 2. Admin Store (`frontend/src/stores/admin.js`)

**New Action:**
```javascript
async function getInvitationLimits()
```
- Fetches `/v1/admin/users/me/invitation-limits`
- Returns user's invitation capabilities

**Updated Action:**
```javascript
async function inviteUser(..., orgLevelPermission, departmentLevelPermission)
```
- Accepts two new clearance parameters
- Sends them to backend API

### 3. Invitations View (`frontend/src/views/admin/Invitations.vue`)

**Updated:**
- `handleInviteUser()`: Passes clearance parameters to store action

## API Endpoints

### Get Invitation Limits
```
GET /api/v1/admin/users/me/invitation-limits
```

**Response:**
```json
{
  "can_invite": true,
  "is_admin": false,
  "is_department_manager": true,
  "allowed_departments": [5],
  "max_org_clearance": 3,
  "max_dept_clearance": 4,
  "clearance_levels": [
    {"value": 1, "label": "GENERAL"},
    {"value": 2, "label": "RESTRICTED"},
    {"value": 3, "label": "CONFIDENTIAL"},
    {"value": 4, "label": "HIGHLY_CONFIDENTIAL"}
  ]
}
```

### Send Invitation
```
POST /api/v1/admin/users/invite
```

**Request:**
```json
{
  "email": "user@example.com",
  "role_id": 2,
  "department_id": 5,
  "is_manager": false,
  "org_level_permission": 2,
  "department_level_permission": 3,
  "invitation_message": "Welcome!",
  "invitation_link_template": "https://app.com/signup?token={token}"
}
```

**Response:**
```json
{
  "message": "Invitation sent to user@example.com"
}
```

## User Flows

### Admin Inviting User

1. Admin clicks "Invite User" button
2. Modal loads with all departments available
3. Admin selects department, role, and clearance levels (no restrictions)
4. Admin submits invitation
5. Backend validates and creates invitation with specified clearances

### Department Manager Inviting User

1. Manager clicks "Invite User" button
2. Modal loads with only their department pre-selected and disabled
3. Clearance dropdowns show only levels ≤ manager's own levels
4. Manager selects role and clearances within limits
5. Backend validates:
   - Department matches manager's department
   - Org clearance ≤ manager's org clearance
   - Dept clearance ≤ manager's dept clearance
6. If valid, creates invitation

## Validation Rules

### Backend Validation

1. **Department Access:**
   - Admins: ✅ Any department
   - Managers: ✅ Only their own department
   - Other users: ❌ Cannot invite

2. **Organization Clearance:**
   - Admins: ✅ Any level (1-4)
   - Managers: ✅ Only levels ≤ their `org_clearance_value`

3. **Department Clearance:**
   - Admins: ✅ Any level (1-4)
   - Managers: ✅ Only levels ≤ their `dept_clearance_value`
   - Managers without dept clearance: ❌ Cannot assign dept clearance

### Frontend Validation

- Email format validation
- Required fields (email, role, org clearance)
- Clearance dropdowns pre-filtered by backend limits
- Department dropdown disabled for managers

## Error Messages

| Scenario | Error Message |
|----------|--------------|
| Manager inviting to other dept | "Department managers can only invite users to their own department" |
| Non-admin/manager trying to invite | "This action requires admin role or department manager status" |
| Org clearance too high | "Cannot assign organization clearance higher than your own level (X)" |
| Dept clearance too high | "Cannot assign department clearance higher than your own level (X)" |
| Manager without dept clearance | "You do not have department clearance to assign" |
| Clearance cache not found | "Could not verify your permissions. Please try again." |

## Caching Strategy

**User Clearance Cache:**
- **Key:** `user_clearance:{user_id}`
- **TTL:** Matches access token expiry (30 minutes default)
- **Contents:**
  ```python
  {
      "user_id": int,
      "security_level": str,
      "department_security_level": str,
      "is_admin": bool,
      "is_department_manager": bool,
      "org_clearance_value": int,
      "dept_clearance_value": Optional[int],
      "department_id": Optional[int]
  }
  ```

**Benefits:**
- Authorization checks don't require DB queries
- Fast permission validation
- Consistent with token-based authentication

## Testing Checklist

### Backend Tests

- [ ] Admin can invite to any department
- [ ] Admin can assign any clearance level
- [ ] Manager can invite to own department
- [ ] Manager cannot invite to other department
- [ ] Manager cannot exceed org clearance limit
- [ ] Manager cannot exceed dept clearance limit
- [ ] Manager without dept clearance cannot assign dept clearance
- [ ] Regular user cannot access invite endpoint (403)
- [ ] Invitation limits endpoint returns correct data
- [ ] Cache includes authorization fields

### Frontend Tests

- [ ] Modal loads invitation limits on mount
- [ ] Admin sees all departments
- [ ] Manager sees only their department (disabled)
- [ ] Clearance dropdowns filtered correctly
- [ ] Form submits with clearance values
- [ ] Error messages display properly
- [ ] Department clearance hidden when no department selected

### Integration Tests

- [ ] End-to-end invitation flow (admin)
- [ ] End-to-end invitation flow (manager)
- [ ] Invitation email includes clearance info
- [ ] Signup with token creates user with correct clearances
- [ ] Permission checks work without cache (DB fallback)

## Files Modified

### Backend
- ✅ `backend/app/handlers/users.py` - Authorization logic
- ✅ `backend/app/routes/users.py` - Endpoint updates
- ✅ `backend/app/core/security.py` - New dependency
- ✅ `backend/app/schemas/user.py` - New schemas
- ✅ `backend/app/models/user_invitation.py` - Clearance columns
- ✅ `backend/app/services/user/invitation_service.py` - Clearance params
- ✅ `backend/app/utils/user_clearance_cache.py` - Cache expansion

### Frontend
- ✅ `frontend/src/components/admin/UserInviteModal.vue` - Clearance UI
- ✅ `frontend/src/stores/admin.js` - API integration
- ✅ `frontend/src/views/admin/Invitations.vue` - Parameter passing

## Migration Required

**Database Migration Needed:**
```sql
-- Add clearance columns to user_invitations table
ALTER TABLE user_invitations 
ADD COLUMN org_level_permission INTEGER NOT NULL DEFAULT 1,
ADD COLUMN department_level_permission INTEGER;
```

Run migration:
```bash
cd backend
alembic revision --autogenerate -m "Add clearance fields to user invitations"
alembic upgrade head
```

## Next Steps

1. **Create Database Migration:**
   - Generate Alembic migration for `user_invitations` table
   - Apply migration to dev/staging/prod

2. **Integration Testing:**
   - Test admin invitation flow
   - Test manager invitation flow
   - Test authorization edge cases
   - Test clearance validation

3. **User Documentation:**
   - Update admin guide with new clearance fields
   - Document manager invitation capabilities
   - Add clearance level descriptions

4. **Monitoring:**
   - Add metrics for invitation attempts by tier
   - Log authorization failures for audit
   - Track clearance distribution

## Benefits

✅ **Scalability:** Department managers can onboard their own team members  
✅ **Security:** Clearances enforced at invitation time  
✅ **Flexibility:** Two-level clearance system (org + dept)  
✅ **Performance:** Cached authorization data prevents DB queries  
✅ **User Experience:** Smart UI adapts to user's permissions  
✅ **Audit Trail:** Activity logs capture invitation events  

## Known Limitations

- Managers cannot delegate manager status (only admins can)
- No bulk invitation feature (one at a time)
- Clearance levels cannot be changed after invitation sent (must resend)
- Department managers must have a department assigned

## Future Enhancements

- [ ] Bulk invitation upload (CSV)
- [ ] Invitation templates with default clearances
- [ ] Temporary clearance elevation requests
- [ ] Invitation approval workflow
- [ ] Self-service invitation links with org-level clearance only
