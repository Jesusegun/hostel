# Hostel Repair Management System - Backend

FastAPI backend for the Hostel Repair Management System.

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
# Copy the example file
copy env.example .env  # Windows
cp env.example .env    # Mac/Linux

# Edit .env and fill in your values
```

### 4. Set Up Database

```bash
# Make sure PostgreSQL is running
# Create database: hostel_repairs

# Run migrations (we'll set this up later)
alembic upgrade head
```

### 5. Run the Server

```bash
# Development mode (auto-reload on code changes)
uvicorn app.main:app --reload --port 8000

# Or use Python directly
python -m app.main
```

### 6. Access API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/api/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models (tables)
│   ├── schemas/             # Pydantic schemas (validation)
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── env.example              # Environment variables template
└── .gitignore              # Git ignore rules
```

## 🔧 Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Style

We follow PEP 8 style guide. Format code with:

```bash
black app/
```

## 📚 Tech Stack

- **FastAPI 0.104+** - Web framework
- **SQLAlchemy 2.0+** - ORM
- **PostgreSQL 15+** - Database
- **Pydantic 2.0+** - Data validation
- **Alembic** - Database migrations
- **Python 3.12** - Programming language

## 🔐 Environment Variables

See `env.example` for all required environment variables.

**Critical Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `GOOGLE_SHEET_ID` - Google Sheet ID for form submissions
- `CLOUDINARY_*` - Cloudinary credentials for image storage
- `SMTP_*` - SMTP server configuration (host, port, user, password)

## 📖 API Documentation

Once the server is running, visit:
- http://localhost:8000/api/docs

FastAPI automatically generates interactive API documentation.

### Notable Endpoints

- `POST /api/auth/login` – Obtain JWT token
- `GET /api/issues/stats` – Hall/admin issue statistics
- `GET /api/dashboard/summary` – **Admin-only** analytics payload (KPIs, hall/category breakdowns, timeline data)

## 🚀 Deployment

See `HOSTEL_REPAIR_SYSTEM_CONTEXT.md` section 8.3 for deployment instructions.

## 📝 License

Internal university project.

