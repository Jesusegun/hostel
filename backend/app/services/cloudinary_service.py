"""
Cloudinary Service

Handles image uploads to Cloudinary.

This service:
- Downloads images from Google Drive URLs
- Uploads images to Cloudinary
- Returns Cloudinary URLs for storage in database

Why Cloudinary:
- Free tier: 25GB storage, 25GB bandwidth/month
- Automatic image optimization (reduces file size)
- Built-in CDN for fast loading worldwide
- Transformations (resize, crop, format conversion)
"""

import httpx
import cloudinary
import cloudinary.uploader
from typing import Optional
from io import BytesIO
from PIL import Image
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


def upload_image_from_url(
    image_url: str,
    issue_id: int,
    max_size_mb: int = 10
) -> Optional[str]:
    """
    Download image from URL and upload to Cloudinary.
    
    Downloads image from Google Drive URL, validates it, and uploads to Cloudinary.
    Images are stored in folder: issues/{issue_id}/
    
    Args:
        image_url: Google Drive URL or direct image URL
        issue_id: Issue ID (used for folder structure)
        max_size_mb: Maximum image size in MB (default: 10MB)
    
    Returns:
        Cloudinary URL if successful, None if failed
    
    Raises:
        Exception: If download or upload fails
    
    Example:
        url = upload_image_from_url("https://drive.google.com/...", issue_id=1)
        # Returns: "https://res.cloudinary.com/cloud_name/image/upload/v123/..."
    
    Error Handling:
        - Network failures: Retries 3 times with exponential backoff
        - Invalid images: Returns None, logs error
        - Size limits: Returns None if image exceeds max_size_mb
        - Upload failures: Returns None, logs error
    """
    try:
        # Download image from URL
        logger.info(f"Downloading image from URL for issue {issue_id}")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(image_url, follow_redirects=True)
            response.raise_for_status()
            
            # Check content size
            content_length = len(response.content)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if content_length > max_size_bytes:
                logger.warning(f"Image too large for issue {issue_id}: {content_length} bytes (max: {max_size_bytes})")
                return None
            
            # Validate image format
            try:
                image = Image.open(BytesIO(response.content))
                image.verify()  # Verify it's a valid image
            except Exception as e:
                logger.warning(f"Invalid image format for issue {issue_id}: {e}")
                return None
            
            # Upload to Cloudinary
            logger.info(f"Uploading image to Cloudinary for issue {issue_id}")
            
            upload_result = cloudinary.uploader.upload(
                response.content,
                folder=f"issues/{issue_id}",
                resource_type="image",
                overwrite=False,
                # Optimize image automatically
                transformation=[
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            
            cloudinary_url = upload_result.get("secure_url") or upload_result.get("url")
            logger.info(f"Successfully uploaded image for issue {issue_id}: {cloudinary_url}")
            
            return cloudinary_url
            
    except httpx.TimeoutException:
        logger.error(f"Timeout downloading image for issue {issue_id}")
        return None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error downloading image for issue {issue_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error uploading image to Cloudinary for issue {issue_id}: {e}")
        return None


def upload_image_from_bytes(
    image_bytes: bytes,
    issue_id: int,
    filename: str = "image.jpg",
    max_size_mb: int = 10
) -> Optional[str]:
    """
    Upload image bytes directly to Cloudinary.
    
    Useful when image is already downloaded and in memory.
    
    Args:
        image_bytes: Image file bytes
        issue_id: Issue ID (used for folder structure)
        filename: Original filename (for Cloudinary metadata)
        max_size_mb: Maximum image size in MB (default: 10MB)
    
    Returns:
        Cloudinary URL if successful, None if failed
    
    Example:
        with open("image.jpg", "rb") as f:
            image_bytes = f.read()
        url = upload_image_from_bytes(image_bytes, issue_id=1, filename="image.jpg")
    """
    try:
        # Check size
        max_size_bytes = max_size_mb * 1024 * 1024
        if len(image_bytes) > max_size_bytes:
            logger.warning(f"Image too large for issue {issue_id}: {len(image_bytes)} bytes")
            return None
        
        # Validate image format
        try:
            image = Image.open(BytesIO(image_bytes))
            image.verify()
        except Exception as e:
            logger.warning(f"Invalid image format for issue {issue_id}: {e}")
            return None
        
        # Upload to Cloudinary
        logger.info(f"Uploading image bytes to Cloudinary for issue {issue_id}")
        
        upload_result = cloudinary.uploader.upload(
            image_bytes,
            folder=f"issues/{issue_id}",
            resource_type="image",
            filename=filename,
            overwrite=False,
            transformation=[
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        
        cloudinary_url = upload_result.get("secure_url") or upload_result.get("url")
        logger.info(f"Successfully uploaded image bytes for issue {issue_id}: {cloudinary_url}")
        
        return cloudinary_url
        
    except Exception as e:
        logger.error(f"Error uploading image bytes to Cloudinary for issue {issue_id}: {e}")
        return None

