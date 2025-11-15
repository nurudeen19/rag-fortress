"""
Security module for JWT token generation, validation, and authentication.

Handles:
- JWT token creation and validation
- Password hashing and verification
- Authentication dependencies for FastAPI
- Current user extraction from tokens
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.user import User
from app.core.database import get_session
from app.core import get_logger


logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User ID to encode in token
        expires_delta: Custom expiration time (uses settings default if None)
    
    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    # Ensure token is a string (jwt.encode may return bytes in some versions)
    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode('utf-8')
    
    logger.debug(f"Created access token for user {user_id}")
    return encoded_jwt


def verify_token(token: str) -> Optional[int]:
    """
    Verify a JWT token and extract user ID.
    
    Args:
        token: JWT token to verify
    
    Returns:
        User ID if valid, None if invalid
    
    Raises:
        HTTPException if token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
        
        return int(user_id)
    
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> int:
    """
    Extract and validate user ID from Authorization header.
    
    Header format: Authorization: Bearer <token>
    
    Returns:
        User ID
    
    Raises:
        HTTPException if token is missing or invalid
    """
    # Get token from Authorization header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Get current authenticated user from token.
    
    Returns:
        User object
    
    Raises:
        HTTPException if user not found or account locked
    """
    user = await session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is locked"
        )
    
    return user


def require_permission(permission_code: str):
    """
    Create a dependency that checks if user has a specific permission.
    
    Usage:
        @router.post("/approve")
        async def approve(
            file_id: int,
            user: User = Depends(require_permission("file_upload_approve"))
        ):
            # Only users with this permission can access
            pass
    
    Args:
        permission_code: Permission code to check
    
    Returns:
        Dependency function
    """
    async def check_permission(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
    ) -> User:
        from app.services.user import RolePermissionService
        
        role_service = RolePermissionService(session)
        has_permission = await role_service.user_has_permission(
            current_user.id,
            permission_code
        )
        
        if not has_permission:
            logger.warning(
                f"User {current_user.id} denied access: missing permission '{permission_code}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return check_permission


def require_role(role_name: str):
    """
    Create a dependency that checks if user has a specific role.
    
    Usage:
        @router.post("/admin")
        async def admin_action(
            user: User = Depends(require_role("admin"))
        ):
            # Only admins can access
            pass
    
    Args:
        role_name: Role name to check
    
    Returns:
        Dependency function
    """
    async def check_role(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.has_role(role_name):
            logger.warning(
                f"User {current_user.id} denied access: missing role '{role_name}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires '{role_name}' role"
            )
        
        return current_user
    
    return check_role
