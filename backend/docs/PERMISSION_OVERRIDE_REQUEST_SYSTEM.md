# Permission Override Request & Approval System

**Implementation Date:** December 4, 2025  
**Status:** ✅ Complete - Ready for Integration

## Overview

This system handles the complete workflow for users requesting temporary elevated permissions when they don't have sufficient clearance to access content. It includes request submission, hierarchical approval routing, auto-escalation, and notifications.

## Problem Solved

**Scenario:** User queries knowledge base but gets "no context" due to insufficient clearance.

**Solution:** User can request temporary elevated access with business justification. Request is routed to appropriate approver (Department Manager or Admin), who can approve/deny. Requester receives notification of decision.

## Approval Authority Matrix

| Request Type | Primary Approver | Fallback | Auto-Escalation |
|--------------|-----------------|----------|-----------------|
| **Department-level** (own dept) | Department Manager | Admin | After 24 hours |
| **Org-wide** | Admin only | N/A | No escalation |
| **Cross-department** | Target Dept Manager | Admin | After 24 hours |

### Key Design Decisions

1. **Department Managers first** - They know their team's needs best
2. **Admins for org-wide** - Organization-wide access needs higher authority
3. **Auto-escalation** - If manager doesn't respond in 24h, escalates to admins
4. **Audit trail** - Full history of who requested, why, who approved/denied

## Architecture

### Core Components

#### 1. PermissionOverrideRequest Model (`backend/app/models/permission_override_request.py`)

**Purpose:** Tracks permission override requests through their lifecycle.

**Key Fields:**
- `requester_id`: User requesting override
- `override_type`: 'org_wide' or 'department'
- `department_id`: For department requests
- `requested_permission_level`: 1-4 (GENERAL to HIGHLY_CONFIDENTIAL)
- `requested_duration_hours`: How long access needed
- `reason`: Business justification
- `trigger_query`: Query that triggered the request (optional)
- `trigger_file_id`: File that couldn't be accessed (optional)
- `status`: pending/approved/denied/expired/cancelled
- `approver_id`: Who approved/denied
- `approval_notes`: Approver's comments
- `auto_escalated`: Whether escalated to admin
- `override_id`: Created PermissionOverride (after approval)

**Status Flow:**
```
PENDING → APPROVED → (PermissionOverride created)
        ↓
        DENIED
        ↓
        CANCELLED (by requester)
        ↓
        EXPIRED (no decision within time limit)
```

#### 2. OverrideRequestService (`backend/app/services/override_request_service.py`)

**Purpose:** Business logic for request/approval workflow.

**Key Methods:**

```python
# Create new request
async def create_request(
    requester_id, override_type, requested_permission_level,
    reason, requested_duration_hours, department_id=None
) -> Tuple[PermissionOverrideRequest, error]

# Approve request (creates PermissionOverride)
async def approve_request(
    request_id, approver_id, approval_notes=None
) -> Tuple[PermissionOverride, error]

# Deny request
async def deny_request(
    request_id, approver_id, denial_reason
) -> Tuple[bool, error]

# Cancel request (by requester)
async def cancel_request(
    request_id, requester_id
) -> Tuple[bool, error]

# Get pending requests for approver
async def get_pending_requests_for_approver(
    approver_id, limit=50, offset=0
) -> List[PermissionOverrideRequest]

# Get user's own requests
async def get_user_requests(
    user_id, status=None, limit=50, offset=0
) -> List[PermissionOverrideRequest]

# Auto-escalate old pending requests
async def process_auto_escalations(
    escalation_threshold_hours=24
) -> int
```

#### 3. NotificationService Extensions

**Added Methods:**
- `notify_override_request_submitted()` - Notify approver of new request
- `notify_admins_new_override_request()` - Notify all admins (org-wide requests)
- `notify_admins_override_escalation()` - Notify admins of escalated request
- `notify_override_request_approved()` - Notify requester of approval
- `notify_override_request_denied()` - Notify requester of denial

## User Flows

