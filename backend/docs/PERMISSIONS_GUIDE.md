# Permissions & Access Control Guide

## Overview

RAG Fortress implements a comprehensive Role-Based Access Control (RBAC) system with:
- Department-based access control
- Four security clearance levels
- Temporary permission overrides with automatic expiry
- Permission override request & approval workflow
- Complete audit trails

## Security Clearance Levels

| Level | Name | Access |
|-------|------|--------|
| 1 | GENERAL | Public information |
| 2 | RESTRICTED | Internal company documents |
| 3 | CONFIDENTIAL | Sensitive business data |
| 4 | HIGHLY_CONFIDENTIAL | Restricted information |

## Core RBAC System

### Roles

**Global Roles:**
- **Super Admin**: Full system access, manages organizations
- **Admin**: Organization-wide administration
- **Manager**: Department management, approve requests
- **User**: Standard access based on clearance level

### User Permissions

Each user has:
- **Organization Permission**: Base clearance level for all documents
- **Department Permissions**: Per-department clearance levels
- **Permission Overrides**: Temporary elevated access

**Effective Permission Calculation:**
```python
effective_permission = max(
    org_permission_level,
    department_permission_level,
    active_override_levels
)
```

### Document Access Rules

A user can access a document if:
1. Their **effective permission** ≥ document security level
2. **Department scope** allows access:
   - Organization-wide files: Accessible to all with sufficient clearance
   - Department-only files: Only accessible to department members

## Permission Overrides

### Overview

Temporary permission elevation with automatic expiry for:
- Special projects requiring elevated access
- Contractor assignments
- Emergency access scenarios
- Compliance audits
- Cross-department collaboration

### Override Types

**1. Organization-Wide Override**
- Elevates access to ALL documents
- Requires Admin approval
- Use for: organization-wide projects, audits

**2. Department-Specific Override**
- Elevates access to specific department's documents
- Requires Department Manager or Admin approval
- Use for: department projects, cross-team collaboration

### Creating Permission Overrides

**Programmatically:**
```python
from app.services.permission import get_permission_service
from datetime import datetime, timedelta

permission_service = get_permission_service()

# Create department override
override = await permission_service.create_override(
    db=db,
    user_id=42,
    override_type="department",
    department_id=3,
    override_permission_level=3,  # CONFIDENTIAL
    reason="Q4 audit project requiring confidential access",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(days=14),
    created_by_id=admin_user_id
)
```

**Via API:**
```bash
POST /api/v1/permissions/overrides
{
  "user_id": 42,
  "override_type": "department",
  "department_id": 3,
  "override_permission_level": 3,
  "reason": "Q4 audit access",
  "valid_until": "2025-12-31T23:59:59Z"
}
```

### Checking Override Status

```python
# Check if override is valid
if override.is_valid():
    print("Override is active")

# Check if expired
if override.is_expired():
    print("Override has expired")

# Days remaining
days_left = override.days_remaining()
if days_left < 0:
    print(f"Expired {abs(days_left)} days ago")
else:
    print(f"Expires in {days_left} days")
```

### Managing Overrides

**Revoke Override (Manual Deactivation):**
```python
override.revoke()  # Sets is_active=False
await db.commit()
```

**Extend Override:**
```python
new_expiry = datetime.utcnow() + timedelta(days=7)
await permission_service.extend_override(
    db=db,
    override_id=override.id,
    new_expiry=new_expiry
)
```

**List Active Overrides:**
```python
overrides = await permission_service.get_active_overrides_for_user(
    db=db,
    user_id=42
)
```

**Cleanup Expired Overrides:**
```python
# Run periodically (background job)
await permission_service.cleanup_expired_overrides(db=db)
```

## Permission Override Requests

### Workflow

When a user lacks sufficient clearance to access content, they can request temporary elevated access:

```
User → Request Elevated Access → Department Manager/Admin Reviews → Approve/Deny → Notification
```

### Approval Authority

