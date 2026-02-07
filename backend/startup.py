#!/usr/bin/env python3
"""
Application startup script with environment-aware configuration.

Usage:
    python startup.py                    # Run in production mode (no reload)
    python startup.py --reload           # Run in development mode (with reload)
    python startup.py --dev              # Same as --reload
    ENVIRONMENT=development python startup.py  # Set via environment variable
"""

import sys
import os
from typing import Tuple
import uvicorn
from app.config.settings import settings


def get_environment() -> Tuple[str, bool]:
    """Determine environment and reload setting from CLI args or environment variables.
    
    Priority:
    1. CLI flags (--reload, --dev) enable reload and set environment to development
    2. ENVIRONMENT variable sets the environment and enables reload if set to "development"
    3. Default to production with reload disabled
    
    Returns:
        Tuple of (environment, reload_enabled)
        environment: 'production' or 'development'
        reload_enabled: True if reload should be enabled
    """
    # Check CLI arguments
    reload_flag = "--reload" in sys.argv or "--dev" in sys.argv
    env_setting = os.getenv("ENVIRONMENT", "production").lower()
    
    # Reload is enabled if: CLI flag is set OR environment is development
    reload_enabled = reload_flag or (env_setting == "development")
    
    # Environment is development if: reload flag given OR environment var says development
    environment = "development" if (reload_flag or env_setting == "development") else "production"
    
    return environment, reload_enabled


if __name__ == "__main__":
    environment, reload = get_environment()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower()
    )

