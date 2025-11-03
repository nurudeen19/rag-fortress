#!/usr/bin/env python3
"""
Production server runner.
"""

import uvicorn
from app.config.settings import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=4,  # Number of worker processes
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
