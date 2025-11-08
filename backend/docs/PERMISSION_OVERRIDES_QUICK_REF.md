# Permission Overrides - Quick Reference

## Model: PermissionOverride

### Basic Usage
```python
from app.models.permission_override import PermissionOverride, OverrideType
from datetime import datetime, timedelta

# Create override
override = PermissionOverride(
    user_id=42,
    override_type=OverrideType.DEPARTMENT,
    department_id=3,
    override_permission_level=3,  # PermissionLevel.MANAGER
    reason="Special project access",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(days=14),
    created_by_id=1,
    is_active=True
)
db.add(override)
await db.commit()
```

### Check Override Status
```python
# Is override currently valid?
if override.is_valid():
    print("Override is active and within time window")

# Has override expired?
if override.is_expired():
    print("Override has passed its expiry date")

# How many days until expiry?
days = override.days_remaining()
if days < 0:
    print(f"Expired {abs(days)} days ago")
else:
    print(f"Expires in {days} days")

# Manually revoke override
override.revoke()  # Sets is_active=False
await db.commit()
```

## Service: PermissionService

### Create Override
```python
from app.services.permission_service import permission_service
from datetime import datetime, timedelta

# Org-wide override
override = await permission_service.create_override(
    user_id=42,
    override_type="org_wide",
    override_permission_level=4,  # EXECUTIVE
    reason="Emergency incident response",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(hours=4),
    created_by_id=1,
    db=session
)

# Department-specific override
override = await permission_service.create_override(
    user_id=42,
    override_type="department",
    department_id=2,
    override_permission_level=3,  # MANAGER
    reason="Q4 audit - 2 weeks",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(days=14),
    created_by_id=1,
    db=session
)
```

### Revoke Override
```python
# Immediately disable override before expiry
override = await permission_service.revoke_override(
    override_id=42,
    db=session
)
```

### Check File Access
```python
# Does user have access to this file?
can_access = await permission_service.can_user_access_file(
    user_id=42,
    file_id=1,
    db=session
)

if can_access:
    # Serve file
else:
    raise PermissionDenied()
```

### Get Active Overrides
```python
# All active overrides for user
overrides = await permission_service.get_active_overrides_for_user(
    user_id=42,
    db=session
)

# Only org-wide overrides
org_overrides = await permission_service.get_active_overrides_for_user(
    user_id=42,
    override_type="org_wide",
    db=session
)

# Only department overrides
dept_overrides = await permission_service.get_active_overrides_for_user(
    user_id=42,
    override_type="department",
    db=session
)
```

### Get Permission Summary
```python
summary = await permission_service.get_user_permission_summary(
    user_id=42,
    db=session
)

print(f"Org level: {summary['org_level_permission']}")           # 2
print(f"Dept level: {summary['department_level_permission']}")   # 3
print(f"Effective: {summary['effective_permission']}")           # 4 (due to override)
print(f"Active overrides: {len(summary['active_overrides'])}")   # 1
```

### Manage Override Lifecycle
```python
# Extend override before expiry
extended = await permission_service.extend_override(
    override_id=42,
    new_valid_until=datetime.utcnow() + timedelta(days=7),
    db=session
)

# Get overrides expiring within 3 days
expiring = await permission_service.get_expiring_soon_overrides(
    days_until_expiry=3,
    db=session
)
for override in expiring:
    print(f"User {override.user_id} expires in {override.days_remaining()} days")

# Cleanup expired overrides (mark as inactive)
count = await permission_service.cleanup_expired_overrides(db=session)
print(f"Marked {count} overrides as expired")
```

### Audit Trail
```python
# Get all overrides (active and revoked) for user
history = await permission_service.audit_override_history(
    user_id=42,
    db=session,
    limit=100
)

for override in history:
    status = "ACTIVE" if override.is_active else "REVOKED"
    print(f"{override.created_at} - {override.reason} ({status})")
    print(f"  Granted by: {override.created_by.username}")
    print(f"  Valid: {override.valid_from} -> {override.valid_until}")
```

## UserPermission Integration

### Get Effective Permission (with overrides)
```python
# Effective permission now includes active overrides
user = await db.get(User, 42)
effective = user.permission.get_effective_permission()

# Effective = max(org_level, dept_level, all_active_overrides)
```

### Check Active Overrides
```python
# Get all active, non-expired overrides
active = user.permission.get_active_overrides()
for override in active:
    print(f"Override: {override.reason}")

# Check if specific override type exists
has_org_override = user.permission.has_active_override(
    override_type="org_wide"
)

has_dept_override = user.permission.has_active_override(
    override_type="department",
    department_id=3
)
```

