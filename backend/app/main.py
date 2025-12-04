"""
FastAPI Application Entry Point

This is the main file that starts the FastAPI application.
Think of it as "opening the restaurant" - it sets up everything and starts serving requests.

Architecture:
    main.py (this file) → Initializes app → Registers routes → Starts server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from app.config import settings, get_cors_origins
from app.database import SessionLocal, check_db_connection, get_db_url_safe
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.models import IssueImageRetry, SyncLog
from app.tasks.sync_scheduler import (
    get_scheduler_status,
    start_scheduler,
    stop_scheduler,
)
import logging

configure_logging()
logger = logging.getLogger(__name__)

# ===== Create FastAPI Application =====

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Hostel Repair Management System",
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    
    # API Documentation URLs
    docs_url="/api/docs",  # Swagger UI: http://localhost:8000/api/docs
    redoc_url="/api/redoc",  # ReDoc: http://localhost:8000/api/redoc
)

# ===== Performance Middleware =====

# Request tracing / context
app.add_middleware(RequestContextMiddleware)

# Response compression (helps poor networks)
app.add_middleware(GZipMiddleware, minimum_size=500)

# Rate limiting (protects against accidental overload)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ===== CORS Middleware =====
# CORS = Cross-Origin Resource Sharing
# Allows frontend (React on localhost:3000) to talk to backend (FastAPI on localhost:8000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),  # Which domains can access our API
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers
)


# ===== Startup Event =====
# Runs once when the server starts

@app.on_event("startup")
async def startup_event():
    """
    Startup Tasks
    
    Runs when the server starts. Good place for:
    - Database connection checks
    - Loading data into memory
    - Starting background tasks
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Database: {get_db_url_safe()}")
    logger.info("=" * 60)
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection successful")
    else:
        logger.warning("Database connection failed - check your DATABASE_URL")
        logger.warning("Sync scheduler will not start until database is connected")
    
    # Start background scheduler for Google Sheets sync
    try:
        start_scheduler()
        logger.info(f"Sync scheduler started (runs every {settings.SYNC_INTERVAL_MINUTES} minutes)")
    except Exception as e:
        logger.warning(f"Failed to start sync scheduler: {e}")
        logger.warning("Manual sync will still work via API endpoint")


# ===== Shutdown Event =====
# Runs when the server stops

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown Tasks
    
    Runs when the server stops. Good place for:
    - Closing database connections
    - Saving state
    - Cleanup tasks
    """
    logger.info("=" * 60)
    logger.info("Shutting down gracefully...")
    
    # Stop background scheduler
    try:
        stop_scheduler()
        logger.info("Sync scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping sync scheduler: {e}")
    
    logger.info("=" * 60)


# ===== Root Endpoint =====
# Simple test endpoint to verify server is running

@app.get("/")
async def root():
    """
    Root Endpoint
    
    Simple health check to verify the API is running.
    Visit: http://localhost:8000/
    
    Returns:
        dict: Welcome message and status
    """
    return {
        "message": "Hostel Repair Management System API",
        "status": "running",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/api/docs",
    }


# ===== Health Check Endpoint =====
# Used by hosting platforms (Railway/Render) to verify app is healthy

@app.get("/api/health")
async def health_check():
    """
    Health Check Endpoint
    
    Used by:
    - Railway/Render for health monitoring
    - Load balancers
    - Monitoring tools
    
    Returns:
        dict: Health status and database connection
    """
    db_status = "connected" if check_db_connection() else "disconnected"
    scheduler_status = get_scheduler_status()

    metrics = {
        "pending_image_retries": None,
        "last_sync": None,
        "last_sync_status": None,
    }

    try:
        with SessionLocal() as session:
            metrics["pending_image_retries"] = (
                session.query(IssueImageRetry).count()
            )
            last_sync = (
                session.query(SyncLog).order_by(SyncLog.started_at.desc()).first()
            )
            if last_sync:
                metrics["last_sync"] = last_sync.to_dict()
                metrics["last_sync_status"] = last_sync.status
    except Exception as exc:  # pragma: no cover - best effort metrics
        metrics["metrics_error"] = str(exc)

    status = (
        "healthy"
        if db_status == "connected" and scheduler_status.get("running")
        else "degraded"
    )
    
    return {
        "status": status,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "scheduler": scheduler_status,
        "metrics": metrics,
        "version": settings.API_VERSION,
    }


# ===== API Routes =====
# Import and register all API routers

from app.api import auth, dashboard, issues, sync, admin

# Authentication routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Issues routes
app.include_router(issues.router, prefix="/api/issues", tags=["Issues"])

# Sync routes
app.include_router(sync.router, prefix="/api/sync", tags=["Sync"])

# Dashboard routes (admin analytics)
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# Hall routes
from app.api import halls
app.include_router(halls.router, prefix="/api", tags=["Halls"])

# Admin routes (DSA only)
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


# ===== Run Application =====
# This is only used when running directly: python main.py
# In production, we use: uvicorn app.main:app

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API Documentation: http://localhost:{settings.PORT}/api/docs")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # Auto-reload on code changes (development only)
        log_level="info",
    )

