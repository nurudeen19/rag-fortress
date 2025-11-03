"""
Background ingestion API endpoints.
Uses FastAPI's BackgroundTasks with clean LangChain-based architecture.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.core import get_logger
from app.jobs import IngestionStatus
from app.jobs.tracker import get_task_tracker, IngestionTask
from app.services.vector_store import DocumentStorageService


logger = get_logger(__name__)
router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


async def _run_ingestion_task(
    task: IngestionTask,
    recursive: bool = True,
    file_types: Optional[List[str]] = None
):
    """
    Background task that runs the actual ingestion.
    Clean 3-step process using LangChain patterns.
    """
    try:
        task.start()
        logger.info(f"Starting ingestion task {task.id}")
        
        # Initialize storage service (reuses embeddings from startup)
        storage = DocumentStorageService()
        
        task.update_progress(0.1, "Storage service initialized")
        
        # Run ingestion: load → chunk → store
        # LangChain handles embedding + vector storage
        results = storage.ingest_from_pending(
            recursive=recursive,
            file_types=file_types
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
                    "error": r.error if not r.success else None
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
    tracker = get_task_tracker()
    
    # Create task
    task_id = str(uuid.uuid4())
    task = tracker.create_task(
        task_id=task_id,
        user_id=user_id,
        params={
            "recursive": recursive,
            "file_types": file_types
        }
    )
    
    # Add to background tasks (FastAPI handles execution)
    background_tasks.add_task(
        _run_ingestion_task,
        task=task,
        recursive=recursive,
        file_types=file_types
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

