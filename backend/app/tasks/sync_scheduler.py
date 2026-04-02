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
from app.models import SyncLog, User
from app.models.user import UserRole
from app.services.sync_service import sync_google_sheets
from app.services.email_service import send_sync_failure_alert
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

        # Check for consecutive failures and alert admins if needed
        _check_and_send_failure_alerts(db)

    except Exception as e:
        logger.error(f"Error in scheduled sync job: {e}", exc_info=True)
    finally:
        db.close()
        clear_request_id()


def _check_and_send_failure_alerts(db):
    """
    Check for consecutive sync failures and alert admin users.

    Alert rules (to avoid spam on flaky networks):
    - Sends at exactly SYNC_FAILURE_ALERT_THRESHOLD (default 3) consecutive failures.
    - Then sends again every 5th consecutive failure (8, 13, 18, ...).
    - This means 3 failures = 45 min of downtime before the first alert.

    Recipients: all users with role=admin and email IS NOT NULL
    (currently DSA + maintenance_officer).
    """
    try:
        threshold = settings.SYNC_FAILURE_ALERT_THRESHOLD

        # Get the most recent sync logs, up to threshold + margin
        recent_logs = (
            db.query(SyncLog)
            .order_by(SyncLog.completed_at.desc())
            .limit(threshold + 10)
            .all()
        )

        if not recent_logs:
            return

        # Count consecutive failures from the most recent log
        consecutive_failures = 0
        latest_errors = []
        for log in recent_logs:
            if log.status == "failed":
                consecutive_failures += 1
                if log.errors and isinstance(log.errors, list):
                    latest_errors.extend(log.errors[:3])
            else:
                break  # First success breaks the streak

        if consecutive_failures < threshold:
            return

        # Anti-spam: only alert at the threshold or every 5th failure after
        failures_past_threshold = consecutive_failures - threshold
        if consecutive_failures != threshold and failures_past_threshold % 5 != 0:
            return

        logger.warning(
            "Sync has failed %d consecutive times (≥ threshold %d). Sending alerts.",
            consecutive_failures,
            threshold,
        )

        # Get all admin users with emails
        admin_users = (
            db.query(User)
            .filter(
                User.role == UserRole.ADMIN,
                User.email.isnot(None),
                User.is_active == True,
            )
            .all()
        )

        for admin in admin_users:
            try:
                send_sync_failure_alert(
                    recipient_email=admin.email,
                    consecutive_failures=consecutive_failures,
                    latest_errors=latest_errors[:5],
                )
            except Exception as e:
                logger.error(
                    "Failed to send sync failure alert to %s: %s",
                    admin.username,
                    e,
                )
    except Exception as e:
        logger.error("Error checking sync failure alerts: %s", e)


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

