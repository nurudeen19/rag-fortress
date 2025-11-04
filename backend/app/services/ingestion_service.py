"""
Ingestion Service - Programmatic API for document ingestion.

Provides both synchronous and async ingestion methods that can be:
1. Called directly from Python code
2. Used by background jobs via FastAPI BackgroundTasks
3. Invoked from HTTP endpoints

Clean separation: service logic vs HTTP/job wiring.
"""

import uuid
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from app.core import get_logger
from app.jobs.tracker import get_task_tracker, IngestionTask
from app.services.vector_store import DocumentStorageService


logger = get_logger(__name__)


@dataclass
class IngestionConfig:
    """Configuration for an ingestion job."""
    recursive: bool = True
    file_types: Optional[List[str]] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    task_id: str
    total: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.successful / self.total * 100) if self.total > 0 else 0.0


class IngestionService:
    """
    Service for document ingestion operations.
    
    Provides both direct and background execution modes.
    
    Usage:
        # Direct synchronous call
        service = IngestionService()
        result = service.ingest_sync(recursive=True)
        
        # Background job with task tracking
        task = service.start_background_job(
            config=IngestionConfig(recursive=True, file_types=['pdf'])
        )
        
        # Check status later
        status = service.get_task_status(task.id)
    """
    
    def __init__(self):
        """Initialize ingestion service."""
        self.tracker = get_task_tracker()
        self.logger = logger
    
    def ingest_sync(
        self,
        recursive: bool = True,
        file_types: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> IngestionResult:
        """
        Run ingestion synchronously (blocks until complete).
        
        Use this when:
        - Running from CLI/scripts
        - Testing
        - Startup initialization
        - Jobs where blocking is acceptable
        
        Args:
            recursive: Search subdirectories in pending folder
            file_types: Optional list of file extensions to process
            progress_callback: Optional callback(progress: float, message: str)
            
        Returns:
            IngestionResult with complete details
            
        Example:
            service = IngestionService()
            result = service.ingest_sync(recursive=True, file_types=['pdf', 'txt'])
            print(f"Ingested {result.successful}/{result.total} documents")
        """
        task_id = str(uuid.uuid4())
        self.logger.info(f"Starting synchronous ingestion (task_id: {task_id})")
        
        try:
            # Progress callback helper
            def report_progress(progress: float, message: str):
                if progress_callback:
                    progress_callback(progress, message)
                self.logger.info(f"[{task_id}] {message} ({progress:.0%})")
            
            report_progress(0.0, "Initializing storage service")
            
            # Initialize storage service (reuses embeddings from startup)
            storage = DocumentStorageService()
            
            report_progress(0.1, "Starting document ingestion")
            
            # Run ingestion: load → chunk → store
            results = storage.ingest_from_pending(
                recursive=recursive,
                file_types=file_types
            )
            
            report_progress(1.0, "Ingestion complete")
            
            # Compile results
            total = len(results)
            successful = sum(1 for r in results if r.success)
            failed = total - successful
            
            result_data = [
                {
                    "document": r.document_path,
                    "success": r.success,
                    "chunks": r.chunks_count if r.success else 0,
                    "error": r.error if not r.success else None
                }
                for r in results
            ]
            
            self.logger.info(
                f"Synchronous ingestion completed: {successful}/{total} documents succeeded"
            )
            
            return IngestionResult(
                task_id=task_id,
                total=total,
                successful=successful,
                failed=failed,
                results=result_data
            )
        
        except Exception as e:
            self.logger.error(f"Synchronous ingestion failed: {e}", exc_info=True)
            raise
    
    def start_background_job(
        self,
        config: IngestionConfig
    ) -> IngestionTask:
        """
        Start ingestion as a background job with task tracking.
        
        Use this when:
        - Called from HTTP endpoints (non-blocking)
        - Long-running operations
        - Need progress tracking
        
        Args:
            config: Ingestion configuration
            
        Returns:
            IngestionTask that can be used to track progress
            
        Example:
            service = IngestionService()
            config = IngestionConfig(recursive=True, file_types=['pdf'])
            task = service.start_background_job(config)
            
            # Later, check status
            if task.is_completed():
                print(f"Success: {task.result}")
        """
        # Generate task ID if not provided
        task_id = config.task_id or str(uuid.uuid4())
        
        # Create tracked task
        task = self.tracker.create_task(
            task_id=task_id,
            user_id=config.user_id,
            params={
                "recursive": config.recursive,
                "file_types": config.file_types
            }
        )
        
        self.logger.info(f"Background ingestion job created: {task_id}")
        
        return task
    
    async def run_background_task(
        self,
        task: IngestionTask,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ):
        """
        Execute the background task (called by FastAPI BackgroundTasks).
        
        This is the worker function that actually runs in background.
        Typically not called directly - use start_background_job() instead.
        
        Args:
            task: Task to execute
            recursive: Search subdirectories
            file_types: File extensions to process
        """
        try:
            task.start()
            self.logger.info(f"Executing background task {task.id}")
            
            # Initialize storage service
            storage = DocumentStorageService()
            
            task.update_progress(0.1, "Storage service initialized")
            
            # Run ingestion
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
            self.logger.info(
                f"Background task {task.id} completed: {successful}/{total} documents"
            )
        
        except Exception as e:
            error_msg = str(e)
            task.fail(error_msg)
            self.logger.error(f"Background task {task.id} failed: {error_msg}", exc_info=True)
    
    def get_task_status(self, task_id: str) -> Optional[IngestionTask]:
        """
        Get status of a tracked ingestion task.
        
        Args:
            task_id: Task ID
            
        Returns:
            IngestionTask or None if not found
        """
        return self.tracker.get_task(task_id)
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[IngestionTask]:
        """
        List ingestion tasks with optional filters.
        
        Args:
            status: Filter by status (pending, running, completed, failed)
            user_id: Filter by user ID
            limit: Maximum number of tasks
            
        Returns:
            List of tasks (most recent first)
        """
        return self.tracker.list_tasks(
            status=status,
            user_id=user_id,
            limit=limit
        )


# Global service instance (singleton pattern)
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """
    Get the global ingestion service instance.
    
    Returns:
        IngestionService singleton
    """
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service
