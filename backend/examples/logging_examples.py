"""
Example usage of the logging system
"""

# Example 1: Using the default logger
from app.core import default_logger

default_logger.info("Application started")
default_logger.debug("Debug information")
default_logger.warning("Warning message")
default_logger.error("Error occurred")


# Example 2: Get a module-specific logger
from app.core import get_logger

logger = get_logger(__name__)
logger.info("Module-specific log message")


# Example 3: In a service class
class RAGService:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def process_query(self, query: str):
        self.logger.info(f"Processing query: {query}")
        
        try:
            # Process query...
            result = "response"
            self.logger.debug(f"Query result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error processing query: {e}", exc_info=True)
            raise


# Example 4: Structured logging with extra context
logger = get_logger(__name__)

# Add context to log messages
logger.info(
    "User query processed",
    extra={
        'user_id': '123',
        'query_length': 50,
        'processing_time': 1.23
    }
)


# Example 5: Logging with exception traceback
try:
    1 / 0
except Exception as e:
    logger.error("Division error occurred", exc_info=True)


# Example 6: Custom log levels
logger.setLevel('DEBUG')  # Temporarily change level


# Example 7: In FastAPI route
from fastapi import APIRouter
from app.core import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/items/{item_id}")
async def get_item(item_id: int):
    logger.info(f"Fetching item: {item_id}")
    
    try:
        # Fetch item...
        item = {"id": item_id, "name": "Item"}
        logger.debug(f"Item found: {item}")
        return item
    except Exception as e:
        logger.error(f"Error fetching item {item_id}: {e}", exc_info=True)
        raise


# Example 8: Performance logging
import time

logger = get_logger(__name__)

def slow_operation():
    start_time = time.time()
    logger.info("Starting slow operation")
    
    # Do work...
    time.sleep(2)
    
    duration = time.time() - start_time
    logger.info(f"Slow operation completed in {duration:.2f}s")


# Example 9: Conditional logging based on environment
from app.config import settings

if settings.DEBUG:
    logger.debug("Detailed debug information only in debug mode")


# Example 10: Logging with correlation IDs (for request tracking)
import uuid

def process_request(request_data):
    correlation_id = str(uuid.uuid4())
    logger = get_logger(__name__)
    
    logger.info(f"[{correlation_id}] Processing request")
    
    try:
        # Process...
        logger.info(f"[{correlation_id}] Request processed successfully")
    except Exception as e:
        logger.error(f"[{correlation_id}] Request failed: {e}", exc_info=True)
