"""
Simple in-memory task tracker for background ingestion.
Uses FastAPI's BackgroundTasks - no complex queue needed!
"""

from typing import Dict, Optional, List, Any
from datetime import datetime

from app.jobs import IngestionStatus


class IngestionTask:
    """Tracks a background ingestion task."""
    
    def __init__(self, task_id: str, user_id: Optional[str] = None, params: Optional[Dict] = None):
        self.id = task_id
        self.user_id = user_id
        self.params = params or {}
        
        self.status = IngestionStatus.PENDING
        self.progress = 0.0
        self.progress_message = "Task queued"
        
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    def start(self):
        """Mark task as started."""
        self.status = IngestionStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.progress_message = "Scanning pending directory..."
    
    def update_progress(self, progress: float, message: str):
        """Update progress (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))
        self.progress_message = message
    
    def complete(self, result: Dict[str, Any]):
        """Mark as completed."""
        self.status = IngestionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.progress = 1.0
        self.progress_message = "Ingestion completed"
    
    def fail(self, error: str):
        """Mark as failed."""
        self.status = IngestionStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error
        self.progress_message = f"Failed: {error}"
    
    @property
    def duration(self) -> Optional[float]:
        """Duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status.value,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "params": self.params,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration
        }


class TaskTracker:
    """
    Simple in-memory tracker for background tasks.
    Stores task status/progress for API queries.
    """
    
    def __init__(self, max_history: int = 100):
        self.tasks: Dict[str, IngestionTask] = {}
        self.max_history = max_history
    
    def create_task(self, task_id: str, user_id: Optional[str] = None, params: Optional[Dict] = None) -> IngestionTask:
        """Create and store a new task."""
        task = IngestionTask(task_id, user_id, params)
        self.tasks[task_id] = task
        self._cleanup_old_tasks()
        return task
    
    def get_task(self, task_id: str) -> Optional[IngestionTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def list_tasks(
        self,
        status: Optional[IngestionStatus] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[IngestionTask]:
        """List tasks with optional filters."""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]
        
        # Most recent first
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]
    
    def _cleanup_old_tasks(self):
        """Remove old completed tasks if history limit exceeded."""
        if len(self.tasks) <= self.max_history:
            return
        
        completed_tasks = [
            (tid, t) for tid, t in self.tasks.items()
            if t.status in [IngestionStatus.COMPLETED, IngestionStatus.FAILED]
        ]
        
        # Sort by completion time
        completed_tasks.sort(key=lambda x: x[1].completed_at or x[1].created_at)
        
        # Remove oldest
        to_remove = len(self.tasks) - self.max_history
        for tid, _ in completed_tasks[:to_remove]:
            del self.tasks[tid]


# Global tracker instance
_tracker = TaskTracker()


def get_task_tracker() -> TaskTracker:
    """Get the global task tracker instance."""
    return _tracker
