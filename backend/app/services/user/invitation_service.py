"""
Invitation service for managing user invitations.
Handles invitation creation, validation, email delivery, and resending.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_invitation import UserInvitation
from app.models.user import User
from app.config.settings import settings
from app.core import get_logger
from app.services.email.builders.specialized import InvitationEmailBuilder


logger = get_logger(__name__)


class InvitationService:
    """Service for managing user invitations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.email_builder = InvitationEmailBuilder()
    
    async def create_invitation(
        self,
        email: str,
        inviter_id: int,
        role_name: Optional[str] = None,
        custom_message: Optional[str] = None,
        department_id: Optional[int] = None,
        is_manager: bool = False,
        org_level_permission: int = 1,
        department_level_permission: Optional[int] = None,
        invitation_link_template: Optional[str] = None,
        ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Create a new invitation and send email.
        
        Args:
            email: Email address to invite
            inviter_id: User ID of the inviter (admin or manager)
            role_name: Optional role to assign
            custom_message: Optional custom message for invitation
            department_id: Optional department to assign user to during onboarding
            is_manager: Whether to make user a manager of the assigned department
            org_level_permission: Organization-wide clearance level (1-4)
            department_level_permission: Department-specific clearance level (1-4, optional)
            invitation_link_template: Optional frontend signup link template with {token} placeholder
        
        Returns:
            Tuple of (invitation_data, error_message) where error_message is user-friendly
        """
        try:
            # Get inviter info
            inviter_result = await self.session.execute(
                select(User).where(User.id == inviter_id)
            )
            inviter = inviter_result.scalar_one_or_none()
            
            if not inviter:
                logger.error(f"Inviter {inviter_id} not found when creating invitation for {email}")
                return None, "Unable to process invitation at this time"
            
            # Validate department if provided
            if department_id:
                from app.models.department import Department
                dept_result = await self.session.execute(
                    select(Department).where(Department.id == department_id)
                )
                if not dept_result.scalar_one_or_none():
                    logger.warning(f"Department {department_id} not found for invitation")
                    return None, f"Department with ID {department_id} not found"
            
            # Check if email is already invited or registered
            result = await self.session.execute(
                select(UserInvitation).where(
                    UserInvitation.email == email.lower(),
                    UserInvitation.status == "pending"
                )
            )
            if result.scalar_one_or_none():
                logger.info(f"Pending invitation already exists for {email}")
                return None, "This email already has a pending invitation"
            
            result = await self.session.execute(
                select(User).where(User.email == email.lower())
            )
            if result.scalar_one_or_none():
                logger.info(f"User with email {email} already exists")
                return None, "This email is already registered"
            
            # Generate invitation token
            token = self._generate_token()
            
            # Calculate expiration
            expiry = datetime.now(timezone.utc) + timedelta(
                days=settings.INVITE_TOKEN_EXPIRE_DAYS
            )
            
            # Create invitation record with new fields
            invitation = UserInvitation(
                token=token,
                email=email.lower(),
                invited_by_id=inviter_id,
                assigned_role=role_name,
                invitation_message=custom_message,
                department_id=department_id,
                is_manager=is_manager,
                org_level_permission=org_level_permission,
                department_level_permission=department_level_permission,
                expires_at=expiry,
                status="pending",
            )
            
            self.session.add(invitation)
            await self.session.flush()
            
            # Send invitation email
            email_sent = await self._send_invitation_email(
                invitation=invitation,
                inviter_name=f"{inviter.first_name} {inviter.last_name}".strip(),
                link_template=invitation_link_template,
            )
            
            if not email_sent:
                logger.warning(f"Failed to send invitation email to {email}, but invitation record created (ID: {invitation.id})")
                # Continue anyway - invitation was created, email may be sent later
            
            await self.session.commit()
            
            logger.info(
                f"Invitation created for {email} by {inviter.username} "
                f"(ID: {invitation.id}) with role {role_name or 'none'}"
            )
            
            return {
                "id": invitation.id,
                "email": invitation.email,
                "token": invitation.token,
                "role": role_name,
                "expires_at": expiry.isoformat(),
            }, None
            
        except Exception as e:
            logger.error(f"Error creating invitation for {email}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return None, "Failed to create invitation"
    
    async def list_invitations(
        self,
        status_filter: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        List invitations with optional filtering and pagination.
        
        Args:
            status_filter: Filter by status (pending, accepted, expired)
            limit: Number of results per page
            offset: Pagination offset
        
        Returns:
            Tuple of (result_dict, error_message) where error_message is user-friendly
        """
        try:
            # Build query
            query = select(UserInvitation).order_by(UserInvitation.created_at.desc())
            
            # Apply status filter
            if status_filter == "expired":
                now = datetime.now(timezone.utc)
                query = query.where(
                    (UserInvitation.status == "pending") &
                    (UserInvitation.expires_at < now)
                )
            elif status_filter and status_filter in ["pending", "accepted"]:
                query = query.where(UserInvitation.status == status_filter)
            
            # Get total count
            count_query = select(UserInvitation)
            if status_filter == "expired":
                now = datetime.now(timezone.utc)
                count_query = count_query.where(
                    (UserInvitation.status == "pending") &
                    (UserInvitation.expires_at < now)
                )
            elif status_filter and status_filter in ["pending", "accepted"]:
                count_query = count_query.where(UserInvitation.status == status_filter)
            
            count_result = await self.session.execute(count_query)
            total = len(count_result.scalars().all())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await self.session.execute(query)
            invitations = result.scalars().all()
            
            # Format response
            invitations_data = [
                self._format_invitation(inv) for inv in invitations
            ]
            
            logger.info(f"Listed {len(invitations_data)} invitations (filter: {status_filter}, total: {total})")
            
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "invitations": invitations_data,
            }, None
            
        except Exception as e:
            logger.error(f"Error listing invitations (filter: {status_filter}): {str(e)}", exc_info=True)
            return None, "Failed to list invitations"
    
    async def resend_invitation(self, invitation_id: int) -> Tuple[bool, Optional[str]]:
        """
        Resend invitation email for a pending invitation.
        
        Args:
            invitation_id: ID of the invitation to resend
        
        Returns:
            Tuple of (success, error_message) where error_message is user-friendly
        """
        try:
            # Get invitation
            result = await self.session.execute(
                select(UserInvitation).where(UserInvitation.id == invitation_id)
            )
            invitation = result.scalar_one_or_none()
            
            if not invitation:
                logger.warning(f"Attempted to resend non-existent invitation {invitation_id}")
                return False, "Invitation not found"
            
            # Validate invitation status
            if invitation.status != "pending":
                logger.info(f"Attempted to resend invitation {invitation_id} with status '{invitation.status}'")
                return False, f"Cannot resend invitation with status '{invitation.status}'"
            
            if invitation.is_expired():
                logger.info(f"Attempted to resend expired invitation {invitation_id} for {invitation.email}")
                return False, "Invitation has expired. Please create a new invitation."
            
            # Get inviter info
            inviter = invitation.invited_by
            if not inviter:
                logger.error(f"Inviter information missing for invitation {invitation_id}")
                return False, "Inviter information not found"
            
            # Resend email
            email_sent = await self._send_invitation_email(
                invitation=invitation,
                inviter_name=f"{inviter.first_name} {inviter.last_name}".strip(),
            )
            
            if not email_sent:
                logger.error(f"Failed to send email when resending invitation {invitation_id} to {invitation.email}")
                return False, "Failed to send invitation email"
            
            logger.info(f"Resent invitation {invitation.id} to {invitation.email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error resending invitation {invitation_id}: {str(e)}", exc_info=True)
            return False, "Failed to resend invitation"
    
    async def verify_invitation_token(
        self, token: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify an invitation token and return invitation details.
        
        Args:
            token: Invitation token to verify
        
        Returns:
            Tuple of (invitation_data, error_message) where error_message is user-friendly
        """
        try:
            # Get invitation
            result = await self.session.execute(
                select(UserInvitation).where(UserInvitation.token == token)
            )
            invitation = result.scalar_one_or_none()
            
            if not invitation:
                logger.warning(f"Verification attempt with invalid token")
                return None, "Invalid invitation token"
            
            # Check if valid
            if not invitation.is_valid():
                if invitation.status != "pending":
                    logger.info(f"Verification attempt for already {invitation.status} invitation {invitation.id}")
                    return None, f"Invitation has already been {invitation.status}"
                else:
                    logger.info(f"Verification attempt for expired invitation {invitation.id}")
                    return None, "Invitation has expired"
            
            logger.info(f"Successfully verified invitation token for {invitation.email}")
            
            return {
                "email": invitation.email,
                "role_name": invitation.assigned_role,
                "message": invitation.invitation_message,
            }, None
            
        except Exception as e:
            logger.error(f"Error verifying invitation token: {str(e)}", exc_info=True)
            return None, "Failed to verify invitation token"
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _generate_token(self) -> str:
        """Generate a cryptographically secure invitation token."""
        return secrets.token_urlsafe(32)
    
    async def _send_invitation_email(
        self,
        invitation: UserInvitation,
        inviter_name: str,
        link_template: Optional[str] = None,
    ) -> bool:
        """
        Send invitation email.
        
        Args:
            invitation: UserInvitation object
            inviter_name: Name of the person sending invitation
            link_template: Optional frontend signup link template with {token} placeholder
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            await self.email_builder.build_and_send(
                recipient_email=invitation.email,
                recipient_name=invitation.email.split('@')[0],
                inviter_name=inviter_name,
                organization_name=settings.APP_NAME,
                invitation_token=invitation.token,
                custom_message=invitation.invitation_message,
                invitation_link_template=link_template,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            return False
    
    def _format_invitation(self, invitation: UserInvitation) -> Dict[str, Any]:
        """Format invitation object for response."""
        is_expired = invitation.is_expired()
        
        return {
            "id": invitation.id,
            "email": invitation.email,
            "assigned_role": invitation.assigned_role,
            "status": invitation.status,
            "is_expired": is_expired,
            "expires_at": invitation.expires_at.isoformat(),
            "accepted_at": invitation.accepted_at.isoformat()
            if invitation.accepted_at
            else None,
            "invited_by": {
                "id": invitation.invited_by.id,
                "username": invitation.invited_by.username,
                "full_name": f"{invitation.invited_by.first_name} {invitation.invited_by.last_name}".strip(),
            }
            if invitation.invited_by
            else None,
            "created_at": invitation.created_at.isoformat(),
            # New fields
            "invitation_message": invitation.invitation_message,
            "department_id": invitation.department_id,
            "is_manager": invitation.is_manager,
        }
