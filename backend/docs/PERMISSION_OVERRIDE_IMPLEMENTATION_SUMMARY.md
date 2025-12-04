# Permission Override Request System - Implementation Summary

## Overview
Implemented a complete permission override request and approval workflow system that allows users to request temporary elevated clearance when they encounter documents they cannot access due to insufficient permissions.

## Backend Implementation

### 1. Database Model Extension
**File:** `backend/app/models/permission_override.py`

Extended the existing `PermissionOverride` model with approval workflow fields:
- `status`: PENDING → APPROVED/DENIED/EXPIRED/REVOKED
- `approver_id`: User who approved/denied the request
- `approval_notes`: Approver's comments
- `decided_at`: Timestamp of decision
- `trigger_query`: Query that triggered the request
- `trigger_file_id`: File that couldn't be accessed
- `auto_escalated`: Whether request was escalated to admins
- `escalated_at`: Escalation timestamp

Added workflow helper methods:
- `is_pending()`, `is_approved()`, `is_denied()`
- `can_be_cancelled()`, `should_auto_escalate()`
- `hours_since_created()`

### 2. Request Service
**File:** `backend/app/services/override_request_service.py`

Implements complete request lifecycle:
- `create_request()`: Create new request with status=PENDING
- `approve_request()`: Approve and activate override
- `deny_request()`: Deny with reason
- `cancel_request()`: Cancel pending request (by requester)
- `get_pending_requests_for_approver()`: Filter by admin/manager authority
- `get_user_requests()`: User's own requests with status filtering
- `process_auto_escalations()`: Auto-escalate dept requests > 24h old

Approval Authority Matrix:
- **Department requests**: Department manager approves (or admin if escalated)
- **Org-wide requests**: Admin only
- **Auto-escalation**: Dept requests pending > 24h escalate to admins

### 3. API Routes
**File:** `backend/app/routes/override_requests.py`

Endpoints:
- `POST /api/v1/override-requests` - Create new request
- `GET /api/v1/override-requests/pending` - Get pending requests for approver
- `GET /api/v1/override-requests/my-requests` - Get user's requests
- `POST /api/v1/override-requests/{id}/approve` - Approve request
- `POST /api/v1/override-requests/{id}/deny` - Deny request
- `DELETE /api/v1/override-requests/{id}` - Cancel pending request

### 4. Request Schemas
**File:** `backend/app/schemas/override_request.py`

Pydantic models for validation:
- `OverrideRequestCreate`: Request submission with validation
- `OverrideApprovalRequest`: Approval with optional notes
- `OverrideDenialRequest`: Denial with required reason
- `OverrideRequestResponse`: Complete request details
- `OverrideRequestListResponse`: List of requests

### 5. Notification Integration
**File:** `backend/app/services/notification_service.py` (already extended)

Database notifications for:
- Request submitted → dept manager/admins
- Request approved → requester
- Request denied → requester with reason
- Request escalated → admins

### 6. User Clearance Cache Integration
**File:** `backend/app/utils/user_clearance_cache.py`

Already integrated! The `_get_effective_security_level()` method:
- Retrieves active overrides via `user.get_active_overrides()`
- Returns highest level from: org permission, dept permission, active overrides
- Cache invalidated on approval to immediately reflect new permissions

### 7. Scheduled Job for Auto-Escalation
**File:** `backend/app/core/startup.py`

Hourly job scheduled on application startup:
- Runs `process_auto_escalations(24)` every hour
- Finds dept requests pending > 24 hours
- Sets `auto_escalated=True` and notifies admins
- Uses JobManager with APScheduler

### 8. Database Migration
**File:** `backend/migrations/versions/dbc6269d79ba_add_approval_workflow_to_permission_.py`

Generated migration adds:
- 8 new columns to `permission_overrides` table
- 3 new indexes for efficient queries
- Foreign key constraint for `approver_id`

To apply: `alembic upgrade head`

## Frontend Implementation

### 1. Admin Store Extension
**File:** `frontend/src/stores/admin.js`

Added API methods:
- `createOverrideRequest(requestData)`
- `fetchPendingOverrideRequests(limit, offset)`
- `fetchMyOverrideRequests(statusFilter, limit, offset)`
- `approveOverrideRequest(requestId, approvalNotes)`
- `denyOverrideRequest(requestId, denialReason)`
- `cancelOverrideRequest(requestId)`

### 2. Request Access Modal
**File:** `frontend/src/components/admin/RequestAccessModal.vue`

User-facing modal for requesting elevated access:

**Features:**
- Shows current clearance levels (org + dept)
- Request type selection (department vs org-wide)
- Clearance level selector (1-4)
- Duration selector (1 hour - 1 week max)
- Business justification textarea (min 20 chars)
- Context display (trigger query/file if provided)
- Approval message (who will review)
- Real-time validation

**Usage:**
```vue
<RequestAccessModal
  v-if="showModal"
  :trigger-query="userQuery"
  :trigger-file-id="fileId"
  :trigger-file-name="fileName"
  :suggested-level="suggestedLevel"
  @close="showModal = false"
  @success="handleRequestSuccess"
/>
```

### 3. Pending Approvals View
**File:** `frontend/src/views/admin/PendingApprovals.vue`

