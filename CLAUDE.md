# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pool Manager is a comprehensive pool maintenance management system built with FastAPI (async Python), PostgreSQL, and vanilla JavaScript. It tracks maintenance tasks, chemical inventory, water readings, and sends automated alerts.

**Key Features:**
- Recurring maintenance task scheduling with automatic due date calculation
- Chemical inventory management with low stock alerts
- Water chemistry readings with visualization (Chart.js)
- Email alerts via APScheduler (runs every 5 minutes)
- Mobile-responsive vanilla JS frontend

## Architecture

### Backend Structure

The application uses **async SQLAlchemy 2.0** throughout with a layered architecture:

```
app/
├── main.py              # FastAPI app with lifespan for scheduler
├── config.py            # Pydantic settings (env-based config)
├── database.py          # Async engine & session factory
├── dependencies.py      # Auth dependency (currently single-user mode)
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── api/routes/          # FastAPI routers
└── services/
    ├── scheduler.py     # APScheduler jobs
    └── email.py         # SMTP email sending
```

### Database Models

All models use UUID primary keys and cascade delete:

- **User**: email, hashed_password (bcrypt)
- **MaintenanceTask**: recurring tasks with frequency_days, next_due_date auto-calculated
- **ChemicalInventory**: items with reorder_threshold for alerts
- **Alert**: configurable email alerts (daily/weekly) for inventory + tasks
- **ReadingType**: predefined types (pH, chlorine, etc.) - seeded in migrations
- **Reading**: time-series water chemistry data

### Key Design Patterns

**Async Database Access**: All routes use `async def` with AsyncSession from `get_db()` dependency. Always use:
```python
result = await db.execute(select(Model).where(...))
items = result.scalars().all()  # or .scalar_one_or_none()
```

**Authentication**: Currently uses `get_current_user()` dependency that returns the default user from `settings.DEFAULT_USER_EMAIL`. No JWT tokens yet - this is a roadmap item.

**Scheduler**: APScheduler runs in the FastAPI lifespan context. The `check_alerts()` job runs every 5 minutes and sends emails if conditions match (app/services/scheduler.py:10-78).

**Task Completion Logic**: When marking a task complete via `POST /tasks/{id}/complete`, the system:
1. Records last_completed_date and notes
2. Auto-calculates next_due_date = today + frequency_days (app/api/routes/tasks.py:94-118)

## Development Commands

### Running the Application

**With Docker (recommended):**
```bash
docker-compose up --build              # Start all services
docker-compose logs -f api             # View API logs
docker-compose logs -f db              # View database logs
docker-compose down                    # Stop services
docker-compose down -v                 # Stop and remove volumes
```

**Locally (without Docker):**
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations

```bash
# With Docker
docker-compose exec api alembic revision -m "description"
docker-compose exec api alembic upgrade head
docker-compose exec api alembic current
docker-compose exec api alembic history
docker-compose exec api alembic downgrade -1

# Locally
alembic revision -m "description"
alembic upgrade head
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U pooluser -d pooldb

# Backup
docker-compose exec db pg_dump -U pooluser pooldb > backup.sql

# Restore
docker-compose exec -T db psql -U pooluser pooldb < backup.sql
```

### Testing

```bash
# With Docker
docker-compose exec api pytest

# With coverage
docker-compose exec api pytest --cov=app

# Locally
pytest
```

## Important Implementation Notes

### Adding New Routes

1. Create model in `app/models/` (inherit from Base, use UUID, add relationships)
2. Create Pydantic schemas in `app/schemas/` (Create/Update/Response variants)
3. Create router in `app/api/routes/` with prefix and tags
4. Import and register in `app/main.py` via `app.include_router()`
5. Create migration: `alembic revision -m "add_table_name"`
6. Update models `__init__.py` to export new model

### Database Session Management

- Always use `db: AsyncSession = Depends(get_db)` in route signatures
- The session auto-closes after request via try/finally in database.py:24-29
- Never manually manage sessions - the dependency handles lifecycle

### Migrations Best Practices

- All tables must be created in migrations, not via `Base.metadata.create_all()`
- Current schema is in `app/alembic/versions/001_initial_schema.py`
- Second migration `002_unique_task_names.py` adds unique constraint
- Seed data (reading types, default user) lives in migrations

### Configuration

Environment variables are loaded via Pydantic Settings (app/config.py):
- Database: DB_USER, DB_PASSWORD, DB_NAME
- Auth: SECRET_KEY, DEFAULT_USER_EMAIL
- Email: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_TLS
- App: DEBUG, SCHEDULER_ENABLED

Default user credentials (change in production):
- Email: admin@example.com
- Password: admin123
- Hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqRY7TRqOu

### Frontend Integration

- Frontend is vanilla JS in `static/` (no framework)
- Served via FastAPI's StaticFiles mount at `/static`
- API calls use fetch() to relative paths
- Access at http://localhost:8000/static/index.html

## Common Troubleshooting

**Port 8000 already in use:**
```bash
lsof -i :8000  # Find process
kill -9 <PID>  # Or change port in docker-compose.yml
```

**Database connection failed:**
```bash
docker-compose ps              # Check db is running
docker-compose restart db      # Restart if needed
```

**Module not found errors:**
```bash
docker-compose down
docker-compose up --build      # Rebuild from scratch
```

**Migration out of sync:**
```bash
docker-compose exec api alembic current
docker-compose exec api alembic upgrade head
```

## API Endpoints

Key routes (all require implicit user auth):
- `GET/POST /tasks/` - List/create maintenance tasks
- `POST /tasks/{id}/complete` - Mark complete (auto-calculates next due)
- `GET/POST /inventory/` - Manage chemical inventory
- `GET /readings/types` - List reading types (seeded data)
- `GET/POST /readings/` - Record water chemistry
- `GET/POST /alerts/` - Configure email alerts
- `GET /health` - Health check
- `GET /readyz` - Readiness check (includes DB)

## Roadmap Items

Per README.md:
- JWT authentication (currently single-user mode)
- Multi-pool support
- Export to CSV/PDF
- Chemical dosage calculator
- Weather integration
- Equipment maintenance tracking
- Cost tracking
