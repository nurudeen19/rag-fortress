"""
System Diagnostics Routes - Authenticated health checks for system components.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

from app.config.settings import settings
from app.services.diagnostics import get_diagnostics_service
from app.core import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


class DiagnosticsRequest(BaseModel):
    """Request model for diagnostics endpoint."""
    diagnostic_key: str


@router.post("/run", summary="Run system diagnostics", description="Run comprehensive health checks on all system components. Requires diagnostic key.", include_in_schema=False)
async def run_diagnostics(
    request: DiagnosticsRequest
) -> dict:
    """
    Run all registered diagnostic tests on system components.
    
    This endpoint performs comprehensive health checks including:
    - Database connection and query tests
    - Cache (Redis) operations tests
    - Vector store connectivity tests
    
    Requires a valid diagnostic key for security.
    
    Args:
        request: Contains the diagnostic_key for authentication
        
    Returns:
        Comprehensive diagnostics report with test results
        
    Raises:
        HTTPException: If diagnostic key is invalid or tests fail
    """
    # Validate diagnostic key
    expected_key = settings.app_settings.DIAGNOSTIC_KEY
    
    if not expected_key:
        logger.error("DIAGNOSTIC_KEY not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Diagnostics endpoint not properly configured"
        )
    
    if request.diagnostic_key != expected_key:
        logger.warning("Invalid diagnostic key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid diagnostic key"
        )
    
    # Run diagnostics
    logger.info("Running system diagnostics...")
    
    try:
        diagnostics_service = get_diagnostics_service()
        results = await diagnostics_service.run_all_diagnostics()
        
        logger.info(
            f"Diagnostics complete: {results['overall_status']} - "
            f"{results['tests_passed']}/{results['tests_run']} passed"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Diagnostics execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnostics execution failed: {str(e)}"
        )


@router.get("/info", summary="Diagnostics endpoint information", include_in_schema=False)
async def diagnostics_info() -> dict:
    """
    Get information about the diagnostics endpoint.
    
    Returns:
        Information about available diagnostic tests
    """
    diagnostics_service = get_diagnostics_service()
    
    return {
        "endpoint": "/api/v1/diagnostics/run",
        "method": "POST",
        "authentication": "Requires diagnostic_key in request body",
        "tests_available": len(diagnostics_service.test_registry),
        "test_names": [
            method.__name__.replace("_test_", "") 
            for method in diagnostics_service.test_registry
        ],
        "description": "Comprehensive health checks for database, cache, vector store, and other components"
    }
