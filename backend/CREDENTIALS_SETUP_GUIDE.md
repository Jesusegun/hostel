# Credentials Setup Guide

Step-by-step instructions for setting up Google Sheets API and Cloudinary credentials.

---

## Part 1: Google Sheets API Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `Hostel Repair System` (or any name)
4. Click **"Create"**
5. Wait for project creation (takes ~30 seconds)

### Step 2: Enable Google Sheets API

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and click **"Enable"**
4. Also enable **"Google Drive API"** (needed for image downloads)
   - Search for "Google Drive API" → Enable

### Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in:
   - **Service account name**: `hostel-repair-sync` (or any name)
   - **Service account ID**: Auto-generated (leave as is)
   - **Description**: `Service account for Google Sheets sync`
4. Click **"Create and Continue"**
5. Skip "Grant this service account access to project" (click **"Continue"**)
6. Skip "Grant users access to this service account" (click **"Done"**)

### Step 4: Create Service Account Key

1. In the **"Credentials"** page, find your service account
2. Click on the service account email
3. Go to **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. **IMPORTANT**: A JSON file will download automatically
   - This file contains your credentials
   - **Keep it secure!** Don't commit it to Git

### Step 5: Save Credentials File

1. Rename the downloaded file to `credentials.json`
2. Move it to: `backend/credentials.json`
   ```
   backend/
   ├── credentials.json  ← Put it here
   ├── app/
   ├── .env
   └── ...
   ```

### Step 6: Get Your Google Sheet ID

1. Open your Google Sheet (the one connected to your Google Form)
2. Look at the URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
   ```
3. Copy the `SHEET_ID_HERE` part
   - Example: If URL is `https://docs.google.com/spreadsheets/d/1ABC123xyz/edit`
   - Sheet ID is: `1ABC123xyz`

### Step 7: Share Sheet with Service Account

1. Open your Google Sheet
2. Click **"Share"** button (top right)
3. In the "Add people and groups" field, paste your **service account email**
   - Find it in: Google Cloud Console → IAM & Admin → Service Accounts
   - It looks like: `hostel-repair-sync@your-project-id.iam.gserviceaccount.com`