| Request Type | Primary Approver | Fallback | Auto-Escalation |
|--------------|-----------------|----------|-----------------|
| Department (own) | Department Manager | Admin | After 24 hours |
| Department (other) | Target Dept Manager | Admin | After 24 hours |
| Organization-wide | Admin only | N/A | No escalation |

### Creating Requests

**From Chat Interface:**
When user gets "no context" due to insufficient clearance:

```python
POST /api/v1/override-requests
{
  "override_type": "department",
  "department_id": 3,
  "requested_permission_level": 3,
  "requested_duration_hours": 336,  # 14 days
  "reason": "Need access to Q4 financial docs for audit",
  "trigger_query": "What were Q4 revenues?",
  "trigger_file_id": 123
}
```

**Programmatically:**
```python
from app.services.override_request import get_override_request_service

service = get_override_request_service()

request = await service.create_request(
    db=db,
    requester_id=user_id,
    override_type="department",
    department_id=3,
    requested_permission_level=3,
    requested_duration_hours=336,
    reason="Q4 audit access needed",
    trigger_query="What were Q4 revenues?"
)
```

### Reviewing Requests

**List Pending Requests (Manager/Admin):**
```python
GET /api/v1/override-requests/pending

# Returns:
[
  {
    "id": 1,
    "requester": {"id": 42, "name": "John Doe"},
    "override_type": "department",
    "department": {"id": 3, "name": "Finance"},
    "requested_permission_level": 3,
    "requested_duration_hours": 336,
    "reason": "Q4 audit access",
    "status": "pending",
    "created_at": "2025-12-06T10:00:00Z"
  }
]
```

**Approve Request:**
```python
POST /api/v1/override-requests/{request_id}/approve
{
  "approval_notes": "Approved for Q4 audit",
  "custom_duration_hours": 240  # Optional: override requested duration
}
```

**Deny Request:**
```python
POST /api/v1/override-requests/{request_id}/deny
{
  "approval_notes": "Insufficient justification"
}
```

### Auto-Escalation

If a Department Manager doesn't respond within 24 hours:
- Request automatically escalates to Admins
- `auto_escalated` flag set to `true`
- Admins receive notification
- Original manager can still approve

**Check for Auto-Escalation:**
```python
# Background job runs hourly
await service.auto_escalate_stale_requests(db=db)
```

### Notifications

Users receive notifications for:
- Request status changes (approved/denied)
- Override expiry warnings (3 days, 1 day before)
- Auto-escalation events

## Access Control in Code

### Check File Access

```python
from app.services.permission import get_permission_service

permission_service = get_permission_service()

# Check if user can access file
can_access = await permission_service.can_user_access_file(
    db=db,
    user_id=user_id,
    file_security_level=3,  # CONFIDENTIAL
    file_department_id=department_id,
    file_is_department_only=True
)

if not can_access:
    raise PermissionDeniedError("Insufficient clearance")
```

### Get User Permission Summary

```python
summary = await permission_service.get_user_permission_summary(
    db=db,
    user_id=user_id
)

# Returns:
{
  "org_permission_level": 2,
  "department_permissions": [
    {"department_id": 1, "permission_level": 2},
    {"department_id": 3, "permission_level": 3}
  ],
  "active_overrides": [
    {
      "override_type": "department",
      "department_id": 3,
      "permission_level": 3,
      "valid_until": "2025-12-20T00:00:00Z",
      "days_remaining": 14
    }
  ],
  "effective_permissions": {
    "org_wide": 2,
    "departments": {
      "1": 2,
      "3": 3  # Elevated by override
    }
  }
}
```

## Database Schema

### PermissionOverride Table

| Field | Type | Purpose |
|-------|------|---------|
| id | INT | Primary key |
| user_id | INT | User receiving override |
| override_type | ENUM | 'org_wide' or 'department' |
| department_id | INT | Department for DEPARTMENT overrides |
| override_permission_level | INT | Elevated permission (1-4) |
| reason | TEXT | Justification for override |
| valid_from | DATETIME | Start of validity |
| valid_until | DATETIME | End of validity |
| created_by_id | INT | User who granted override |
| is_active | BOOL | Manual revocation flag |

