"""
Event Bus System

Provides asynchronous event emission and handling for non-critical tasks.
Decouples event producers from consumers, improving response latency.

Events are processed in background tasks without blocking the main request flow.

The EventBus is responsible for managing all events. Individual event handlers
are defined in the app/events/ directory for better modularity and scalability.
"""

from typing import Callable, Dict, List, Any, Optional, Tuple
from collections import defaultdict
import asyncio
from datetime import datetime, timezone
import importlib
import pkgutil
from pathlib import Path

from app.events.base import BaseEventHandler
import app.events

from app.core import get_logger


logger = get_logger(__name__)


def _resolve_handler(handler: Callable) -> Tuple[Callable, str]:
    """Return a coroutine callable plus a friendly name for logs."""

    handler_name = getattr(handler, "__name__", handler.__class__.__name__)
    candidate = handler

    if not asyncio.iscoroutinefunction(candidate) and hasattr(handler, "__call__"):
        candidate = handler.__call__

    if not asyncio.iscoroutinefunction(candidate):
        raise ValueError(f"Handler {handler_name} must be an async function")

    return candidate, handler_name


def _get_handler_display_name(handler: Callable) -> str:
    """Prefer the owning class name when a bound method is logged."""

    if hasattr(handler, "__self__") and handler.__self__:
        return handler.__self__.__class__.__name__
    return getattr(handler, "__name__", handler.__class__.__name__)


class EventBus:
    """
    Simple in-process event bus for asynchronous task execution.
    
    Features:
    - Non-blocking event emission
    - Multiple subscribers per event type
    - Background task execution
    - Error isolation (handler failures don't block other handlers)
    - Graceful degradation (events can be processed even if some handlers fail)
    """
    
    _instance: Optional['EventBus'] = None
    
    def __new__(cls) -> 'EventBus':
        """Singleton pattern - one event bus per application."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize event bus with handler registry."""
        if hasattr(self, '_initialized'):
            return
        
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._background_tasks: set = set()
        self._initialized = True
        logger.info("EventBus initialized")
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to listen for (e.g., "activity_logged")
            handler: Async callable that receives event data
        """
        normalized_handler, handler_name = _resolve_handler(handler)

        self._handlers[event_type].append(normalized_handler)
        logger.debug(f"Subscribed {handler_name} to '{event_type}' events")
    
    async def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit an event to all subscribed handlers.
        
        Handlers are executed in background tasks without blocking.
        Failures in individual handlers are logged but don't affect others.
        
        Args:
            event_type: Type of event being emitted
            data: Event payload (will be passed to handlers)
        """
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for '{event_type}' event")
            return
        
        # Enrich event data with metadata
        enriched_data = {
            **data,
            "_event_type": event_type,
            "_emitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Execute handlers in background
        for handler in handlers:
            task = asyncio.create_task(
                self._execute_handler(event_type, handler, enriched_data)
            )
            # Track background tasks to prevent garbage collection
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        
        logger.debug(f"Emitted '{event_type}' event to {len(handlers)} handler(s)")
    
    async def _execute_handler(
        self, 
        event_type: str, 
        handler: Callable, 
        data: Dict[str, Any]
    ) -> None:
        """
        Execute a single event handler with error isolation.
        
        Args:
            event_type: Type of event
            handler: Handler function to execute
            data: Event data
        """
        try:
            await handler(data)
        except Exception as e:
            handler_name = _get_handler_display_name(handler)
            logger.error(
                f"Error in handler {handler_name} for '{event_type}' event: {e}",
                exc_info=True
            )
    
    async def wait_for_pending_tasks(self, timeout: float = 5.0) -> None:
        """
        Wait for all pending background tasks to complete.
        
        Useful during application shutdown to ensure events are processed.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        if not self._background_tasks:
            return
        
        logger.info(f"Waiting for {len(self._background_tasks)} pending event task(s)...")
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._background_tasks, return_exceptions=True),
                timeout=timeout
            )
            logger.info("All event tasks completed")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for event tasks after {timeout}s")


# ============================================================================
# Global Event Bus Instance
# ============================================================================

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def init_event_handlers() -> None:
    """
    Initialize event bus and auto-register all event handlers.
    
    Automatically discovers and registers all event handlers from the
    app/events/ directory. Each handler must inherit from BaseEventHandler.
    
    Call this during application startup after core services are initialized.
    
    Benefits:
    - No need to manually register each handler
    - New events can be added by just creating a new file in app/events/
    - Scalable and maintainable
    """    
    
    bus = get_event_bus()
    
    # Get the events package path
    events_package_path = Path(app.events.__file__).parent
    
    # Counter for registered handlers
    registered_count = 0
    
    # Auto-discover and import all event handler modules
    for module_info in pkgutil.iter_modules([str(events_package_path)]):
        # Skip base.py and __init__.py
        if module_info.name in ['base', '__init__']:
            continue
        
        try:
            # Import the module
            module = importlib.import_module(f'app.events.{module_info.name}')
            
            # Find all classes that inherit from BaseEventHandler
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a class and inherits from BaseEventHandler
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseEventHandler) and 
                    attr is not BaseEventHandler):
                    
                    # Create instance of the handler
                    handler_instance = attr()
                    
                    # Register with the event bus
                    bus.subscribe(handler_instance.event_type, handler_instance)
                    registered_count += 1
                    
                    logger.info(
                        f"Registered event handler: {attr.__name__} "
                        f"for '{handler_instance.event_type}' events"
                    )
        
        except Exception as e:
            logger.error(f"Failed to load event handler module '{module_info.name}': {e}", exc_info=True)
    
    logger.info(f"✓ Event handlers initialized ({registered_count} handlers registered)")

