# Pool Manager - Complete Deployment Guide

## Table of Contents
1. [Fresh Installation](#fresh-installation)
2. [File Checklist](#file-checklist)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Verification](#verification)
5. [Common Issues](#common-issues)

## Fresh Installation

### Prerequisites
- Linux/macOS/WSL with bash
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Quick Start (3 commands)

```bash
# 1. Clone and enter directory
git clone <your-repo> pool-manager && cd pool-manager

# 2. Run setup script
chmod +x setup.sh && ./setup.sh

# 3. Open in browser
open http://localhost:8000/static/index.html
```

## File Checklist

Create these files in your new project directory:

### Root Directory
```
pool-manager/
├── .env.example                 ✓ Copy from artifact
├── .gitignore                   ✓ Copy from artifact
├── docker-compose.yml           ✓ Copy from artifact
├── Dockerfile                   ✓ Copy from artifact
├── entrypoint.sh                ✓ Copy from artifact (chmod +x)
├── requirements.txt             ✓ Copy from artifact
├── alembic.ini                  ✓ Copy from artifact
├── setup.sh                     ✓ Copy from artifact (chmod +x)
├── README.md                    ✓ Copy from artifact
└── DEPLOYMENT_GUIDE.md          ✓ This file
```

### App Directory
```
app/
├── __init__.py                  ✓ Empty file
├── main.py                      ✓ Copy from artifact
├── config.py                    ✓ Copy from artifact
├── database.py                  ✓ Copy from artifact
├── dependencies.py              ✓ Copy from artifact
├── models/
│   ├── __init__.py             ✓ Copy from artifact
│   ├── user.py                 ✓ Copy from artifact
│   ├── inventory.py            ✓ Copy from artifact
│   ├── task.py                 ✓ Copy from artifact
│   ├── alert.py                ✓ Copy from artifact
│   └── reading.py              ✓ Copy from artifact
├── api/
│   ├── __init__.py             ✓ Empty file
│   └── routes/
│       ├── __init__.py         ✓ Copy from artifact
│       ├── health.py           ✓ Copy from artifact
│       ├── inventory.py        ✓ Copy from artifact
│       ├── tasks.py            ✓ Copy from artifact
│       ├── alerts.py           ✓ Copy from artifact
│       └── readings.py         ✓ Copy from artifact
├── services/
│   ├── __init__.py             ✓ Empty file
│   ├── email.py                ✓ Copy from artifact
│   └── scheduler.py            ✓ Copy from artifact
└── alembic/
    ├── env.py                  ✓ Copy from artifact
    └── versions/
        ├── __init__.py         ✓ Empty file
        └── 001_initial_schema.py ✓ Copy from artifact
```

### Static Directory
```
static/
├── index.html                   ✓ Copy from artifact
├── css/
│   └── styles.css              ✓ Copy from artifact
└── js/
    └── app.js                  ✓ Copy from artifact
```

### Tests Directory (Optional)
```
tests/
├── __init__.py                  ✓ Empty file
├── conftest.py                 ✓ Create if needed
└── test_api.py                 ✓ Create if needed
```

## Step-by-Step Setup

### Step 1: Create Project Structure

```bash
# Create main directory
mkdir pool-manager
cd pool-manager

# Create all subdirectories
mkdir -p app/models app/schemas app/api/routes app/services app/alembic/versions
mkdir -p static/css static/js
mkdir -p tests

# Create __init__.py files
touch app/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/api/__init__.py
touch app/api/routes/__init__.py
touch app/services/__init__.py
touch app/alembic/versions/__init__.py
touch tests/__init__.py
```

### Step 2: Copy Files from Artifacts

Copy each file from the artifacts I created into the appropriate location. Here's the mapping:

**Root files:**
- `.env.example` → `.env.example`
- `.gitignore` → `.gitignore`
- `docker-compose.yml` → `docker-compose.yml`
- `Dockerfile` → `Dockerfile`
- `entrypoint.sh` → `entrypoint.sh`
- `requirements.txt` → `requirements.txt`
- `alembic.ini` → `alembic.ini`
- `setup.sh` → `setup.sh`
- `README.md` → `README.md`

**App files:**
- `app/config.py`
- `app/database.py`
- `app/dependencies.py`
- `app/main.py`

**Model files:**
- `app/models/__init__.py`
- `app/models/user.py`
- `app/models/inventory.py`
- `app/models/task.py`
- `app/models/alert.py`
- `app/models/reading.py`

**Schema files:**
- `app/schemas/__init__.py`
- `app/schemas/user.py`
- `app/schemas/inventory.py`
- `app/schemas/task.py`
- `app/schemas/alert.py`
- `app/schemas/reading.py`

**Route files:**
- `app/api/routes/__init__.py`
- `app/api/routes/health.py`
- `app/api/routes/inventory.py`
- `app/api/routes/tasks.py`
- `app/api/routes/alerts.py`
- `app/api/routes/readings.py`

**Service files:**
- `app/services/email.py`
- `app/services/scheduler.py`

**Alembic files:**
- `app/alembic/env.py`
- `app/alembic/versions/001_initial_schema.py`

**Frontend files:**
- `static/index.html`
- `static/css/styles.css`
- `static/js/app.js`

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secret key
openssl rand -hex 32

# Edit .env file
nano .env  # or your preferred editor
```

Update these values in `.env`:
```env
DB_PASSWORD=your_secure_password_here
SECRET_KEY=paste_generated_key_here
DEFAULT_USER_EMAIL=your_email@example.com

# Optional: Configure SMTP for email alerts
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_gmail@gmail.com
```

### Step 4: Make Scripts Executable

```bash
chmod +x setup.sh
chmod +x entrypoint.sh
```

### Step 5: Run Setup

```bash
./setup.sh
```

This will:
- Build Docker containers
- Start PostgreSQL database
- Run database migrations
- Seed default data
- Start the API server

### Step 6: Access Application

Open your browser to:
- **Frontend:** http://localhost:8000/static/index.html
- **API Docs:** http://localhost:8000/docs

Default login:
- Email: `admin@example.com`
- Password: `admin123`

## Verification

### 1. Check Services Status

```bash
docker-compose ps
```

Expected output:
```
NAME       IMAGE              STATUS       PORTS
pool_api   pool-manager-api   Up (healthy) 0.0.0.0:8000->8000/tcp
pool_db    postgres:15-alpine Up (healthy) 5432/tcp
```

### 2. Check API Health

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

### 3. Check Database

```bash
docker-compose exec api alembic current
```

Expected: `001_initial (head)`

### 4. Verify Reading Types

```bash
curl http://localhost:8000/readings/types
```

Expected: Array of 8 reading types

### 5. Check Logs

```bash
docker-compose logs api --tail 50
```

Look for:
- ✓ Scheduler started
- INFO: Application startup complete

## Common Issues

### Issue 1: Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Issue 2: Database Connection Failed

**Error:** `could not connect to server`

**Solution:**
```bash
# Check database is running
docker-compose ps db

# Restart database
docker-compose restart db

# Check logs
docker-compose logs db
```

### Issue 3: Migration Failed

**Error:** `Target database is not up to date`

**Solution:**
```bash
# Check current migration
docker-compose exec api alembic current

# Run migrations
docker-compose exec api alembic upgrade head

# If still failing, reset database
docker-compose down -v
docker-compose up -d
```

### Issue 4: Permission Denied on Scripts

**Error:** `permission denied: ./setup.sh`

**Solution:**
```bash
chmod +x setup.sh entrypoint.sh
```

### Issue 5: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Rebuild containers
docker-compose down
docker-compose up --build
```

### Issue 6: Can't Access Frontend

**Error:** 404 when accessing /static/index.html

**Solution:**
```bash
# Check static files exist
ls -la static/

# Check volume mounting in docker-compose.yml
# Should have:
#   - ./static:/app/static

# Restart
docker-compose restart api
```

## Manual Installation (Without Docker)

If you prefer to run without Docker:

### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
```

### 2. Create Database

```bash
sudo -u postgres psql
CREATE DATABASE pooldb;
CREATE USER pooluser WITH PASSWORD 'poolpass';
GRANT ALL PRIVILEGES ON DATABASE pooldb TO pooluser;
\q
```

### 3. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
# Set DATABASE_URL=postgresql+asyncpg://pooluser:poolpass@localhost:5432/pooldb
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

### Additional Security for Production

1. **Change default password immediately**
2. **Use strong SECRET_KEY** (openssl rand -hex 32)
3. **Use HTTPS** (configure reverse proxy)
4. **Restrict CORS origins** in `app/main.py`
5. **Set DEBUG=False** in `.env`
6. **Use environment secrets** (not .env file)
7. **Regular backups** of PostgreSQL database

### Recommended Production Stack

- **Reverse Proxy:** Nginx or Traefik
- **SSL:** Let's Encrypt
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack or Loki
- **Backups:** Automated PostgreSQL dumps

### Environment Variables for Production

```env
DEBUG=False
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/pooldb
SECRET_KEY=production-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Backup and Restore

### Backup Database

```bash
# Create backup
docker-compose exec db pg_dump -U pooluser pooldb > backup.sql

# With timestamp
docker-compose exec db pg_dump -U pooluser pooldb > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Stop API
docker-compose stop api

# Restore
docker-compose exec -T db psql -U pooluser pooldb < backup.sql

# Start API
docker-compose start api
```

## Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose down
docker-compose up --build -d

# Run any new migrations
docker-compose exec api alembic upgrade head
```

## Support

If you encounter issues:

1. Check this guide first
2. Review logs: `docker-compose logs -f`
3. Check GitHub issues
4. Create new issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Relevant logs

## Next Steps

After successful deployment:

1. ✓ Change default admin password
2. ✓ Create your first maintenance task
3. ✓ Add chemical inventory items
4. ✓ Record your first water reading
5. ✓ Set up email alerts (optional)
6. ✓ Explore the API docs at /docs

---

**Congratulations! Your Pool Manager is ready to use! 🎉**

│   ├── alert.py                ✓ Copy from artifact
│   └── reading.py              ✓ Copy from artifact
├── schemas/
│   ├── __init__.py             ✓ Copy from artifact
│   ├── user.py                 ✓ Copy from artifact
│   ├── inventory.py            ✓ Copy from artifact
│   ├── task.py