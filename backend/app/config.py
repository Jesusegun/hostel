"""
Configuration Management

This module handles all environment-based configuration using Pydantic Settings.
All sensitive data (passwords, API keys) comes from environment variables, never hardcoded.

Why Pydantic Settings?
- Type validation (catches errors early)
- Auto-loads from .env files
- Easy to test (can override settings)
- Clear documentation of required variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Application Settings
    
    All settings are loaded from environment variables or .env file.
    Required settings will raise an error if not provided.
    """
    
    # ===== Application Settings =====
    APP_NAME: str = "Hostel Repair Management System"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    # ===== Server Settings =====
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    PUBLIC_API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    
    # ===== Database Settings =====
    # This is REQUIRED - will error if not provided
    DATABASE_URL: str
    
    # ===== JWT Authentication =====
    JWT_SECRET_KEY: str  # REQUIRED - use: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # ===== Google Sheets API =====
    GOOGLE_SHEETS_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_SHEET_ID: str  # REQUIRED
    
    # ===== Cloudinary (Image Storage) =====
    CLOUDINARY_CLOUD_NAME: str  # REQUIRED
    CLOUDINARY_API_KEY: str  # REQUIRED
    CLOUDINARY_API_SECRET: str  # REQUIRED
    
    # ===== Email Service (SMTP) =====
    SMTP_HOST: str  # REQUIRED - e.g., "smtp.gmail.com" or "smtp-mail.outlook.com"
    SMTP_PORT: int = 587  # Default TLS port (587 for TLS, 465 for SSL)
    SMTP_USER: str  # REQUIRED - SMTP username/email address
    SMTP_PASSWORD: str  # REQUIRED - SMTP password or app password
    SMTP_USE_TLS: bool = True  # Enable TLS encryption (recommended)
    SYSTEM_EMAIL_FROM: str = "noreply@hostelrepairs.com"  # Should match SMTP_USER
    SYSTEM_EMAIL_NAME: str = "Hostel Repairs System"
    
    # ===== CORS (Cross-Origin Resource Sharing) =====
    # List of allowed frontend URLs
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # ===== Background Tasks =====
    SYNC_INTERVAL_MINUTES: int = 15  # How often to sync from Google Sheets
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"  # Load from .env file
        case_sensitive = True  # DATABASE_URL != database_url


@lru_cache()
def get_settings() -> Settings:
    """
    Get Settings Instance (Cached)
    
    Why @lru_cache?
    - Settings object is created once and reused
    - Improves performance (no re-reading .env file)
    - Thread-safe
    
    Usage:
        from app.config import settings
        print(settings.DATABASE_URL)
    """
    return Settings()


# Create a global settings instance
settings = get_settings()


# ===== Helper Functions =====

def is_development() -> bool:
    """Check if running in development mode"""
    return settings.ENVIRONMENT == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return settings.ENVIRONMENT == "production"


def get_cors_origins() -> List[str]:
    """
    Get CORS origins based on environment
    
    In development: Allow localhost
    In production: Only allow production URLs
    """
    if is_production():
        return settings.ALLOWED_ORIGINS
    else:
        # In development, be more permissive
        return settings.ALLOWED_ORIGINS + [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]

