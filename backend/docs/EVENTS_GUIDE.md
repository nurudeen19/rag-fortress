# Events System Documentation

## Overview

The refactored event system provides a scalable, modular architecture for handling asynchronous events. Events are processed in the background without blocking the main request flow.

## Architecture

```
app/
├── core/
│   └── events.py          # EventBus class (manages all events)
└── events/
    ├── __init__.py        # Package initialization
    ├── base.py            # BaseEventHandler class
    ├── activity_log_event.py    # Activity logging handler
    ├── semantic_cache_event.py  # Semantic cache storage handler
    ├── message_save_event.py    # Background message persistence (latency optimization)
    └── [your_event].py    # Add more events here
```

## Key Features

✅ **Scalable**: Add new events by creating a new file  
✅ **Independent**: Each event handler is self-contained  
✅ **Auto-discovery**: Handlers are automatically registered  
✅ **Non-blocking**: Events process in the background  
✅ **Error isolation**: Handler failures don't affect other handlers  
✅ **Simple usage**: Just emit events and continue

## Creating a New Event

### Step 1: Create Event Handler File

Create a new file in `app/events/` (e.g., `my_event.py`):

```python
from typing import Dict, Any
from app.events.base import BaseEventHandler
from app.core import get_logger

logger = get_logger(__name__)


class MyEventHandler(BaseEventHandler):
    """Handles my custom events."""
    
    @property
    def event_type(self) -> str:
        return "my_event"  # Unique event identifier
    
    async def handle(self, event_data: Dict[str, Any]) -> None:
        """Process the event."""
        try:
            # Extract data
            user_id = event_data["user_id"]
            action = event_data["action"]
            
            # Do your processing
            logger.info(f"Processing my_event for user {user_id}: {action}")
            
            # Database operations if needed
            # async with get_session() as session:
            #     await my_service.do_something(session, user_id)
            #     await session.commit()
        
        except Exception as e:
            logger.error(f"Failed to process my_event: {e}", exc_info=True)
```

### Step 2: That's It!

The event handler will be **automatically discovered and registered** on application startup. No manual registration needed!

### Step 3: Emit Events from Services

```python
from app.core.events import get_event_bus

async def my_service_function(user_id: int):
    bus = get_event_bus()
    
    # Do your main work
    result = await some_operation()
    
    # Emit event (non-blocking)
    await bus.emit("my_event", {
        "user_id": user_id,
        "action": "something_happened",
        "details": result
    })
    
    # Return immediately - event processes in background
    return result
```

## Existing Events

### 1. Activity Log Event

**Event Type**: `activity_log`

**Purpose**: Log security and audit activities asynchronously

**Required Fields**:
- `user_id`: int
- `incident_type`: str
- `severity`: str
- `description`: str

**Optional Fields**:
- `details`: Dict
- `user_clearance_level`: str
- `required_clearance_level`: str
- `access_granted`: bool
- `user_query`: str
- `threat_type`: str
- `ip_address`: str
- `user_agent`: str

**Example Usage**:
```python
from app.core.events import get_event_bus

bus = get_event_bus()
await bus.emit("activity_log", {
    "user_id": 1,
    "incident_type": "UNAUTHORIZED_ACCESS",
    "severity": "HIGH",
    "description": "User attempted to access restricted resource",
    "ip_address": "192.168.1.1"
})
```

## Best Practices

### 1. Make Handlers Idempotent

Events may be processed more than once in failure scenarios. Design handlers to be idempotent when possible.

### 2. Handle Your Own Sessions

Each handler should create its own database session:

```python
async def handle(self, event_data: Dict[str, Any]) -> None:
    async with get_session() as session:
        await my_service.do_work(session, ...)
        await session.commit()
```

### 3. Don't Let Errors Propagate

Always catch and log exceptions in your handler:

```python
async def handle(self, event_data: Dict[str, Any]) -> None:
    try:
        # Your logic here
        pass
    except Exception as e:
        logger.error(f"Failed to process event: {e}", exc_info=True)
```

### 4. Validate Required Fields

Check for required fields and handle missing data gracefully:

```python
try:
    user_id = event_data["user_id"]
except KeyError as e:
    logger.error(f"Missing required field: {e}")
    return
```

### 5. Keep Events Lightweight

Events are for non-critical, background tasks. Don't use them for:
- Critical operations that must complete before returning
- Operations that need immediate feedback
- Operations where order is critical

## Event Bus API

### Get Event Bus Instance
```python
from app.core.events import get_event_bus

bus = get_event_bus()
```

### Emit Event
```python
await bus.emit("event_type", {
    "field1": "value1",
    "field2": "value2"
})
```

### Check Handler Count
```python
count = bus.get_handler_count()  # All handlers
count = bus.get_handler_count("my_event")  # Specific event
```

### Get Event Types
```python
event_types = bus.get_event_types()
# Returns: ["activity_log", "my_event", ...]
```

### Disable/Enable Event Bus
```python
bus.disable()  # Events will be dropped
bus.enable()   # Resume event processing
```

## Migration from Old System

If you have code using the old `emit_activity_log()` function, it still works but is deprecated:

```python
# OLD (deprecated but still works)
from app.core.events import emit_activity_log
await emit_activity_log(user_id=1, ...)

# NEW (recommended)
from app.core.events import get_event_bus
bus = get_event_bus()
await bus.emit("activity_log", {"user_id": 1, ...})
```

## Troubleshooting

### Event not processing?

1. Check if handler is registered:
   ```python
   bus = get_event_bus()
   print(bus.get_event_types())  # Should include your event type
   ```

2. Check logs for handler registration:
   ```
   INFO: Registered event handler: MyEventHandler for 'my_event' events
   ```

3. Check for errors in handler:
   ```
   ERROR: Error in MyEventHandler for 'my_event' event: ...
   ```

### Handler not auto-discovered?

1. Ensure file is in `app/events/` directory
2. Ensure class inherits from `BaseEventHandler`
3. Ensure `event_type` property is implemented
4. Ensure `handle()` method is implemented
5. Check for import errors in the handler module

## Performance Considerations

- Events are processed in background asyncio tasks
- Multiple events can process concurrently
- Handlers don't block the main request
- Failed handlers don't affect other handlers
- Events include metadata (`_event_type`, `_emitted_at`)

## Example: Complete Event Workflow

```python
# 1. Define event handler (app/events/order_created_event.py)
class OrderCreatedEvent(BaseEventHandler):
    @property
    def event_type(self) -> str:
        return "order_created"
    
    async def handle(self, event_data: Dict[str, Any]) -> None:
        order_id = event_data["order_id"]
        # Send confirmation email
        # Update inventory
        # Notify warehouse
        logger.info(f"Order {order_id} processed")

# 2. Emit from service (app/services/order_service.py)
async def create_order(db, user_id: int, items: List):
    order = await db_create_order(db, user_id, items)
    await db.commit()
    
    bus = get_event_bus()
    await bus.emit("order_created", {
        "order_id": order.id,
        "user_id": user_id,
        "total": order.total
    })
    
    return order  # Returns immediately

# 3. Event processes in background automatically
```

## Summary

The new event system is:
- **Simple**: Just create a file and emit events
- **Scalable**: Add events without changing existing code
- **Maintainable**: Each event is independent
- **Reliable**: Error isolation and graceful degradation
- **Fast**: Non-blocking background processing

For more examples, see `app/events/EXAMPLE_NEW_EVENT.py`.
