"""Service for handling permission override requests and approval workflow.

This service manages the complete lifecycle of permission override requests using
the extended PermissionOverride model with status field for approval workflow:
- Request submission by users (status=PENDING)
- Automatic approver determination
- Approval/denial processing (status=APPROVED/DENIED)
- Auto-escalation to admins
- Notification sending
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission_override import PermissionOverride, OverrideType, OverrideStatus
from app.models.user import User
from app.models.department import Department
from app.models.user_permission import UserPermission, PermissionLevel
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _load_override_relationships(query):
    """Helper to load all relationships needed for OverrideRequestResponse."""
    return query.options(
        selectinload(PermissionOverride.user),
        selectinload(PermissionOverride.approver),
        selectinload(PermissionOverride.department)
    )


class OverrideRequestService:
    """Service for managing permission override requests and approvals."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
    
    async def create_request(
        self,
        requester_id: int,
        override_type: str,
        requested_permission_level: int,
        reason: str,
        requested_duration_hours: Optional[int] = None,
        custom_duration_days: Optional[int] = None,
        department_id: Optional[int] = None,
        trigger_query: Optional[str] = None,
        trigger_file_id: Optional[int] = None,
    ) -> Tuple[Optional[PermissionOverride], Optional[str]]:
        """
        Create a new permission override request (status=PENDING).
        
        Args:
            requester_id: User requesting the override
            override_type: 'org_wide' or 'department'
            requested_permission_level: Permission level (1-4)
            reason: Business justification
            requested_duration_hours: Preset duration in hours (for quick selections)
            custom_duration_days: Custom duration in days (for longer-term projects)
            department_id: Required for department requests
            trigger_query: Optional query that triggered this request
            trigger_file_id: Optional file that couldn't be accessed
            
        Returns:
            Tuple of (request, error_message)
        """
        try:
            # Validation
            if override_type == OverrideType.DEPARTMENT.value and not department_id:
                return None, "Department ID required for department-level requests"
            
            if requested_permission_level not in [1, 2, 3, 4]:
                return None, "Invalid permission level (must be 1-4)"
            
            # Determine actual duration in hours
            if requested_duration_hours and requested_duration_hours > 0:
                total_duration_hours = requested_duration_hours
                if total_duration_hours > 8760:  # Max 1 year
                    return None, "Duration must not exceed 1 year (8760 hours)"
            elif custom_duration_days and custom_duration_days > 0:
                total_duration_hours = custom_duration_days * 24
                if total_duration_hours > 8760:  # Max 1 year
                    return None, "Custom duration must not exceed 365 days"
            else:
                return None, "Either requested_duration_hours or custom_duration_days must be provided"
            
            # Get requester's current permissions and roles
            user_result = await self.session.execute(
                select(User)
                .options(
                    selectinload(User.user_permission),
                    selectinload(User.roles)
                )
                .where(User.id == requester_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None, "User not found"
            
            # Admins cannot submit override requests - they approve them
            if user.has_role("admin"):
                return None, "Administrators cannot submit permission requests. Admins have full access and approve requests from others."
            
            # Check if they already have this level or higher
            if override_type == OverrideType.ORG_WIDE.value:
                current_level = user.user_permission.org_level_permission if user.user_permission else 1
                if current_level >= requested_permission_level:
                    return None, f"You already have {PermissionLevel(current_level).name} organization clearance"
            else:
                current_level = user.user_permission.department_level_permission if user.user_permission else None
                if current_level and current_level >= requested_permission_level:
                    return None, f"You already have {PermissionLevel(current_level).name} department clearance"
            
            # Create override request (PENDING status, dates will be set on approval)
            override_request = PermissionOverride(
                user_id=requester_id,
                override_type=override_type,
                department_id=department_id,
                override_permission_level=requested_permission_level,
                reason=reason,
                requested_duration_hours=total_duration_hours,
                valid_from=datetime.now(timezone.utc),  # Placeholder, will be set on approval
                valid_until=datetime.now(timezone.utc),  # Placeholder, will be set on approval
                created_by_id=requester_id,  # Requester creates the request
                status=OverrideStatus.PENDING.value,
                is_active=False,  # Not active until approved
                trigger_query=trigger_query,
                trigger_file_id=trigger_file_id,
            )
            
            self.session.add(override_request)
            await self.session.flush()
            
            # Reload the object to load relationships properly
            await self.session.refresh(override_request, ["user", "approver", "department"])
            
            # Determine and notify approver
            await self._notify_approver(override_request)
            
            logger.info(
                f"Override request created: id={override_request.id}, user={requester_id}, "
                f"type={override_type}, level={requested_permission_level}, duration_hours={total_duration_hours}"
            )
            
            return override_request, None
            
        except Exception as e:
            logger.error(f"Error creating override request: {e}", exc_info=True)
            return None, "Failed to create request. Please try again."
    
    async def approve_request(
        self,
        request_id: int,
        approver_id: int,
        approval_notes: Optional[str] = None,
    ) -> Tuple[Optional[PermissionOverride], Optional[str]]:
        """
        Approve a permission override request.
        
        Updates status to APPROVED, sets is_active=True, and adjusts valid_from to now.
        
        Args:
            request_id: Request to approve
            approver_id: User approving the request
            approval_notes: Optional notes from approver
            
        Returns:
            Tuple of (approved_override, error_message)
        """
        try:
            # Get request with relationships
            result = await self.session.execute(
                _load_override_relationships(
                    select(PermissionOverride)
                    .where(PermissionOverride.id == request_id)
                )
            )
            override_request = result.scalar_one_or_none()
            
            if not override_request:
                return None, "Request not found"
            
            if not override_request.is_pending():
                return None, f"Request already {override_request.status}"
            
            # Verify approver has authority
            can_approve, error_msg = await self._verify_approver_authority(
                override_request, approver_id
            )
            if not can_approve:
                return None, error_msg
            
            # Calculate valid dates based on requested duration (now on approval)
            valid_from = datetime.now(timezone.utc)
            valid_until = valid_from + timedelta(hours=override_request.requested_duration_hours)
            
            # Update the override
            override_request.status = OverrideStatus.APPROVED.value
            override_request.approver_id = approver_id
            override_request.approval_notes = approval_notes
            override_request.decided_at = datetime.now(timezone.utc)
            override_request.is_active = True
            override_request.valid_from = valid_from
            override_request.valid_until = valid_until
            
            # Notify requester
            await self._notify_requester_approved(override_request)
            
            logger.info(
                f"Override request approved: request_id={request_id}, "
                f"approver_id={approver_id}"
            )
            
            return override_request, None
            
        except Exception as e:
            logger.error(f"Error approving request: {e}", exc_info=True)
            return None, "Failed to approve request. Please try again."
    
    async def deny_request(
        self,
        request_id: int,
        approver_id: int,
        denial_reason: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Deny a permission override request.
        
        Updates status to DENIED.
        
        Args:
            request_id: Request to deny
            approver_id: User denying the request
            denial_reason: Reason for denial
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get request
            result = await self.session.execute(
                _load_override_relationships(
                    select(PermissionOverride)
                    .where(PermissionOverride.id == request_id)
                )
            )
            override_request = result.scalar_one_or_none()
            
            if not override_request:
                return False, "Request not found"
            
            if not override_request.is_pending():
                return False, f"Request already {override_request.status}"
            
            # Verify approver has authority
            can_approve, error_msg = await self._verify_approver_authority(
                override_request, approver_id
            )
            if not can_approve:
                return False, error_msg
            
            # Update request
            override_request.status = OverrideStatus.DENIED.value
            override_request.approver_id = approver_id
            override_request.approval_notes = denial_reason
            override_request.decided_at = datetime.now(timezone.utc)
            
            # Notify requester
            await self._notify_requester_denied(override_request, denial_reason)
            
            logger.info(
                f"Override request denied: request_id={request_id}, "
                f"approver_id={approver_id}"
            )
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error denying request: {e}", exc_info=True)
            return False, "Failed to deny request. Please try again."
    
    async def cancel_request(
        self,
        request_id: int,
        requester_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Cancel a pending request (by requester).
        
        Args:
            request_id: Request to cancel
            requester_id: Must match request's user_id
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = await self.session.execute(
                select(PermissionOverride)
                .where(PermissionOverride.id == request_id)
            )
            override_request = result.scalar_one_or_none()
            
            if not override_request:
                return False, "Request not found"
            
            if override_request.user_id != requester_id:
                return False, "You can only cancel your own requests"
            
            if not override_request.can_be_cancelled():
                return False, f"Cannot cancel {override_request.status} request"
            
            # Delete the pending request
            await self.session.delete(override_request)
            
            logger.info(f"Override request cancelled: request_id={request_id}")
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error cancelling request: {e}", exc_info=True)
            return False, "Failed to cancel request. Please try again."
    
    async def get_pending_requests_for_approver(
        self,
        approver_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PermissionOverride]:
        """
        Get pending override requests that a user can approve.
        
        For admins: all org_wide requests + all department requests
        For department managers: requests for their department
        
        Args:
            approver_id: User ID
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of pending requests
        """
        try:
            # Get user with relationships
            user_result = await self.session.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.id == approver_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return []
            
            is_admin = user.has_role("admin")
            
            if is_admin:
                # Admins see all pending requests
                query = _load_override_relationships(
                    select(PermissionOverride)
                    .where(PermissionOverride.status == OverrideStatus.PENDING.value)
                    .order_by(PermissionOverride.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            else:
                # Department managers see requests for their department
                dept_result = await self.session.execute(
                    select(Department)
                    .where(Department.manager_id == approver_id)
                )
                department = dept_result.scalar_one_or_none()
                
                if not department:
                    return []  # Not a manager
                
                query = _load_override_relationships(
                    select(PermissionOverride)
                    .where(
                        and_(
                            PermissionOverride.status == OverrideStatus.PENDING.value,
                            PermissionOverride.department_id == department.id,
                            PermissionOverride.override_type == OverrideType.DEPARTMENT.value
                        )
                    )
                    .order_by(PermissionOverride.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error fetching pending requests: {e}", exc_info=True)
            return []
    
    async def get_requests_for_approver(
        self,
        approver_id: int,
        status: str = "pending",
        limit: int = 50,
        offset: int = 0,
    ) -> List[PermissionOverride]:
        """
        Get override requests that a user can approve, filtered by status.
        
        For admins: all requests with the specified status
        For department managers: requests for their department with the specified status
        
        Args:
            approver_id: User ID
            status: Status filter (pending, approved, denied, expired, revoked)
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of requests with the specified status
        """
        try:
            # Get user with relationships
            user_result = await self.session.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.id == approver_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return []
            
            is_admin = user.has_role("admin")
            
            if is_admin:
                # Admins see all requests with the specified status
                query = _load_override_relationships(
                    select(PermissionOverride)
                    .where(PermissionOverride.status == status)
                    .order_by(PermissionOverride.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            else:
                # Department managers see requests for their department with the specified status
                dept_result = await self.session.execute(
                    select(Department)
                    .where(Department.manager_id == approver_id)
                )
                department = dept_result.scalar_one_or_none()
                
                if not department:
                    return []  # Not a manager
                
                query = _load_override_relationships(
                    select(PermissionOverride)
                    .where(
                        and_(
                            PermissionOverride.status == status,
                            PermissionOverride.department_id == department.id,
                            PermissionOverride.override_type == OverrideType.DEPARTMENT.value
                        )
                    )
                    .order_by(PermissionOverride.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error fetching requests for approver: {e}", exc_info=True)
            return []
    
    async def get_user_requests(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[PermissionOverride]:
        """
        Get override requests for a user.
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of requests
        """
        try:
            query = _load_override_relationships(
                select(PermissionOverride)
                .where(PermissionOverride.user_id == user_id)
            )
            
            if status:
                query = query.where(PermissionOverride.status == status)
            
            query = (
                query
                .order_by(PermissionOverride.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error fetching user requests: {e}", exc_info=True)
            return []
    
    async def process_auto_escalations(
        self,
        escalation_threshold_hours: int = 24,
    ) -> int:
        """
        Auto-escalate pending requests that haven't been reviewed.
        
        This should be run periodically (e.g., hourly job).
        Department requests that are pending for > threshold hours
        get escalated to admins.
        
        Args:
            escalation_threshold_hours: Hours before escalation
            
        Returns:
            Number of requests escalated
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=escalation_threshold_hours)
            
            # Find pending department requests past threshold
            result = await self.session.execute(
                _load_override_relationships(
                    select(PermissionOverride)
                    .where(
                        and_(
                            PermissionOverride.status == OverrideStatus.PENDING.value,
                            PermissionOverride.override_type == OverrideType.DEPARTMENT.value,
                            PermissionOverride.auto_escalated.is_(False),
                            PermissionOverride.created_at <= cutoff_time
                        )
                    )
                )
            )
            requests = list(result.scalars().all())
            
            escalated_count = 0
            for request in requests:
                request.auto_escalated = True
                request.escalated_at = datetime.now(timezone.utc)
                
                # Notify admins
                await self._notify_admins_escalation(request)
                escalated_count += 1
            
            if escalated_count > 0:
                logger.info(f"Auto-escalated {escalated_count} override requests to admins")
            
            return escalated_count
            
        except Exception as e:
            logger.error(f"Error processing auto-escalations: {e}", exc_info=True)
            return 0

    async def process_expired_overrides(self) -> int:
        """
        Deactivate overrides that are past their valid_until window.
        Sets is_active=False and status=EXPIRED when applicable.
        """
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(PermissionOverride)
                .where(
                    and_(
                        PermissionOverride.is_active.is_(True),
                        PermissionOverride.status == OverrideStatus.APPROVED.value,
                        PermissionOverride.valid_until < now,
                    )
                )
            )
            overrides = list(result.scalars().all())

            # Prepare cache invalidation for affected users
            user_ids = {ov.user_id for ov in overrides}
            cache = None

            expired_count = 0
            for override in overrides:
                override.is_active = False
                override.status = OverrideStatus.EXPIRED.value
                expired_count += 1

            if expired_count > 0:
                logger.info(f"Marked {expired_count} override(s) as expired")

                # Lazy import to avoid circulars
                from app.utils.user_clearance_cache import get_user_clearance_cache
                cache = cache or get_user_clearance_cache(self.session)
                for user_id in user_ids:
                    await cache.invalidate(user_id)

            return expired_count

        except Exception as e:
            logger.error(f"Error processing expired overrides: {e}", exc_info=True)
            return 0
    
    # Helper methods
    
    async def _verify_approver_authority(
        self,
        override_request: PermissionOverride,
        approver_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """Verify approver has authority to approve this request."""
        user_result = await self.session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == approver_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False, "Approver not found"
        
        # Prevent self-approval - users cannot approve their own requests
        if override_request.user_id == approver_id:
            return False, "You cannot approve your own permission request"
        
        is_admin = user.has_role("admin")
        
        # Admins can approve anything (except their own, already checked)
        if is_admin:
            return True, None
        
        # For org_wide, only admins can approve
        if override_request.override_type == OverrideType.ORG_WIDE.value:
            return False, "Only admins can approve organization-wide requests"
        
        # For department, check if user is the department manager
        if override_request.department_id:
            dept_result = await self.session.execute(
                select(Department)
                .where(
                    and_(
                        Department.id == override_request.department_id,
                        Department.manager_id == approver_id
                    )
                )
            )
            department = dept_result.scalar_one_or_none()
            
            if department:
                # Manager can approve requests from subordinates in their department
                return True, None
        
        return False, "You do not have authority to approve this request"
    
    async def _notify_approver(self, override_request: PermissionOverride) -> None:
        """Notify appropriate approver about new request."""
        try:
            if override_request.override_type == OverrideType.ORG_WIDE.value:
                # Notify all admins
                await self.notification_service.notify_admins_new_override_request(override_request)
                return

            # Department-level: prefer the department manager, else fall back to admins
            if override_request.department_id:
                dept_result = await self.session.execute(
                    select(Department).where(Department.id == override_request.department_id)
                )
                dept = dept_result.scalar_one_or_none()
                
                if dept and dept.manager_id and dept.manager_id != override_request.user_id:
                    await self.notification_service.notify_override_request_submitted(
                        override_request, dept.manager_id
                    )
                    return
                
                logger.info(
                    "Falling back to admin notification for department request: "
                    f"request_id={override_request.id}, dept_id={override_request.department_id}"
                )

            # If no department or no eligible manager, notify admins
            await self.notification_service.notify_admins_new_override_request(override_request)
        except Exception as e:
            logger.error(f"Error notifying approver: {e}", exc_info=True)
    
    async def _notify_admins_escalation(self, override_request: PermissionOverride) -> None:
        """Notify admins about escalated request."""
        try:
            await self.notification_service.notify_admins_override_escalation(override_request)
        except Exception as e:
            logger.error(f"Error notifying admins of escalation: {e}", exc_info=True)
    
    async def _notify_requester_approved(self, override_request: PermissionOverride) -> None:
        """Notify requester that their request was approved."""
        try:
            await self.notification_service.notify_override_request_approved(override_request)
        except Exception as e:
            logger.error(f"Error notifying requester of approval: {e}", exc_info=True)
    
    async def _notify_requester_denied(
        self,
        override_request: PermissionOverride,
        denial_reason: str,
    ) -> None:
        """Notify requester that their request was denied."""
        try:
            await self.notification_service.notify_override_request_denied(
                override_request, denial_reason
            )
        except Exception as e:
            logger.error(f"Error notifying requester of denial: {e}", exc_info=True)
