#!/usr/bin/env python3
"""
Example: Programmatic ingestion without HTTP.

Shows how to call ingestion service directly from Python.
Useful for:
- CLI tools
- Scheduled jobs (cron)
- Testing
- Admin scripts
- Startup initialization
"""

import sys
import os

# Add backend to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services.ingestion_service import get_ingestion_service, IngestionConfig


def example_1_sync_ingestion():
    """Example 1: Simple synchronous ingestion."""
    print("=" * 60)
    print("Example 1: Synchronous Ingestion")
    print("=" * 60)
    
    service = get_ingestion_service()
    
    # Run synchronous ingestion (blocks until complete)
    result = service.ingest_sync(
        recursive=True,
        file_types=['pdf', 'txt', 'md']
    )
    
    print(f"\nResults:")
    print(f"  Total: {result.total}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Success rate: {result.success_rate:.1f}%")
    
    if result.failed > 0:
        print("\nFailed documents:")
        for r in result.results:
            if not r['success']:
                print(f"  - {r['document']}: {r['error']}")


def example_2_with_progress_callback():
    """Example 2: Sync ingestion with progress callback."""
    print("\n" + "=" * 60)
    print("Example 2: With Progress Callback")
    print("=" * 60)
    
    service = get_ingestion_service()
    
    def on_progress(progress: float, message: str):
        """Called during ingestion to report progress."""
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"\r[{bar}] {progress:.0%} - {message}", end="", flush=True)
    
    result = service.ingest_sync(
        recursive=True,
        progress_callback=on_progress
    )
    
    print(f"\n\nCompleted: {result.successful}/{result.total} documents")


def example_3_background_job_without_http():
    """Example 3: Background job without FastAPI."""
    print("\n" + "=" * 60)
    print("Example 3: Background Job (Manual Execution)")
    print("=" * 60)
    
    service = get_ingestion_service()
    
    # Create config
    config = IngestionConfig(
        recursive=True,
        file_types=['pdf'],
        user_id='admin'
    )
    
    # Start job (creates task for tracking)
    task = service.start_background_job(config)
    print(f"Task created: {task.id}")
    print(f"Status: {task.status.value}")
    
    # In a real background job, this would be called by a worker
    # For demo, we'll run it synchronously here
    import asyncio
    asyncio.run(service.run_background_task(
        task=task,
        recursive=config.recursive,
        file_types=config.file_types
    ))
    
    # Check final status
    final_task = service.get_task_status(task.id)
    print(f"\nFinal status: {final_task.status.value}")
    if final_task.result:
        print(f"Documents: {final_task.result['successful']}/{final_task.result['total']}")


def example_4_list_tasks():
    """Example 4: List recent ingestion tasks."""
    print("\n" + "=" * 60)
    print("Example 4: List Recent Tasks")
    print("=" * 60)
    
    service = get_ingestion_service()
    
    # List all tasks
    tasks = service.list_tasks(limit=5)
    
    print(f"\nFound {len(tasks)} recent tasks:")
    for task in tasks:
        status_emoji = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(task.status.value, '❓')
        
        print(f"\n{status_emoji} Task {task.id}")
        print(f"   Status: {task.status.value}")
        print(f"   Created: {task.created_at}")
        if task.completed_at:
            duration = (task.completed_at - task.created_at).total_seconds()
            print(f"   Duration: {duration:.1f}s")
        if task.result:
            print(f"   Result: {task.result.get('successful', 0)}/{task.result.get('total', 0)} docs")


def main():
    """Run all examples."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Programmatic ingestion examples")
    parser.add_argument(
        "--example",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific example (1-4), or all if not specified"
    )
    
    args = parser.parse_args()
    
    if args.example == 1:
        example_1_sync_ingestion()
    elif args.example == 2:
        example_2_with_progress_callback()
    elif args.example == 3:
        example_3_background_job_without_http()
    elif args.example == 4:
        example_4_list_tasks()
    else:
        # Run all examples
        example_1_sync_ingestion()
        # example_2_with_progress_callback()  # Skip for brevity
        # example_3_background_job_without_http()  # Skip for brevity
        example_4_list_tasks()


if __name__ == "__main__":
    main()