**Indexes:**
- `(user_id, is_active)` - Fast active override lookups
- `(valid_until, is_active)` - Fast expiry queries
- `(user_id, override_type)` - Type-filtered queries

### PermissionOverrideRequest Table

| Field | Type | Purpose |
|-------|------|---------|
| id | INT | Primary key |
| requester_id | INT | User requesting override |
| override_type | ENUM | 'org_wide' or 'department' |
| department_id | INT | Target department |
| requested_permission_level | INT | Requested level (1-4) |
| requested_duration_hours | INT | Requested duration |
| reason | TEXT | Justification |
| trigger_query | TEXT | Query that triggered request |
| trigger_file_id | INT | File that couldn't be accessed |
| status | ENUM | pending/approved/denied/expired/cancelled |
| approver_id | INT | Who approved/denied |
| approval_notes | TEXT | Approver's comments |
| approved_at | DATETIME | When approved/denied |
| auto_escalated | BOOL | Auto-escalated to admins |
| escalated_at | DATETIME | When escalated |

**Indexes:**
- `(status, requester_id)` - User's request history
- `(status, override_type)` - Pending requests by type
- `(status, department_id)` - Department pending requests

## Best Practices

### Override Duration

- **Short-term projects**: 7-14 days
- **Medium-term projects**: 1-3 months
- **Audits/Reviews**: 2-4 weeks
- **Emergency access**: 24-48 hours

### Security Considerations

1. **Always provide clear justification** - Required for audit trail
2. **Use minimum required level** - Don't over-elevate permissions
3. **Set appropriate expiry** - Avoid indefinite access
4. **Review active overrides** - Periodic audit of elevated access
5. **Revoke when no longer needed** - Don't wait for expiry

### Monitoring

**Track expiring overrides:**
```python
expiring = await permission_service.get_expiring_soon_overrides(
    db=db,
    days_threshold=3
)
```

**Audit override history:**
```python
history = await permission_service.audit_override_history(
    db=db,
    user_id=user_id
)
```

## Troubleshooting

### User Can't Access Document

**Check effective permission:**
```python
summary = await permission_service.get_user_permission_summary(db, user_id)
effective_level = summary["effective_permissions"]["org_wide"]
```

**Check active overrides:**
```python
overrides = await permission_service.get_active_overrides_for_user(db, user_id)
```

### Override Not Working

**Verify override is active:**
```python
if not override.is_valid():
    print(f"Override inactive: expired={override.is_expired()}, active={override.is_active}")
```

**Check time window:**
```python
now = datetime.utcnow()
if now < override.valid_from:
    print("Override not started yet")
elif now > override.valid_until:
    print("Override expired")
```

## API Reference

### Endpoints

```
POST   /api/v1/permissions/overrides           # Create override
GET    /api/v1/permissions/overrides/{id}      # Get override
DELETE /api/v1/permissions/overrides/{id}      # Revoke override
PATCH  /api/v1/permissions/overrides/{id}      # Extend override
GET    /api/v1/permissions/users/{id}/summary  # Permission summary

POST   /api/v1/override-requests                # Create request
GET    /api/v1/override-requests/pending        # List pending
POST   /api/v1/override-requests/{id}/approve   # Approve request
POST   /api/v1/override-requests/{id}/deny      # Deny request
GET    /api/v1/override-requests/my-requests    # User's requests
```

## See Also

- [RBAC System](../../docs/ROLE_BASED_ACCESS_CONTROL.md) - Core RBAC architecture
- [File Upload Architecture](FILE_UPLOAD_ARCHITECTURE.md) - Document security levels
- [Email System](EMAIL_SYSTEM.md) - Notification system
