"""
Email configuration settings.
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from fastapi_mail import ConnectionConfig
except ImportError:
    # Allow settings to be imported even if fastapi_mail isn't installed
    ConnectionConfig = None


class EmailSettings(BaseSettings):
    """Email and SMTP configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # SMTP Configuration
    SMTP_SERVER: str = Field("localhost", env="SMTP_SERVER")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field("noreply@ragfortress.com", env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field("RAG Fortress", env="SMTP_FROM_NAME")
    SMTP_USE_TLS: bool = Field(True, env="SMTP_USE_TLS")
    SMTP_USE_SSL: bool = Field(False, env="SMTP_USE_SSL")
    
    # Email Token Expiry Settings
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = Field(
        24 * 60, 
        env="EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES"
    )  # 24 hours
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(
        60,
        env="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"
    )  # 1 hour
    INVITE_TOKEN_EXPIRE_DAYS: int = Field(
        7,
        env="INVITE_TOKEN_EXPIRE_DAYS"
    )  # 7 days
    
    # Frontend URLs for email links
    FRONTEND_URL: str = Field("http://localhost:5173", env="FRONTEND_URL")
    EMAIL_VERIFICATION_URL: str = Field(
        "http://localhost:5173/verify-email", 
        env="EMAIL_VERIFICATION_URL"
    )
    PASSWORD_RESET_URL: str = Field(
        "http://localhost:5173/reset-password", 
        env="PASSWORD_RESET_URL"
    )
    INVITE_URL: str = Field(
        "http://localhost:5173/accept-invite", 
        env="INVITE_URL"
    )

    @field_validator("SMTP_PORT")
    @classmethod
    def validate_smtp_port(cls, v: int) -> int:
        """Validate SMTP port is in valid range."""
        if v < 1 or v > 65535:
            raise ValueError(f"SMTP_PORT must be between 1 and 65535, got {v}")
        return v

    @field_validator("SMTP_USE_SSL", mode="after")
    @classmethod
    def validate_tls_ssl_conflict(cls, v: bool, info) -> bool:
        """Ensure both TLS and SSL are not enabled simultaneously."""
        smtp_use_tls = info.data.get("SMTP_USE_TLS", False)
        if v and smtp_use_tls:
            raise ValueError("Cannot use both SMTP_USE_TLS and SMTP_USE_SSL")
        return v

    def validate_config(self):
        """Validate email configuration."""
        # Only validate if SMTP is configured
        if self.SMTP_USERNAME and self.SMTP_PASSWORD:
            if not self.SMTP_FROM_EMAIL:
                raise ValueError("SMTP_FROM_EMAIL is required when SMTP is configured")
        else:
            # Email is optional - SMTP configuration is not required
            pass

    def get_connection_config(self):
        """
        Creates a FastMail ConnectionConfig instance from SMTP settings.
        
        This method creates a ConnectionConfig object that can be used
        with FastMail for sending emails.
        
        Returns:
            ConnectionConfig instance for FastMail
        """
        if ConnectionConfig is None:
            raise ImportError("fastapi_mail is required for email functionality. Install it with: pip install fastapi-mail")
        
        return ConnectionConfig(
            MAIL_USERNAME=self.SMTP_USERNAME or "",
            MAIL_PASSWORD=self.SMTP_PASSWORD or "",
            MAIL_FROM=self.SMTP_FROM_EMAIL,
            MAIL_FROM_NAME=self.SMTP_FROM_NAME,
            MAIL_PORT=self.SMTP_PORT,
            MAIL_SERVER=self.SMTP_SERVER,
            MAIL_STARTTLS=self.SMTP_USE_TLS,
            MAIL_SSL_TLS=self.SMTP_USE_SSL,
            USE_CREDENTIALS=bool(self.SMTP_USERNAME and self.SMTP_PASSWORD),
            VALIDATE_CERTS=True,
        )
