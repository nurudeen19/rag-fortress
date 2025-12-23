"""
Base Event Handler

All event handlers should inherit from this base class to ensure
consistency and proper integration with the EventBus.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from app.core import get_logger


logger = get_logger(__name__)


class BaseEventHandler(ABC):
    """
    Base class for all event handlers.
    
    Each event handler should:
    1. Inherit from this class
    2. Implement the handle() method
    3. Define event_type property
    4. Be self-contained and independent
    
    Example:
        class MyEventHandler(BaseEventHandler):
            @property
            def event_type(self) -> str:
                return "my_event"
            
            async def handle(self, event_data: Dict[str, Any]) -> None:
                # Process the event
                pass
    """
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """
        Return the event type this handler processes.
        
        This should be a unique identifier for the event type.
        Examples: "activity_log", "user_registered", "email_sent"
        """
        pass
    
    @abstractmethod
    async def handle(self, event_data: Dict[str, Any]) -> None:
        """
        Process the event.
        
        This method should:
        - Be async
        - Handle its own database sessions if needed
        - Catch and log errors (don't let them propagate)
        - Be idempotent when possible
        
        Args:
            event_data: Dictionary containing all event data
                       Always includes:
                       - _event_type: str (the event type)
                       - _emitted_at: str (ISO format timestamp)
                       Plus any custom fields passed during emission
        """
        pass
    
    async def __call__(self, event_data: Dict[str, Any]) -> None:
        """
        Make the handler callable so it can be used directly with EventBus.
        
        This wraps the handle() method with error handling.
        """
        try:
            await self.handle(event_data)
        except Exception as e:
            logger.error(
                f"Error in {self.__class__.__name__} for '{self.event_type}' event: {e}",
                exc_info=True
            )
