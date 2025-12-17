"""
This script tests if all imports in startup.py are loaded successfully.
Run this script to verify that there are no ImportErrors or other issues.
"""

import sys
import os



try:
    from app.core import get_logger
    from app.core.cache import(
        initialize_cache,
        close_cache
    )
    from app.core.events import (
        get_event_bus,
        init_event_handlers,
    )
    from app.core.email_client import init_email_client
    from app.core.embedding_factory import get_embedding_provider
    from app.core.llm_factory import (
        get_internal_llm_provider,
        get_llm_provider,
        get_fallback_llm_provider
    )
    from app.core.vector_store_factory import get_vector_store, get_retriever
    from app.core.database import DatabaseManager
    from app.core.settings_loader import load_settings_by_category
    from app.config import (
        settings as settings_module,
        settings,
        cache_settings,
        DatabaseSettings,
        Settings
    )
    from app.jobs import get_job_manager
    from app.jobs.integration import JobQueueIntegration
    from app.jobs.bootstrap import init_jobs
    from app.services.vector_store.reranker import get_reranker_service

    print("All imports loaded successfully.")

except ImportError as e:
    print(f"ImportError: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")