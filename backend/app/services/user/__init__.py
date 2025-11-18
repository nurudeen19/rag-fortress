"""
User management services.

Modular services for handling all user-related operations:
- Authentication (login, logout, token management)
- Password management (changes, resets, validation)
- Account management (creation, activation, suspension)
- Role and permission management (assignment, checking)
- Invitation management (creation, sending, verification)
- Profile management (retrieval, updates)

All services follow a simple pattern:
1. Take AsyncSession as constructor parameter
2. Return Tuple[Result, Optional[error]] for operations
3. Log all significant operations
4. Raise exceptions only for unexpected errors, not validation failures
"""

from app.services.user.auth_service import AuthService
from app.services.user.password_service import PasswordService
from app.services.user.user_service import UserAccountService
from app.services.user.role_permission_service import RolePermissionService
from app.services.user.invitation_service import InvitationService
from app.services.user.profile_service import UserProfileService

__all__ = [
    "AuthService",
    "PasswordService",
    "UserAccountService",
    "RolePermissionService",
    "InvitationService",
    "UserProfileService",
]
