Enable Images - Re-enable Checklist and Steps

Purpose
This document explains how to fully re-enable image handling (Google Drive download -> Cloudinary upload -> API -> UI) after it was disabled.

Quick overview of what was disabled
- Google Sheets parsing no longer reads the image column.
- Sync pipeline no longer uploads to Cloudinary or tracks retry queues.
- Issue API responses no longer include image_url.
- Frontend no longer renders images or shows image retry messaging.
- Cloudinary config is commented out.
- Issue image retry model exports are commented out.

General approach to re-enable
1. Re-enable backend ingestion and upload.
2. Re-enable database fields and retry tracking.
3. Re-enable API schema and responses.
4. Re-enable frontend rendering and sync status messaging.
5. Verify end-to-end flow.

Step 1 - Backend configuration
- Uncomment Cloudinary settings in [backend/app/config.py](backend/app/config.py).
- Ensure Cloudinary credentials are set in your server environment (do not commit secrets to Git).
- Confirm GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEET_ID are configured as before.

Step 2 - Backend services and sync pipeline
- Re-enable image parsing in Google Sheets service:
  - Uncomment the image field extraction and return field in [backend/app/services/google_sheets_service.py](backend/app/services/google_sheets_service.py).
- Re-enable Cloudinary upload logic and retry queue in [backend/app/services/sync_service.py](backend/app/services/sync_service.py).
  - Uncomment IssueImageRetry import at the top of the file.
  - Uncomment imports for get_image_drive_url and upload_image_from_url.
  - Uncomment the retry queue processing and retry metrics (_apply_retry_metrics).
  - Uncomment image handling block in the sync loop.
  - Restore retry_summary in all sync responses (success and failure).

Step 3 - Models and database
- Issue model:
  - Uncomment image_url column and image retry relationship in [backend/app/models/issue.py](backend/app/models/issue.py).
  - Restore image_url in Issue.to_dict if you want legacy paths using to_dict to include it.
- Issue image retry model:
  - Re-enable model export in [backend/app/models/__init__.py](backend/app/models/__init__.py).
- Issue image retry relationship:
  - Re-enable the IssueImageRetry.issue relationship in [backend/app/models/issue_image_retry.py](backend/app/models/issue_image_retry.py).
- Initialization script:
  - Re-enable IssueImageRetry import in [backend/app/init_db.py](backend/app/init_db.py).

Database migration guidance
- If your database already has issues.image_url and issue_image_retries, no migration is needed.
- If the database was created after images were disabled, you must add those structures:
  - Add issues.image_url column (String(500), nullable).
  - Create issue_image_retries table.
  - Preferred: create an Alembic migration and apply it.

Step 4 - API schemas and responses
- Re-add image_url to IssueResponse and IssueListItem in [backend/app/schemas/issue.py](backend/app/schemas/issue.py).
- Re-add image_url to issue list and detail responses in [backend/app/api/issues.py](backend/app/api/issues.py).
- Re-enable retry fields in sync status output in [backend/app/api/sync.py](backend/app/api/sync.py).
- Re-enable health metrics for image retry queue in [backend/app/main.py](backend/app/main.py).

Step 5 - Backend service exports
- Re-enable Cloudinary service exports and get_image_drive_url export in [backend/app/services/__init__.py](backend/app/services/__init__.py).

Step 6 - Frontend UI and sync messaging
- Re-enable image rendering in the issue detail view:
  - Restore image block in [frontend/src/pages/IssueDetailPage.jsx](frontend/src/pages/IssueDetailPage.jsx).
- Re-enable image retry messaging in sync status:
  - Restore retry summary handling in [frontend/src/pages/SyncStatusPage.jsx](frontend/src/pages/SyncStatusPage.jsx).
- Update any sync copy if needed in [frontend/src/services/syncService.js](frontend/src/services/syncService.js).

Step 7 - Verification checklist
- Manual sync creates issues with image_url populated.
- Issue detail shows image preview.
- Issue list and detail APIs include image_url.
- Sync status returns retry metrics and pending retry count (if configured).
- Health endpoint returns retry metrics without error.

Notes and cautions
- Do not commit secrets. Store Cloudinary and Google credentials in secure environment variables or a protected .env on the server.
- Ensure Google Drive image sharing is compatible with direct download URLs.
- Cloudinary upload failures should create retry entries; confirm this path works by testing with a bad URL and a valid URL.

Recommended order when re-enabling
1. Backend config and services.
2. Models and migrations.
3. API schemas and routes.
4. Frontend rendering and sync UI.
5. End-to-end tests.
