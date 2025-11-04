"""
Background ingestion API endpoints.

Thin HTTP layer over IngestionService.
All business logic is in app.services.ingestion_service,
allowing direct programmatic access without HTTP.
"""

from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.core import get_logger
from app.jobs import IngestionStatus
from app.services.ingestion_service import (
    get_ingestion_service,
    IngestionConfig
)


logger = get_logger(__name__)
router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/start")
async def start_ingestion(
    background_tasks: BackgroundTasks,
    recursive: bool = True,
    file_types: Optional[List[str]] = Query(None, description="File extensions to process (e.g., pdf, txt, json)"),
    user_id: Optional[str] = None
):
    """
    Start background ingestion of all documents in pending directory.
    
    Clean 3-step process:
    1. Load documents from pending/
    2. Chunk using LangChain splitters
    3. Store with vector_store.add_documents() (LangChain handles embeddings)
    
    This endpoint returns immediately with a task ID.
    Use GET /ingestion/status/{task_id} to check progress.
    
    Args:
        recursive: Search subdirectories in pending folder
        file_types: Optional list of file extensions to process
        user_id: Optional user ID for tracking
    
    Returns:
        Task ID and initial status
        
    Examples:
        # Ingest all documents
        POST /ingestion/start
        
        # Ingest only PDF files
        POST /ingestion/start?file_types=pdf
        
        # Ingest JSON and CSV files
        POST /ingestion/start?file_types=json&file_types=csv
    """
    service = get_ingestion_service()
    
    # Create ingestion config
    config = IngestionConfig(
        recursive=recursive,
        file_types=file_types,
        user_id=user_id
    )
    
    # Start background job (creates tracked task)
    task = service.start_background_job(config)
    
    # Add to FastAPI background tasks
    background_tasks.add_task(
        service.run_background_task,
        task=task,
        recursive=recursive,
        file_types=file_types
    )
    
    logger.info(f"Ingestion task {task.id} queued")
    
    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Ingestion started in background. Use GET /ingestion/status/{task_id} to check progress."
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status and progress of an ingestion task.
    
    Args:
        task_id: Task ID returned from POST /ingestion/start
        
    Returns:
        Task details including status, progress, and results (if completed)
    """
    service = get_ingestion_service()
    task = service.get_task_status(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task.to_dict()


@router.get("/tasks")
async def list_tasks(
    status: Optional[IngestionStatus] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tasks to return")
):
    """
    List ingestion tasks with optional filters.
    
    Args:
        status: Filter by task status (pending, running, completed, failed)
        user_id: Filter by user ID
        limit: Maximum number of tasks
        
    Returns:
        List of tasks (most recent first)
    """
    service = get_ingestion_service()
    tasks = service.list_tasks(status=status, user_id=user_id, limit=limit)
    
    return {
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }

