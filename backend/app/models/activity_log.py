"""
Activity Log model for tracking user actions and security incidents.

Tracks:
- Document access attempts (authorized and unauthorized)
- Query validation failures (malicious patterns)
- Permission violations
- System access patterns
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base


# Incident type naming convention guidelines (not restrictive, just suggestions)
# Format: snake_case for consistency
# Common types:
#   - malicious_query_blocked
#   - document_access_granted
#   - document_access_denied
#   - insufficient_clearance
#   - clearance_override_used
#   - bulk_document_request
#   - suspicious_activity
#   - access_pattern_anomaly
#   - query_validation_failed
#   - sensitive_data_access


class ActivityLog(Base):
    """
    Activity log for tracking user actions and security incidents.
    
    Provides comprehensive audit trail for:
    - Compliance requirements (who accessed what when)
    - Security monitoring (detect unusual patterns)
    - Access request workflows (user discovers restricted content)
    - Incident investigation (trace security events)
    """
    
    __tablename__ = "activity_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Incident classification (flexible string, not restricted by enum)
    # Use consistent naming: snake_case (e.g., "malicious_query_blocked", "access_denied")
    incident_type = Column(String(100), nullable=False, index=True)
    
    # Severity level for filtering/alerting
    severity = Column(String(20), nullable=False, default="info", index=True)  # info, warning, critical
    
    # Human-readable description
    description = Column(String(500), nullable=False)
    
    # Structured details (JSON format)
    details = Column(Text, nullable=True)
    
    # Access control context
    user_clearance_level = Column(String(50), nullable=True)
    required_clearance_level = Column(String(50), nullable=True)
    access_granted = Column(Boolean, nullable=True, index=True)
    
    # Query/action context
    user_query = Column(Text, nullable=True)
    threat_type = Column(String(100), nullable=True)  # prompt_injection, sql_injection, etc.


    # IP address and user agent for security tracking
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp (inherited from Base: created_at, updated_at)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="activity_logs")
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    
    # Indexes for performance (removed document_id index as field removed)
    __table_args__ = (
        Index('idx_activity_user_type', 'user_id', 'incident_type'),
        Index('idx_activity_user_created', 'user_id', 'created_at'),
        Index('idx_activity_severity_created', 'severity', 'created_at'),
        Index('idx_activity_type_created', 'incident_type', 'created_at'),
        Index('idx_activity_access_denied', 'user_id', 'access_granted', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, type={self.incident_type}, severity={self.severity})>"
    
    @property
    def user_name(self) -> str:
        """Get user's full name from relationship."""
        if not self.user:
            return "Unknown"
        # Try to get from user_profile first
        if hasattr(self.user, 'user_profile') and self.user.user_profile:
            first_name = getattr(self.user.user_profile, 'first_name', '')
            last_name = getattr(self.user.user_profile, 'last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                return full_name
        # Fall back to email
        return self.user.email or "Unknown"
    
    @property
    def user_department(self) -> str:
        """Get user's department name from relationship."""
        if not self.user or not hasattr(self.user, 'department'):
            return None
        if self.user.department and hasattr(self.user.department, 'name'):
            return self.user.department.name
        return None
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_department": self.user_department,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
            "user_clearance_level": self.user_clearance_level,
            "required_clearance_level": self.required_clearance_level,
            "access_granted": self.access_granted,
            "user_query": self.user_query[:100] if self.user_query else None,  # Truncate for privacy
            "threat_type": self.threat_type,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
