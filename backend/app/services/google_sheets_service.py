"""
Google Sheets Service

Handles Google Sheets API operations.

This service:
- Fetches data from Google Sheets
- Parses form submission rows
- Extracts Google Drive image URLs
- Converts Drive URLs to direct download URLs

Why this service exists:
- Separates Google API logic from sync logic
- Reusable for other Google Sheets operations
- Easier to test and maintain
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


def get_google_sheets_client():
    """
    Initialize and return Google Sheets API client.
    
    Uses service account credentials from credentials.json file.
    Service account must have access to the Google Sheet.
    
    Returns:
        Google Sheets API service object
    
    Raises:
        FileNotFoundError: If credentials.json not found
        Exception: If authentication fails
    
    Example:
        service = get_google_sheets_client()
        result = service.spreadsheets().values().get(...).execute()
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        logger.info("Google Sheets API client initialized successfully")
        return service
        
    except FileNotFoundError:
        logger.error(f"Credentials file not found: {settings.GOOGLE_SHEETS_CREDENTIALS_FILE}")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets client: {e}")
        raise


def fetch_sheet_data(
    sheet_id: str,
    range_name: str = "A:Z"
) -> List[List[str]]:
    """
    Fetch all rows from Google Sheet.
    
    Args:
        sheet_id: Google Sheet ID (from URL)
        range_name: Range to fetch (default: "A:Z" for all columns)
    
    Returns:
        List of rows, where each row is a list of cell values
    
    Raises:
        HttpError: If Google API request fails
        Exception: If client initialization fails
    
    Example:
        rows = fetch_sheet_data("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
        # Returns: [["Timestamp", "Email", ...], ["2025-11-23", "student@example.com", ...], ...]
    
    Error Handling:
        - API errors: Raises HttpError with details
        - Rate limiting: Should be handled by retry logic in caller
        - Empty sheet: Returns empty list
    """
    try:
        service = get_google_sheets_client()
        
        logger.info(f"Fetching data from Google Sheet: {sheet_id}, range: {range_name}")
        
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        rows = result.get('values', [])
        logger.info(f"Fetched {len(rows)} rows from Google Sheet")
        
        return rows
        
    except HttpError as e:
        logger.error(f"Google Sheets API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching sheet data: {e}")
        raise