### 1. User Requests Override (Department-Level)

**Trigger:** User gets "no context" during query due to insufficient clearance.

**Steps:**
1. User clicks "Request Access" button
2. Modal shows:
   - Current clearance level
   - Requested clearance level (dropdown)
   - Duration (hours/days)
   - Reason (required text area)
3. User submits request
4. System:
   - Validates user doesn't already have this level
   - Creates PermissionOverrideRequest with status=PENDING
   - Determines approver (Department Manager for dept requests)
   - Sends notification to approver
5. User sees confirmation: "Request submitted to [Manager Name]"

### 2. Department Manager Approves Request

**Trigger:** Manager receives notification about pending request.

**Steps:**
1. Manager navigates to "Pending Approvals" section
2. Sees list of pending requests with:
   - Requester name
   - Requested level
   - Duration
   - Reason
   - Context (query/file that triggered it)
3. Manager clicks request to view details
4. Manager reviews and clicks "Approve" or "Deny"
5. If approving:
   - Optional approval notes
   - Confirms approval
6. System:
   - Creates PermissionOverride with specified dates
   - Updates request status to APPROVED
   - Links override_id to request
   - Sends notification to requester
7. Requester receives notification: "Your request was APPROVED! You now have CONFIDENTIAL department access until 2025-12-10."

### 3. Auto-Escalation (Manager Doesn't Respond)

**Trigger:** Scheduled job runs hourly, finds pending department requests > 24 hours old.

**Steps:**
1. Job identifies stale requests:
   - Status = PENDING
   - Created > 24 hours ago
   - Not already escalated
2. For each request:
   - Sets `auto_escalated = True`
   - Sets `escalated_at = now()`
   - Notifies all admins
3. Admins receive notification: "ESCALATED: Permission request from [User] requires admin review"
4. Admin can now approve/deny the request

### 4. Admin Approves Org-Wide Request

**Trigger:** User requests org-wide clearance (goes directly to admins).

**Steps:**
1. User submits org-wide request
2. All admins receive notification
3. Any admin can approve/deny
4. Same approval flow as department manager
5. Creates PermissionOverride with `override_type=org_wide`

### 5. Request Denied

**Steps:**
1. Approver clicks "Deny"
2. Enters denial reason (required)
3. Confirms denial
4. System:
   - Updates request status to DENIED
   - Records denial reason in approval_notes
   - Sends notification to requester
5. Requester receives notification: "Your request was DENIED. Reason: [reason]"

### 6. User Cancels Request

**Steps:**
1. User navigates to "My Requests"
2. Sees pending request
3. Clicks "Cancel"
4. Request status changes to CANCELLED
5. No notifications sent

## API Integration

### Frontend → Backend Flow

**When user gets "no context" during query:**

```javascript
// 1. User clicks "Request Access" in no-context message
showRequestAccessModal({
  currentOrgLevel: 2,  // User's current level
  currentDeptLevel: 2,
  suggestedLevel: 3,   // Based on available docs
  triggerQuery: "Q4 financial reports",
  triggerFileId: 123
})

// 2. User fills form and submits
const response = await api.post('/v1/override-requests', {
  override_type: 'department',
  department_id: user.department_id,
  requested_permission_level: 3,
  reason: "Need to complete Q4 audit report",
  requested_duration_hours: 48,
  trigger_query: "Q4 financial reports",
  trigger_file_id: 123
})

// 3. Show confirmation
showNotification('success', 'Request submitted to your department manager')
```

**Manager viewing pending requests:**

```javascript
// Get pending requests
const { requests } = await api.get('/v1/override-requests/pending')

// Show in dashboard
requests.forEach(request => {
  displayRequest({
    id: request.id,
    requester: request.requester.full_name,
    level: request.requested_permission_level,
    duration: request.requested_duration_hours,
    reason: request.reason,
    created_at: request.created_at
  })
})

// Approve request
await api.post(`/v1/override-requests/${requestId}/approve`, {
  approval_notes: "Approved for audit project"
})

// Deny request
await api.post(`/v1/override-requests/${requestId}/deny`, {
  denial_reason: "Insufficient justification"
})
```