Admin/manager dashboard for reviewing requests:

**Features:**
- Lists all pending requests (filtered by authority)
- Shows requester info, level, duration, reason
- Displays context (query/file that triggered request)
- Escalation badge for auto-escalated requests
- Approve button with optional notes modal
- Deny button with required reason modal
- Real-time request removal on action
- Auto-refresh capability

**Access:** Requires `admin` or `department_manager` role

### 4. My Requests View
**File:** `frontend/src/views/users/MyRequests.vue`

User's personal request history:

**Features:**
- Filter by status (all/pending/approved/denied)
- Status badges with color coding
- Shows approval/denial details and notes
- Expiry countdown for active overrides
- Cancel button for pending requests
- Escalation notices
- Request context display

**Statuses:**
- **Pending** (yellow): Awaiting review
- **Approved** (green): Active or future override
- **Denied** (red): Request denied with reason
- **Expired** (gray): Override has expired
- **Revoked** (gray): Manually revoked

## Integration Points

### 1. Retrieval Service (Already Works!)
The user clearance cache automatically integrates approved overrides:
1. User queries knowledge base
2. `user_clearance_cache.get_clearance()` called
3. `_get_effective_security_level()` includes active overrides
4. Retrieval service uses effective level for filtering
5. If insufficient: User can click "Request Access" (trigger modal)

### 2. File Access Control
Same pattern - retrieval service checks effective clearance which includes overrides.

### 3. Cache Invalidation
On approval, the route handler:
```python
await cache_util.invalidate(override_request.user_id)
```
Ensures user immediately gets new permissions on next request.

## Usage Flow

### User Requests Access
1. User encounters "no results" due to low clearance
2. Frontend shows `RequestAccessModal` with context
3. User fills reason, duration, selects level
4. `POST /api/v1/override-requests` creates request with `status=PENDING`
5. Notification sent to dept manager or admin

### Manager/Admin Approves
1. Manager navigates to **Pending Approvals** view
2. Sees request with full context and justification
3. Clicks "Approve" → confirmation modal with optional notes
4. `POST /api/v1/override-requests/{id}/approve`
5. Override activated: `status=APPROVED`, `is_active=True`
6. User's cache invalidated
7. Notification sent to requester

### Auto-Escalation (if no response)
1. Hourly job checks pending dept requests
2. If > 24 hours old: `auto_escalated=True`
3. Admins notified
4. Admins can now see and approve the request

### User Checks Status
1. User navigates to **My Requests**
2. Sees request status, approval notes, expiry
3. Active overrides show countdown
4. Can cancel pending requests

## Configuration

### Escalation Threshold
Default: 24 hours (configured in `startup.py`)
```python
await service.process_auto_escalations(
    escalation_threshold_hours=24  # Adjust as needed
)
```

### Max Duration
Default: 168 hours (1 week) - enforced in validation
Change in `backend/app/schemas/override_request.py`:
```python
requested_duration_hours: int = Field(..., ge=1, le=168)
```

### Job Frequency
Default: Hourly (3600 seconds)
Change in `backend/app/core/startup.py`:
```python
self.job_manager.add_recurring_job(
    escalate_overrides,
    interval_seconds=3600,  # Adjust as needed
    ...
)
```

## Router Setup

Already registered in `backend/app/main.py`:
```python
from app.routes.override_requests import router as override_requests_router
app.include_router(override_requests_router)
```

## Testing

### Backend Tests (Recommended)
```python
# test_override_request_service.py
async def test_create_request()
async def test_approve_request()
async def test_deny_request()
async def test_cancel_request()
async def test_approval_authority()
async def test_auto_escalation()
```

### Frontend Tests
1. Request submission with various durations
2. Approval/denial flow
3. Auto-escalation display
4. Status filtering
5. Cache invalidation verification

## Documentation

Comprehensive documentation created:
- **File:** `backend/docs/PERMISSION_OVERRIDE_REQUEST_SYSTEM.md`
- Covers: Architecture, flows, API examples, testing scenarios

## Deployment Checklist

- [x] Database migration generated
- [ ] Run migration: `alembic upgrade head`
- [ ] Restart application (to start scheduled job)
- [ ] Verify job scheduled: Check logs for "Override request escalation job scheduled"
- [ ] Test request creation from frontend
- [ ] Test approval flow
- [ ] Wait 24+ hours and verify auto-escalation (or adjust threshold for testing)

## Notes

1. **No Frontend Routing Required**: Views can be integrated into existing admin dashboard and user profile sections
2. **Notification System**: Uses existing database notifications (no email templates needed)
3. **Permissions**: Uses existing `require_admin_or_department_manager` dependency
4. **Cache**: Automatically integrates with existing clearance cache system
5. **Jobs**: Uses existing APScheduler job manager (no new infrastructure needed)

## Future Enhancements

1. **Audit Log**: Track all approval/denial decisions
2. **Request Templates**: Common request reasons for faster submission
3. **Bulk Approval**: Approve multiple requests at once
4. **Request Analytics**: Dashboard showing request patterns
5. **Email Notifications**: In addition to database notifications
6. **Scheduled Overrides**: Request access for future date/time
7. **Recurring Overrides**: For regular elevated access needs