## Common Patterns

### Grant Temporary Access
```python
# User needs access for specific duration
override = await permission_service.create_override(
    user_id=user_id,
    override_type="org_wide",
    override_permission_level=PermissionLevel.CONFIDENTIAL,
    reason="Business reason here",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(days=7),
    created_by_id=admin_id,
    db=session
)
await session.commit()
```

### Emergency Revocation
```python
# User no longer needs access
override = await permission_service.revoke_override(
    override_id=override_id,
    db=session
)
await session.commit()
```

### Check File Access
```python
# Part of file serving/download endpoint
can_access = await permission_service.can_user_access_file(
    user_id=request.user.id,
    file_id=file_id,
    db=session
)

if not can_access:
    raise HTTPException(status_code=403, detail="Insufficient permissions")

# Serve file...
```

### Scheduled Cleanup Job
```python
# Run daily to clean up expired overrides
# Can be part of background task scheduler

async def cleanup_job(session: AsyncSession):
    count = await permission_service.cleanup_expired_overrides(db=session)
    logger.info(f"Cleaned up {count} expired permission overrides")
    await session.commit()
```

### Expiry Notifications
```python
# Run daily to notify users of expiring overrides
async def notify_expiring_overrides():
    expiring = await permission_service.get_expiring_soon_overrides(
        days_until_expiry=3,
        db=session
    )
    
    for override in expiring:
        email_body = f"""
Your temporary access ({override.reason}) will expire in {override.days_remaining()} days.
Valid until: {override.valid_until}

If you need extended access, please contact your manager.
"""
        await send_email(override.user.email, "Access Expiring Soon", email_body)
```

## OverrideType Values

```python
"org_wide"      # Override applies to organization-wide permission
"department"    # Override applies to department-specific permission
```

## Database Indexes

Efficient queries are supported by these indexes:
- `(user_id, is_active)` - Fast lookup of active overrides per user
- `(valid_until, is_active)` - Fast expiry queries
- `(user_id, override_type)` - Fast type-filtered queries
- `(department_id, override_type)` - Fast department queries

## Examples

### Example 1: Q4 Audit Access
```python
# Employee needs elevated access for 2-week audit
override = await permission_service.create_override(
    user_id=42,
    override_type="org_wide",
    override_permission_level=PermissionLevel.CONFIDENTIAL,
    reason="Q4 audit - 2 week project",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(days=14),
    created_by_id=admin_id,
    db=session
)

# After 14 days, override automatically expires
# User reverts to normal permission level
```

### Example 2: Contractor Access
```python
# Contractor needs limited department access for 30 days
override = await permission_service.create_override(
    user_id=contractor_id,
    override_type="department",
    department_id=2,  # Sales department
    override_permission_level=PermissionLevel.CONFIDENTIAL,
    reason="Contract work - sales forecasting model",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(days=30),
    created_by_id=admin_id,
    db=session
)

# Contractor can access Sales CONFIDENTIAL files
# But not other departments or RESTRICTED files
```

### Example 3: Emergency Access
```python
# IT needs emergency access for incident response (4 hours)
override = await permission_service.create_override(
    user_id=ops_user_id,
    override_type="org_wide",
    override_permission_level=PermissionLevel.EXECUTIVE,
    reason="Production incident - database corruption",
    valid_from=datetime.utcnow(),
    valid_until=datetime.utcnow() + timedelta(hours=4),
    created_by_id=cto_id,
    db=session
)

# After incident resolved, can manually revoke:
await permission_service.revoke_override(override_id=override.id, db=session)
```

## PermissionLevel Values

```python
PermissionLevel.NONE = 0           # No access
PermissionLevel.PUBLIC = 1         # Public data
PermissionLevel.EMPLOYEE = 2       # Standard employee
PermissionLevel.MANAGER = 3        # Manager/team lead
PermissionLevel.EXECUTIVE = 4      # Executive
PermissionLevel.ADMIN = 5          # Full system access
```

## Troubleshooting

### Override not working
- Check if override.is_valid() returns True
- Verify override_permission_level >= required_level
- Ensure user.permission.is_active = True
- Check if current time is between valid_from and valid_until

### User still has access after revoke
- Ensure is_active was set to False
- Run cleanup_expired_overrides if override was legitimately expired
- Check get_effective_permission() calculation

### Missing expired overrides from queries
- Run cleanup_expired_overrides to mark them inactive
- Only use get_active_overrides() to filter by active/valid status
- Use audit_override_history() for complete history
