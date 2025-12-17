"""
Event Bus System

Provides asynchronous event emission and handling for non-critical tasks.
Decouples event producers from consumers, improving response latency.

Events are processed in background tasks without blocking the main request flow.
"""

from typing import Callable, Dict, List, Any, Optional, Coroutine
from collections import defaultdict
import asyncio
from datetime import datetime, timezone

from app.core import get_logger
from app.core.database import get_session
from app.services import activity_logger_service


logger = get_logger(__name__)


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
        self._enabled = True
        self._initialized = True
        logger.info("EventBus initialized")
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to listen for (e.g., "activity_logged")
            handler: Async callable that receives event data
        """
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError(f"Handler {handler.__name__} must be an async function")
        
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to '{event_type}' events")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unsubscribed {handler.__name__} from '{event_type}' events")
            except ValueError:
                logger.warning(f"Handler {handler.__name__} not found for '{event_type}'")
    
    async def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit an event to all subscribed handlers.
        
        Handlers are executed in background tasks without blocking.
        Failures in individual handlers are logged but don't affect others.
        
        Args:
            event_type: Type of event being emitted
            data: Event payload (will be passed to handlers)
        """
        if not self._enabled:
            logger.debug(f"EventBus disabled, skipping '{event_type}' event")
            return
        
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
            # Log error but don't propagate (error isolation)
            logger.error(
                f"Error in handler {handler.__name__} for '{event_type}' event: {e}",
                exc_info=True
            )
    
    def disable(self) -> None:
        """Disable event emission (events will be silently dropped)."""
        self._enabled = False
        logger.warning("EventBus disabled - events will be dropped")
    
    def enable(self) -> None:
        """Enable event emission."""
        self._enabled = True
        logger.info("EventBus enabled")
    
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
    
    def get_handler_count(self, event_type: Optional[str] = None) -> int:
        """
        Get number of registered handlers.
        
        Args:
            event_type: Specific event type, or None for total across all types
        
        Returns:
            Number of registered handlers
        """
        if event_type:
            return len(self._handlers.get(event_type, []))
        return sum(len(handlers) for handlers in self._handlers.values())
    
    def get_event_types(self) -> List[str]:
        """Get list of all event types with registered handlers."""
        return list(self._handlers.keys())


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
    Initialize event bus and register event handlers.
    
    Handlers are imported from event_handlers.py for better modularity.
    Call this during application startup after core services are initialized.
    
    Note: Events don't need to be "declared" - the bus is generic.
    You can emit any event type. However, handlers must be registered
    to actually process events.
    """
    from app.core.event_handlers import handle_activity_log
    
    bus = get_event_bus()
    
    # Register activity logging handler
    bus.subscribe("activity_log", handle_activity_log)
    
    # Add more handler registrations here:
    # from app.core.event_handlers import handle_user_registered
    # bus.subscribe("user_registered", handle_user_registered)
    
    logger.info(f"✓ Event handlers initialized ({bus.get_handler_count()} total handlers)")


async def emit_activity_log(
    user_id: int,
    incident_type: str,
    severity: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    user_clearance_level: Optional[str] = None,
    required_clearance_level: Optional[str] = None,
    access_granted: Optional[bool] = None,
    user_query: Optional[str] = None,
    threat_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Emit an activity log event (non-blocking).
    
    This is the recommended way to log activities without blocking response latency.
    
    Args:
        Same as activity_logger_service.log_activity
    """
    bus = get_event_bus()
    
    event_data = {
        "user_id": user_id,
        "incident_type": incident_type,
        "severity": severity,
        "description": description,
        "details": details,
        "user_clearance_level": user_clearance_level,
        "required_clearance_level": required_clearance_level,
        "access_granted": access_granted,
        "user_query": user_query,
        "threat_type": threat_type,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    
    await bus.emit("activity_log", event_data)