## Database Schema

### permission_override_requests Table

```sql
CREATE TABLE permission_override_requests (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    override_type VARCHAR(20) NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    requested_permission_level INTEGER NOT NULL,
    reason TEXT NOT NULL,
    requested_duration_hours INTEGER NOT NULL,
    trigger_query TEXT,
    trigger_file_id INTEGER REFERENCES files(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approver_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approval_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    decided_at TIMESTAMP,
    auto_escalated BOOLEAN NOT NULL DEFAULT FALSE,
    escalated_at TIMESTAMP,
    override_id INTEGER REFERENCES permission_overrides(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX ix_override_requests_status_created ON permission_override_requests(status, created_at);
CREATE INDEX ix_override_requests_requester_status ON permission_override_requests(requester_id, status);
CREATE INDEX ix_override_requests_dept_status ON permission_override_requests(department_id, status);
CREATE INDEX ix_override_requests_requester ON permission_override_requests(requester_id);
CREATE INDEX ix_override_requests_dept ON permission_override_requests(department_id);
CREATE INDEX ix_override_requests_status ON permission_override_requests(status);
```

## Scheduled Jobs

### Auto-Escalation Job

**Purpose:** Escalate stale department requests to admins.

**Schedule:** Every hour

**Implementation:**
```python
# In jobs/scheduled_tasks.py or similar
@scheduler.scheduled_job('interval', hours=1)
async def escalate_pending_override_requests():
    async with get_db_session() as session:
        service = OverrideRequestService(session)
        count = await service.process_auto_escalations(
            escalation_threshold_hours=24
        )
        await session.commit()
        logger.info(f"Escalated {count} override requests")
```

## Configuration

### Settings (`backend/app/config/app_settings.py`)

```python
# Permission Override Settings
OVERRIDE_REQUEST_AUTO_ESCALATION_HOURS: int = 24
OVERRIDE_REQUEST_MAX_DURATION_HOURS: int = 168  # 1 week
OVERRIDE_REQUEST_DEFAULT_DURATION_HOURS: int = 48
```

## Validation Rules

### Request Creation

1. **User doesn't already have requested level:**
   - Check current org/dept permissions
   - Reject if current >= requested

2. **Duration is reasonable:**
   - Must be > 0
   - Max: 168 hours (1 week) by default

3. **Department request validation:**
   - Must provide department_id
   - User must belong to a department

4. **Permission level validation:**
   - Must be 1-4
   - Should be higher than current level

### Approval Authority

1. **Department requests:**
   - Department Manager of target dept
   - OR any Admin

2. **Org-wide requests:**
   - Only Admins

3. **Auto-escalation:**
   - After 24 hours, escalates to Admins
   - Only for department requests

## Notifications

### Notification Types

| Type | Recipients | Trigger |
|------|-----------|---------|
| `override_request_submitted` | Department Manager | New dept request |
| `override_request_admin` | All Admins | New org-wide request |
| `override_request_escalated` | All Admins | Auto-escalation |
| `override_request_approved` | Requester | Request approved |
| `override_request_denied` | Requester | Request denied |

### Notification Messages

**New Request (to Manager):**
```
New permission override request from John Doe: CONFIDENTIAL department 
access for 2 days. Reason: Need to complete Q4 audit report...
```

**New Org-Wide Request (to Admins):**
```
New ORG-WIDE permission request from Jane Smith: HIGHLY_CONFIDENTIAL 
access for 3 days. Reason: Emergency security incident response...
```

**Escalated (to Admins):**
```
ESCALATED: Permission request from John Doe requires admin review 
(CONFIDENTIAL for 2 days). Department manager did not respond within 24 hours.
```

**Approved (to Requester):**
```
Your permission override request was APPROVED! You now have CONFIDENTIAL 
department access until 2025-12-10 15:30 UTC.
```

