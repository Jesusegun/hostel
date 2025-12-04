# Database Models

This directory contains all SQLAlchemy database models (tables).

## Models Overview

### 1. Hall (`hall.py`)
Represents a hostel/hall in the university.

**Fields:**
- `id` - Primary key
- `name` - Hall name (e.g., "Levi", "Integrity")
- `created_at` - When the hall was added

**Relationships:**
- One hall has many users (hall admins)
- One hall has many issues

---

### 2. Category (`category.py`)
Represents issue categories (types of problems).

**Fields:**
- `id` - Primary key
- `name` - Category name (e.g., "Plumbing", "Electrical")
- `is_active` - Whether the category is active
- `created_at` - When the category was created

**Relationships:**
- One category has many issues

---

### 3. User (`user.py`)
Represents system users (hall admins and admin users).

**Fields:**
- `id` - Primary key
- `username` - Login username
- `password_hash` - Bcrypt hashed password
- `email` - Email for password recovery (optional)
- `role` - "hall_admin" or "admin"
- `hall_id` - Associated hall (only for hall admins)
- `is_active` - Whether the account is active
- `created_at` - When the account was created
- `updated_at` - When the account was last updated

**Relationships:**
- One user belongs to one hall (if hall_admin)
- One user can resolve many issues
- One user can create many audit logs

**User Roles:**
- **Hall Admin:** Manages issues for their specific hall
- **Admin:** Manages all halls and system settings

---

### 4. Issue (`issue.py`)
Represents a repair issue submitted by a student.

**Fields:**
- `id` - Primary key
- `google_form_timestamp` - When the form was submitted
- `student_email` - Student's email
- `student_name` - Student's name (optional)
- `hall_id` - Which hall the issue is in
- `room_number` - Room number
- `category_id` - Issue category
- `description` - Detailed description
- `image_url` - Cloudinary URL of the image
- `status` - "pending", "in_progress", or "done"
- `resolved_at` - When the issue was resolved
- `resolved_by` - User who resolved the issue
- `created_at` - When the issue was created
- `updated_at` - When the issue was last updated

**Relationships:**
- One issue belongs to one hall
- One issue belongs to one category
- One issue is resolved by one user
- One issue has many audit logs

**Issue Statuses:**
- **Pending:** Just submitted, not started yet
- **In Progress:** Being worked on
- **Done:** Completed/resolved

---

### 5. AuditLog (`audit_log.py`)
Tracks all changes made to issues.

**Fields:**
- `id` - Primary key
- `issue_id` - Which issue was changed
- `user_id` - Who made the change
- `action` - Type of action (e.g., "status_change")
- `old_value` - Previous value
- `new_value` - New value
- `details` - Additional details
- `timestamp` - When the change was made

**Relationships:**
- One audit log belongs to one issue
- One audit log belongs to one user

---

## Database Relationships Diagram

```
┌─────────────┐
│    Hall     │
│             │
│ - id        │
│ - name      │
└──────┬──────┘
       │
       │ 1:N
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│    User     │    │   Issue     │
│             │    │             │
│ - id        │    │ - id        │
│ - username  │    │ - hall_id   │
│ - role      │    │ - category_id
│ - hall_id   │    │ - status    │
└──────┬──────┘    └──────┬──────┘
       │                  │
       │                  │ N:1
       │                  ▼
       │           ┌─────────────┐
       │           │  Category   │
       │           │             │
       │           │ - id        │
       │           │ - name      │
       │           └─────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐
│  AuditLog   │
│             │
│ - id        │
│ - issue_id  │
│ - user_id   │
│ - action    │
└─────────────┘
```

---

## Initialization

To create all tables and seed initial data:

```bash
python -m app.init_db
```

This will:
1. Create all 5 tables
2. Seed 11 halls
3. Seed 10 categories
4. Seed 13 users (11 hall admins + 2 admin users)

Default password for all users: `changeme123`

---

## Usage Examples

### Query Examples

```python
from app.database import SessionLocal
from app.models import Hall, User, Issue

db = SessionLocal()

# Get all halls
halls = db.query(Hall).all()

# Get a specific user
user = db.query(User).filter(User.username == "levi").first()

# Get all pending issues for a hall
issues = db.query(Issue).filter(
    Issue.hall_id == 1,
    Issue.status == "pending"
).all()

# Get issues with related data
issues = db.query(Issue).join(Hall).join(Category).all()
for issue in issues:
    print(f"{issue.hall.name} - {issue.category.name} - {issue.status}")
```

### Create Examples

```python
# Create a new issue
issue = Issue(
    student_email="student@example.com",
    hall_id=1,
    room_number="A205",
    category_id=1,
    description="Leaking pipe",
    status="pending"
)
db.add(issue)
db.commit()

# Update issue status
issue.status = "in_progress"
db.commit()

# Create audit log
log = AuditLog(
    issue_id=issue.id,
    user_id=1,
    action="status_change",
    old_value="pending",
    new_value="in_progress"
)
db.add(log)
db.commit()
```

---

## Notes

- All timestamps use UTC timezone
- Passwords are hashed with bcrypt (never store plain text!)
- Foreign keys use CASCADE or SET NULL for deletions
- Indexes are added on frequently queried columns
- All models have `to_dict()` methods for API responses

