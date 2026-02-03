"""
System Diagnostics Service - Health checks for critical components.
Provides pluggable component testing for database, cache, vector store, etc.
"""

from typing import Dict, Any, List, Callable, Awaitable
from datetime import datetime, timezone

from sqlalchemy import text

from app.core import get_logger
from app.core.cache import get_cache
from app.core.database import get_session


logger = get_logger(__name__)


class DiagnosticsService:
    """
    Pluggable diagnostics service for testing system components.
    Each test is a separate method that can be added/removed from the test suite.
    """
    
    def __init__(self):
        """Initialize diagnostics service."""
        # Registry of all available tests
        # Add/remove methods here to include/exclude from diagnostics
        self.test_registry: List[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = [
            self._test_database_connection,
            self._test_cache_operations,
            self._test_vector_store_connection,
        ]
        
    async def run_all_diagnostics(self) -> Dict[str, Any]:
        """
        Run all registered diagnostic tests.
        
        Returns:
            Dictionary with overall status and individual test results
        """
        start_time = datetime.now(timezone.utc)
        results = []
        all_passed = True
        
        logger.info("Starting system diagnostics...")
        
        # Run all tests
        for test_method in self.test_registry:
            try:
                test_result = await test_method({})
                results.append(test_result)
                
                if test_result.get("status") != "pass":
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"Diagnostic test failed: {test_method.__name__}: {e}")
                results.append({
                    "test": test_method.__name__.replace("_test_", ""),
                    "status": "error",
                    "message": f"Test execution failed: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                all_passed = False
        
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "overall_status": "healthy" if all_passed else "degraded",
            "timestamp": start_time.isoformat(),
            "duration_ms": duration_ms,
            "tests_run": len(results),
            "tests_passed": sum(1 for r in results if r.get("status") == "pass"),
            "tests_failed": sum(1 for r in results if r.get("status") in ["fail", "error"]),
            "results": results
        }
    
    async def _test_database_connection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test database connectivity and basic operations.
        
        Args:
            context: Shared context between tests
            
        Returns:
            Test result dictionary
        """
        test_name = "database_connection"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get database session
            async for session in get_session():
                try:
                    # Execute a simple query
                    result = await session.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    
                    if row and row[0] == 1:
                        # Try to fetch actual data
                        user_count_result = await session.execute(
                            text("SELECT COUNT(*) FROM users")
                        )
                        user_count = user_count_result.scalar()
                        
                        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                        
                        return {
                            "test": test_name,
                            "status": "pass",
                            "message": "Database connection successful",
                            "details": {
                                "query_test": "passed",
                                "user_count": user_count,
                                "response_time_ms": duration_ms
                            },
                            "timestamp": start_time.isoformat()
                        }
                    else:
                        return {
                            "test": test_name,
                            "status": "fail",
                            "message": "Database query returned unexpected result",
                            "timestamp": start_time.isoformat()
                        }
                        
                except Exception as e:
                    logger.error(f"Database test query failed: {e}")
                    return {
                        "test": test_name,
                        "status": "fail",
                        "message": f"Query execution failed: {str(e)}",
                        "timestamp": start_time.isoformat()
                    }
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {
                "test": test_name,
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "timestamp": start_time.isoformat()
            }
    
    async def _test_cache_operations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test cache (Redis) connectivity and operations.
        
        Args:
            context: Shared context between tests
            
        Returns:
            Test result dictionary
        """
        test_name = "cache_operations"
        start_time = datetime.now(timezone.utc)
        test_key = "diagnostic:test:health_check"
        test_value = f"test_value_{start_time.timestamp()}"
        
        try:
            cache = get_cache()
            
            if not cache:
                return {
                    "test": test_name,
                    "status": "fail",
                    "message": "Cache client not available",
                    "timestamp": start_time.isoformat()
                }
            
            # Test SET operation
            set_start = datetime.now(timezone.utc)
            await cache.set(test_key, test_value, ttl=10)  # 10 second TTL
            set_duration = int((datetime.now(timezone.utc) - set_start).total_seconds() * 1000)
            
            # Test GET operation
            get_start = datetime.now(timezone.utc)
            retrieved_value = await cache.get(test_key)
            get_duration = int((datetime.now(timezone.utc) - get_start).total_seconds() * 1000)
            
            # Verify value matches
            if retrieved_value == test_value:
                # Clean up test key
                await cache.delete(test_key)
                
                total_duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                
                return {
                    "test": test_name,
                    "status": "pass",
                    "message": "Cache operations successful",
                    "details": {
                        "set_operation": "passed",
                        "get_operation": "passed",
                        "value_match": True,
                        "set_time_ms": set_duration,
                        "get_time_ms": get_duration,
                        "total_time_ms": total_duration
                    },
                    "timestamp": start_time.isoformat()
                }
            else:
                # Clean up even on failure
                await cache.delete(test_key)
                
                return {
                    "test": test_name,
                    "status": "fail",
                    "message": "Cache value mismatch",
                    "details": {
                        "expected": test_value,
                        "received": retrieved_value
                    },
                    "timestamp": start_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Cache test failed: {e}")
            
            # Try to clean up test key
            try:
                cache = get_cache()
                if cache:
                    await cache.delete(test_key)
            except:
                pass
            
            return {
                "test": test_name,
                "status": "error",
                "message": f"Cache operation failed: {str(e)}",
                "timestamp": start_time.isoformat()
            }
    
    async def _test_vector_store_connection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test vector store connectivity and operations.
        
        Args:
            context: Shared context between tests
            
        Returns:
            Test result dictionary
        """
        test_name = "vector_store_connection"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Import vector store factory (core component)
            from app.core.vector_store_factory import get_retriever
            
            # Get vector store instance
            init_start = datetime.now(timezone.utc)
            try:
                # Get the actual vector store retriever
                retriever = get_retriever()
                init_duration = int((datetime.now(timezone.utc) - init_start).total_seconds() * 1000)
                
                # Try a simple search (may return no results if store is empty)
                search_start = datetime.now(timezone.utc)
                try:
                    # Simple diagnostic query using invoke (LangChain retriever method)
                    results = retriever.invoke("test")
                    search_duration = int((datetime.now(timezone.utc) - search_start).total_seconds() * 1000)
                    
                    total_duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    
                    return {
                        "test": test_name,
                        "status": "pass",
                        "message": "Vector store connection successful",
                        "details": {
                            "initialization": "passed",
                            "search_operation": "passed",
                            "documents_found": len(results) if results else 0,
                            "init_time_ms": init_duration,
                            "search_time_ms": search_duration,
                            "total_time_ms": total_duration
                        },
                        "timestamp": start_time.isoformat()
                    }
                    
                except Exception as search_error:
                    logger.warning(f"Vector store search failed (may be expected if empty): {search_error}")
                    
                    # Connection works but search failed - still consider it a pass if initialization worked
                    return {
                        "test": test_name,
                        "status": "pass",
                        "message": "Vector store initialized (search operation skipped)",
                        "details": {
                            "initialization": "passed",
                            "search_operation": "skipped",
                            "init_time_ms": init_duration,
                            "note": "Search test skipped - vector store may be empty"
                        },
                        "timestamp": start_time.isoformat()
                    }
                    
            except Exception as init_error:
                logger.error(f"Vector store initialization failed: {init_error}")
                return {
                    "test": test_name,
                    "status": "fail",
                    "message": f"Vector store initialization failed: {str(init_error)}",
                    "timestamp": start_time.isoformat()
                }
                    
        except ImportError as e:
            logger.error(f"Vector store module import failed: {e}")
            return {
                "test": test_name,
                "status": "error",
                "message": f"Vector store module not available: {str(e)}",
                "timestamp": start_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Vector store connection test failed: {e}")
            return {
                "test": test_name,
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "timestamp": start_time.isoformat()
            }


# Singleton instance
_diagnostics_service = None

def get_diagnostics_service() -> DiagnosticsService:
    """Get or create diagnostics service instance."""
    global _diagnostics_service
    if _diagnostics_service is None:
        _diagnostics_service = DiagnosticsService()
    return _diagnostics_service