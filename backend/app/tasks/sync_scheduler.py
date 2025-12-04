"""
Sync Scheduler

Sets up and manages scheduled Google Sheets synchronization.

This module:
- Initializes APScheduler
- Schedules sync job to run every 15 minutes
- Handles job execution and error recovery
- Provides start/stop functions for app lifecycle

Why APScheduler:
- Industry standard for Python background jobs
- Supports cron-like scheduling
- Handles timezones correctly
- Thread-safe (can run alongside FastAPI)
"""

import logging
from typing import Optional
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.sync_service import sync_google_sheets
from app.utils.request_context import clear_request_id, set_request_id

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None


def scheduled_sync_job():
    """
    Scheduled background job that syncs Google Sheets.
    
    This function is called by APScheduler every 15 minutes.
    It:
    1. Creates a database session
    2. Calls sync_google_sheets()
    3. Logs the results
    4. Handles errors gracefully (doesn't crash scheduler)
    
    Error Handling:
        - Database errors: Logged, don't crash scheduler
        - Sync errors: Logged, sync continues on next run
        - Network errors: Logged, retry on next run
    """
    request_id = f"scheduler-{uuid4().hex[:8]}"
    set_request_id(request_id)
    logger.info("Starting scheduled Google Sheets sync")

    db = SessionLocal()
    try:
        result = sync_google_sheets(db, manual=False)

        if result["status"] == "success":
            logger.info(
                f"Scheduled sync completed: {result['rows_created']} created, "
                f"{result['rows_skipped']} skipped, {len(result.get('errors', []))} errors"
            )
        else:
            logger.error(f"Scheduled sync failed: {result.get('errors', [])}")

    except Exception as e:
        logger.error(f"Error in scheduled sync job: {e}", exc_info=True)
    finally:
        db.close()
        clear_request_id()


def setup_sync_scheduler() -> BackgroundScheduler:
    """
    Initialize and configure APScheduler for Google Sheets sync.
    
    Creates a BackgroundScheduler and adds the sync job.
    Job runs every 15 minutes (from config: SYNC_INTERVAL_MINUTES).
    
    Returns:
        Configured BackgroundScheduler instance
    
    Example:
        scheduler = setup_sync_scheduler()
        scheduler.start()
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # Add sync job (runs every 15 minutes)
    sync_interval = settings.SYNC_INTERVAL_MINUTES
    scheduler.add_job(
        scheduled_sync_job,
        trigger=IntervalTrigger(minutes=sync_interval),
        id="google_sheets_sync",
        name="Google Sheets Sync",
        replace_existing=True,
        max_instances=1  # Don't run multiple syncs simultaneously
    )
    
    logger.info(f"Sync scheduler configured: runs every {sync_interval} minutes")
    
    return scheduler


def start_scheduler():
    """
    Start the background scheduler.
    
    Should be called on application startup.
    Scheduler will run in background thread and execute jobs on schedule.
    
    Example:
        start_scheduler()
        # Scheduler now running, sync will execute every 15 minutes
    """
    global scheduler
    
    if scheduler is None:
        scheduler = setup_sync_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Sync scheduler started")
    else:
        logger.warning("Scheduler already running")


def stop_scheduler():
    """
    Stop the background scheduler.
    
    Should be called on application shutdown.
    Gracefully shuts down scheduler and waits for running jobs to complete.
    
    Example:
        stop_scheduler()
        # Scheduler stopped, no more scheduled syncs
    """
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Sync scheduler stopped")
    else:
        logger.warning("Scheduler not running")


def is_scheduler_running() -> bool:
    """Return True if the scheduler is initialized and running."""
    return bool(scheduler and scheduler.running)


def get_scheduler_status() -> dict:
    """Detailed scheduler status for health endpoints."""
    if scheduler and scheduler.running:
        jobs = scheduler.get_jobs()
        next_run = None
        next_times = [
            job.next_run_time for job in jobs if getattr(job, "next_run_time", None)
        ]
        if next_times:
            next_run = min(next_times)
        return {
            "running": True,
            "jobs": len(jobs),
            "next_run": next_run.isoformat() if next_run else None,
        }
    return {"running": False, "jobs": 0, "next_run": None}

