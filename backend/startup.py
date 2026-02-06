#!/usr/bin/env python3
"""
Development server runner.
"""

import uvicorn
from app.config.settings import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Enable auto-reload in development
        log_level=settings.LOG_LEVEL.lower()
    )
