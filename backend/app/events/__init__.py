"""
Events Package

This package contains all event handlers for the application.
Each event handler is self-contained and can be easily added or removed
without affecting other handlers.

To create a new event:
1. Create a new file in this directory (e.g., my_event.py)
2. Inherit from BaseEventHandler
3. Implement the handle() method
4. The event will be auto-registered on application startup
"""

from app.events.base import BaseEventHandler

__all__ = ["BaseEventHandler"]