def parse_form_submission(
    row: List[str],
    headers: List[str]
) -> Optional[Dict[str, any]]:
    """
    Parse a form submission row into structured dictionary.
    
    Expected columns (from Google Form):
    1. Timestamp (A)
    2. Email Address (B)
    3. Name (C) - Optional
    4. Hall (D)
    5. Room Number (E)
    6. Category (F)
    7. Describe the Issue (G) - Optional
    8. Image (H) - Google Drive URL
    
    Args:
        row: List of cell values from Google Sheet
        headers: List of header names (first row)
    
    Returns:
        Dictionary with parsed form data, or None if invalid
    
    Example:
        headers = ["Timestamp", "Email Address", "Name", "Hall", "Room Number", "Category", "Describe the Issue", "Image"]
        row = ["2025-11-23 10:00:00", "student@example.com", "John Doe", "Levi", "A205", "Plumbing", "Leaking pipe", "https://drive.google.com/..."]
        data = parse_form_submission(row, headers)
        # Returns: {
        #     "timestamp": datetime(...),
        #     "email": "student@example.com",
        #     "name": "John Doe",
        #     "hall": "Levi",
        #     "room_number": "A205",
        #     "category": "Plumbing",
        #     "description": "Leaking pipe",
        #     "image_url": "https://drive.google.com/..."
        # }
    
    Validation:
        - Required fields: email, hall, room_number, category
        - Optional fields: name, description
        - Timestamp parsing: Handles various date formats
    """
    try:
        # Create mapping from headers to indices
        header_map = {header.lower().strip(): idx for idx, header in enumerate(headers)}
        
        # Helper to get value by header name (case-insensitive)
        def get_value(header_name: str, default: str = "") -> str:
            for key, idx in header_map.items():
                if header_name.lower() in key:
                    if idx < len(row):
                        return row[idx].strip() if row[idx] else default
            return default
        
        # Parse timestamp
        timestamp_str = get_value("timestamp")
        timestamp = None
        if timestamp_str:
            try:
                # Try parsing various date formats
                # Google Forms typically uses formats like:
                # - "11/24/2025 19:22:00" (US format with time)
                # - "24/11/2025 19:22:00" (European format)
                # - "2025-11-24 19:22:00" (ISO format)
                # - "11/24/2025" (date only)
                # - May include timezone info
                
                # Remove timezone info if present (e.g., "GMT+01:00", "UTC")
                timestamp_clean = timestamp_str.split(" GMT")[0].split(" UTC")[0].strip()
                
                # Try multiple formats in order of likelihood
                formats = [
                    "%m/%d/%Y %H:%M:%S",      # US format with seconds: "11/24/2025 19:22:00"
                    "%d/%m/%Y %H:%M:%S",      # European format with seconds: "24/11/2025 19:22:00"
                    "%Y-%m-%d %H:%M:%S",      # ISO format with seconds: "2025-11-24 19:22:00"
                    "%m/%d/%Y %H:%M",         # US format without seconds: "11/24/2025 19:22"
                    "%d/%m/%Y %H:%M",         # European format without seconds: "24/11/2025 19:22"
                    "%Y-%m-%d %H:%M",         # ISO format without seconds: "2025-11-24 19:22"
                    "%m/%d/%Y",               # US date only: "11/24/2025"
                    "%d/%m/%Y",               # European date only: "24/11/2025"
                    "%Y-%m-%d",               # ISO date only: "2025-11-24"
                ]
                
                for fmt in formats:
                    try:
                        timestamp = datetime.strptime(timestamp_clean, fmt)
                        # Add timezone info (assume UTC if not specified)
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
                
                if not timestamp:
                    logger.warning(f"Could not parse timestamp with any format: {timestamp_str}")
            except Exception as e:
                logger.warning(f"Error parsing timestamp: {timestamp_str}, error: {e}")
        
        # Get required fields
        email = get_value("email")
        hall = get_value("hall")
        room_number = get_value("room number") or get_value("room_number")
        category = get_value("category")
        image_url = get_value("image")
        
        # Validate required fields
        if not email or not hall or not room_number or not category:
            logger.warning(f"Missing required fields in row: email={bool(email)}, hall={bool(hall)}, room_number={bool(room_number)}, category={bool(category)}")
            return None
        
        # Get optional fields
        name = get_value("name")
        description = get_value("description") or get_value("describe")
        
        return {
            "timestamp": timestamp,
            "email": email,
            "name": name if name else None,
            "hall": hall,
            "room_number": room_number,
            "category": category,
            "description": description if description else None,
            "image_url": image_url if image_url else None
        }
        
    except Exception as e:
        logger.error(f"Error parsing form submission row: {e}")
        return None


def get_image_drive_url(image_url: str) -> str:
    """
    Convert Google Drive sharing URL to direct download URL.
    
    Google Forms stores images in Google Drive with sharing URLs like:
    - https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    - https://drive.google.com/open?id=FILE_ID
    
    This function extracts the file ID and converts to direct download URL:
    - https://drive.google.com/uc?export=download&id=FILE_ID
    
    Args:
        image_url: Google Drive sharing URL
    
    Returns:
        Direct download URL
    
    Example:
        sharing_url = "https://drive.google.com/file/d/1ABC123xyz/view?usp=sharing"
        download_url = get_image_drive_url(sharing_url)
        # Returns: "https://drive.google.com/uc?export=download&id=1ABC123xyz"
    
    Note:
        - Handles various Google Drive URL formats
        - Returns original URL if format not recognized
    """
    if not image_url:
        return ""
    
    # Pattern 1: https://drive.google.com/file/d/FILE_ID/view
    pattern1 = r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)'
    match1 = re.search(pattern1, image_url)
    if match1:
        file_id = match1.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Pattern 2: https://drive.google.com/open?id=FILE_ID
    pattern2 = r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)'
    match2 = re.search(pattern2, image_url)
    if match2:
        file_id = match2.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Pattern 3: Already a direct download URL
    if "uc?export=download" in image_url:
        return image_url
    
    # If no pattern matches, return original URL (might be direct image URL)
    logger.warning(f"Could not parse Google Drive URL format: {image_url}")
    return image_url