**Denied (to Requester):**
```
Your permission override request was DENIED. Requested: CONFIDENTIAL 
department access. Reason: Insufficient business justification provided.
```

## Frontend Components Needed

### 1. RequestAccessModal

**Triggered by:** "No context" retrieval result

**Props:**
- `currentOrgLevel`: User's current org clearance
- `currentDeptLevel`: User's current dept clearance
- `suggestedLevel`: System suggestion based on available docs
- `triggerQuery`: Query that triggered this
- `triggerFileId`: File that couldn't be accessed (optional)

**Fields:**
- Override type: Radio (Department / Organization-wide)
- Requested level: Dropdown (filtered to levels > current)
- Duration: Input with unit selector (hours/days)
- Reason: Textarea (required, min 20 chars)

**Actions:**
- Submit → POST /v1/override-requests
- Cancel → Close modal

### 2. PendingApprovalsSection

**Location:** Admin/Manager dashboard

**Shows:**
- List of pending requests
- Request details (requester, level, duration, reason)
- Context (query/file that triggered it)
- Time since requested
- Escalation indicator

**Actions:**
- View details
- Approve (with optional notes)
- Deny (with required reason)

### 3. MyRequestsSection

**Location:** User profile/dashboard

**Shows:**
- User's override requests
- Status indicator
- Approver (if decided)
- Decision notes
- Created/decided timestamps

**Actions:**
- View details
- Cancel (if pending)

## Testing Scenarios

### Backend Tests

- [ ] User can create department override request
- [ ] User can create org-wide override request
- [ ] System prevents request if user already has level
- [ ] Department manager can approve dept request
- [ ] Admin can approve any request
- [ ] Regular user cannot approve requests
- [ ] Manager cannot approve org-wide requests
- [ ] Auto-escalation triggers after 24 hours
- [ ] Approval creates PermissionOverride
- [ ] Denial doesn't create override
- [ ] Requester receives approval notification
- [ ] Requester receives denial notification
- [ ] Approver receives new request notification
- [ ] Admins receive escalation notification

### Integration Tests

- [ ] End-to-end: Request → Approval → Override active
- [ ] End-to-end: Request → Denial → No override
- [ ] End-to-end: Request → Auto-escalate → Admin approval
- [ ] User can cancel pending request
- [ ] User cannot cancel approved/denied request
- [ ] Override expires correctly after duration
- [ ] Multiple simultaneous requests handled correctly

## Migration Required

```bash
cd backend
alembic revision --autogenerate -m "Add permission override request workflow"
alembic upgrade head
```

## Files Created/Modified

### Created
- ✅ `backend/app/models/permission_override_request.py` - Request model
- ✅ `backend/app/services/override_request_service.py` - Request service
- ✅ `backend/docs/PERMISSION_OVERRIDE_REQUEST_SYSTEM.md` - This doc

### Modified
- ✅ `backend/app/models/user.py` - Added override_requests relationship
- ✅ `backend/app/services/notification_service.py` - Added override notifications

### TODO
- [ ] Routes for override requests (CRUD endpoints)
- [ ] Scheduled job for auto-escalation
- [ ] Frontend components (modals, dashboards)
- [ ] Integration with retrieval "no context" flow

## Benefits

✅ **Self-service** - Users can request access when needed  
✅ **Hierarchical** - Department managers handle team requests  
✅ **Scalable** - Auto-escalation prevents bottlenecks  
✅ **Auditable** - Full trail of requests/approvals  
✅ **Flexible** - Org-wide or department-specific  
✅ **Time-limited** - Temporary access with automatic expiry  
✅ **Contextual** - Tracks what triggered the request  

## Next Steps

1. **Create Routes** - REST endpoints for requests/approvals
2. **Add Scheduled Job** - Auto-escalation cron
3. **Build Frontend** - Request modal, approval dashboard
4. **Integrate with Retrieval** - Show "Request Access" button
5. **Testing** - Unit + integration tests
6. **Documentation** - User guide for requesters/approvers
