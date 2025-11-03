"""
Background ingestion API endpoints.
Uses FastAPI's BackgroundTasks for simple async execution.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.core import get_logger
from app.jobs import IngestionStatus
from app.jobs.tracker import get_task_tracker, IngestionTask
from app.services.document_ingestion import DocumentIngestionService


logger = get_logger(__name__)
router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


async def _run_ingestion_task(
    task: IngestionTask,
    recursive: bool = True,
    file_types: Optional[List[str]] = None,
    fields_to_keep: Optional[List[str]] = None,
    json_flatten: bool = True
):
    """
    Background task that runs the actual ingestion.
    This is executed by FastAPI's BackgroundTasks.
    """
    ingestion_service = None
    
    try:
        task.start()
        logger.info(f"Starting ingestion task {task.id}")
        
        # Initialize service
        ingestion_service = DocumentIngestionService()
        await ingestion_service.initialize()
        
        task.update_progress(0.1, "Service initialized")
        
        # Run ingestion from pending directory
        results = await ingestion_service.ingest_from_pending(
            recursive=recursive,
            file_types=file_types,
            fields_to_keep=fields_to_keep,
            json_flatten=json_flatten
        )
        
        # Compile results
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        result_data = {
            "total": total,
            "successful": successful,
            "failed": failed,
            "results": [
                {
                    "document": r.document_path,
                    "success": r.success,
                    "chunks": r.chunks_count if r.success else 0,
                    "error": r.error_message if not r.success else None
                }
                for r in results
            ]
        }
        
        task.complete(result_data)
        logger.info(f"Task {task.id} completed: {successful}/{total} documents ingested")
    
    except Exception as e:
        error_msg = str(e)
        task.fail(error_msg)
        logger.error(f"Task {task.id} failed: {error_msg}", exc_info=True)
    
    finally:
        if ingestion_service:
            await ingestion_service.cleanup()


@router.post("/start")
async def start_ingestion(
    background_tasks: BackgroundTasks,
    recursive: bool = True,
    file_types: Optional[List[str]] = Query(None, description="File extensions to process (e.g., pdf, txt, json)"),
    fields_to_keep: Optional[List[str]] = Query(None, description="Fields to keep for structured data (JSON, CSV, XLSX)"),
    json_flatten: bool = Query(True, description="Flatten nested JSON objects"),
    user_id: Optional[str] = None
):
    """
    Start background ingestion of all documents in pending directory.
    
    This endpoint returns immediately with a task ID.
    Use GET /ingestion/status/{task_id} to check progress.
    
    Args:
        recursive: Search subdirectories in pending folder
        file_types: Optional list of file extensions to process
        fields_to_keep: Optional list of fields/columns to keep for structured formats
        json_flatten: Whether to flatten JSON nested objects
        user_id: Optional user ID for tracking
    
    Returns:
        Task ID and initial status
        
    Examples:
        # Ingest all documents
        POST /ingestion/start
        
        # Ingest only JSON files with specific fields
        POST /ingestion/start?file_types=json&fields_to_keep=name&fields_to_keep=email
        
        # Ingest CSV files with column filtering
        POST /ingestion/start?file_types=csv&fields_to_keep=Name&fields_to_keep=Department
    """
    tracker = get_task_tracker()
    
    # Create task
    task_id = str(uuid.uuid4())
    task = tracker.create_task(
        task_id=task_id,
        user_id=user_id,
        params={
            "recursive": recursive,
            "file_types": file_types,
            "fields_to_keep": fields_to_keep,
            "json_flatten": json_flatten
        }
    )
    
    # Add to background tasks (FastAPI handles execution)
    background_tasks.add_task(
        _run_ingestion_task,
        task=task,
        recursive=recursive,
        file_types=file_types,
        fields_to_keep=fields_to_keep,
        json_flatten=json_flatten
    )
    
    logger.info(f"Ingestion task {task_id} queued")
    
    return {
        "task_id": task_id,
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
    tracker = get_task_tracker()
    task = tracker.get_task(task_id)
    
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
    tracker = get_task_tracker()
    tasks = tracker.list_tasks(status=status, user_id=user_id, limit=limit)
    
    return {
        "count": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
    }

