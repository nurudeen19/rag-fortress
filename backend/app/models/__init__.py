"""
Models module for SQLAlchemy ORM models.

This module exports all model classes and the declarative base.
"""
from app.models.base import Base
from app.models.application_setting import ApplicationSetting
from app.models.department import Department
from app.models.user import User
from app.models.auth import Role, Permission, user_roles, role_permissions
from app.models.user_profile import UserProfile
from app.models.user_invitation import UserInvitation
from app.models.user_permission import UserPermission, PermissionLevel
from app.models.permission_override import PermissionOverride, OverrideType
from app.models.file_upload import FileUpload, FileStatus, SecurityLevel
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.activity_log import ActivityLog
from app.models.error_report import ErrorReport, ErrorReportStatus, ErrorReportCategory

__all__ = [
    "Base",
    "ApplicationSetting",
    "Department",
    "User",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "UserProfile",
    "UserInvitation",
    "UserPermission",
    "PermissionLevel",
    "PermissionOverride",
    "OverrideType",
    "FileUpload",
    "FileStatus",
    "SecurityLevel",
    "Conversation",
    "Message",
    "MessageRole",
    "ActivityLog",
    "ErrorReport",
    "ErrorReportStatus",
    "ErrorReportCategory",
]