4. Set permission to **"Viewer"** (read-only is enough)
5. Uncheck **"Notify people"** (service account doesn't need email)
6. Click **"Share"**

**Why?** The service account needs permission to read your Google Sheet.

---

## Part 2: Cloudinary Setup

### Step 1: Create Cloudinary Account

1. Go to [Cloudinary.com](https://cloudinary.com/)
2. Click **"Sign Up for Free"**
3. Fill in:
   - Email address
   - Password
   - Company/Name (optional)
4. Click **"Create Account"**
5. Verify your email (check inbox)

### Step 2: Get Your Credentials

1. After logging in, you'll see the **Dashboard**
2. Look for **"Account Details"** section
3. You'll see three values:
   - **Cloud Name**: e.g., `dxyz123abc`
   - **API Key**: e.g., `123456789012345`
   - **API Secret**: e.g., `abcdefghijklmnopqrstuvwxyz123456`
4. **Copy all three values** (you'll need them for `.env` file)

**Note**: API Secret is sensitive - keep it private!

---

## Part 3: Update .env File

### Step 1: Copy env.example to .env

If you don't have a `.env` file yet:

```bash
# In backend/ directory
cp env.example .env
```

### Step 2: Add Your Credentials

Open `backend/.env` and update these values:

```bash
# ===== Google Sheets API =====
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_ID=your-actual-sheet-id-here

# ===== Cloudinary =====
CLOUDINARY_CLOUD_NAME=your-cloud-name-here
CLOUDINARY_API_KEY=your-api-key-here
CLOUDINARY_API_SECRET=your-api-secret-here
```

**Example:**
```bash
GOOGLE_SHEET_ID=1ABC123xyz456DEF789
CLOUDINARY_CLOUD_NAME=dxyz123abc
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz123456
```

### Step 3: Verify File Locations

Make sure your file structure looks like this:

```
backend/
├── .env                    ← Your credentials (already exists)
├── credentials.json        ← Google service account key
├── app/
│   ├── main.py
│   └── ...
└── ...
```

---

## Part 4: Test Your Setup

### Test 1: Verify credentials.json

```bash
# In backend/ directory
python -c "import json; f=open('credentials.json'); data=json.load(f); print('✅ Valid JSON'); print('Project ID:', data.get('project_id'))"
```

**Expected**: Should print "✅ Valid JSON" and your project ID.

### Test 2: Test Google Sheets Connection

```bash
# In backend/ directory
python -c "from app.services.google_sheets_service import get_google_sheets_client; client = get_google_sheets_client(); print('✅ Google Sheets client initialized')"
```

**Expected**: Should print "✅ Google Sheets client initialized" without errors.

### Test 3: Test Cloudinary Connection

```bash
# In backend/ directory
python -c "import cloudinary; from app.config import settings; cloudinary.config(cloud_name=settings.CLOUDINARY_CLOUD_NAME, api_key=settings.CLOUDINARY_API_KEY, api_secret=settings.CLOUDINARY_API_SECRET); print('✅ Cloudinary configured')"
```

**Expected**: Should print "✅ Cloudinary configured" without errors.

### Test 4: Test Manual Sync (Full Test)

1. Make sure your server is running:
   ```bash
   cd backend
   .\venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload
   ```

2. In another terminal, test the sync endpoint:
   ```powershell
   # First, login as admin to get token
   $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"maintenance_officer","password":"changeme123"}'
   $token = $loginResponse.access_token

   # Trigger manual sync
   $headers = @{
       "Authorization" = "Bearer $token"
   }
   Invoke-RestMethod -Uri "http://localhost:8000/api/sync/google-sheets" -Method POST -Headers $headers
   ```

**Expected**: Should return sync results with `status: "success"` or `status: "failed"` with error details.

---

## Troubleshooting

### Error: "Credentials file not found"

**Problem**: `credentials.json` is missing or in wrong location.

**Solution**: 
- Make sure `credentials.json` is in `backend/` directory
- Check the file name (must be exactly `credentials.json`)

### Error: "Permission denied" or "403 Forbidden"

**Problem**: Service account doesn't have access to Google Sheet.

**Solution**:
1. Open your Google Sheet
2. Click "Share"
3. Add service account email with "Viewer" permission
4. Make sure you clicked "Share" (not just "Done")

### Error: "Invalid Cloudinary credentials"

**Problem**: Wrong Cloudinary credentials in `.env`.

**Solution**:
1. Double-check all three values in `.env`:
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
2. Make sure there are no extra spaces or quotes
3. Copy-paste directly from Cloudinary dashboard

### Error: "Sheet not found" or "404 Not Found"

**Problem**: Wrong Google Sheet ID.

**Solution**:
1. Open your Google Sheet
2. Check the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
3. Copy the `SHEET_ID` part (between `/d/` and `/edit`)
4. Update `GOOGLE_SHEET_ID` in `.env`

### Error: "Module not found" or Import errors

**Problem**: Python packages not installed.

**Solution**:
```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Security Best Practices

### ✅ DO:
- Keep `credentials.json` and `.env` in `.gitignore` (already done)
- Never commit credentials to Git
- Use different credentials for development and production
- Rotate credentials if they're exposed

### ❌ DON'T:
- Don't share `credentials.json` publicly
- Don't commit `.env` file to Git
- Don't hardcode credentials in code
- Don't use production credentials for testing

---

## Quick Checklist

Before testing, make sure:

- [ ] Google Cloud project created
- [ ] Google Sheets API enabled
- [ ] Google Drive API enabled
- [ ] Service account created
- [ ] Service account key downloaded as `credentials.json`
- [ ] `credentials.json` in `backend/` directory
- [ ] Google Sheet shared with service account email
- [ ] Cloudinary account created
- [ ] Cloudinary credentials copied
- [ ] `.env` file updated with all credentials
- [ ] Google Sheet ID copied to `.env`

---

## Next Steps

Once credentials are set up:

1. **Test the sync**: Use the manual sync endpoint to test
2. **Check sync logs**: View sync history via `/api/sync/status`
3. **Monitor scheduled sync**: Check server logs every 15 minutes
4. **Verify issues created**: Check database or use Issues API

---

## Need Help?

If you encounter issues:

1. Check server logs for detailed error messages
2. Verify all credentials are correct
3. Test each component individually (Google Sheets, Cloudinary)
4. Check that service account has proper permissions
5. Ensure `.env` file is in correct location and format

