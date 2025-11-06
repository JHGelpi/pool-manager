# 🏊 Pool Manager

A comprehensive pool maintenance management system built with FastAPI, PostgreSQL, and modern web technologies.

## Features

- **📋 Task Management** - Schedule and track recurring maintenance tasks
- **🧪 Chemical Inventory** - Monitor chemical levels and get low stock alerts
- **📊 Water Readings** - Record and visualize water chemistry over time
- **📧 Email Alerts** - Automated reminders for low inventory and due tasks
- **📱 Mobile-Friendly** - Responsive design works on all devices

## Feature Requests
- [ ] Equipment manager to record and document the equipment you have and when purchased
- [X] Salinator cleaning task 
- [X] Input of readings to be in a table for quick data entry
- [ ] Take a photo of chemical reading stick and compare to hex colors of target reading
- [X] Reorder the chemistry readings to:
   1. Total Hardness (scale of 0 to 1000, 250-500 is target range)
   2. Free Chlorine (scale of 0-10, 1-3 is target range)
   3. Bromine (scale of 0-20, 2-6 is target range)
   4. Total Chlorine (scale of 0-10, 1-3 is target range)
   5. Cyanuric Acid (scale of 0-240, 30-100 is target range)
   6. Total Alkalinity (scale of 0-240, 80-120 is target range)
   7. pH (scale of 6.2-9.0, 7.2-7.8 is target range)
   8. Salt ppm

## Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- PostgreSQL 15 (database)
- SQLAlchemy 2.0 (async ORM)
- Alembic (database migrations)
- APScheduler (background tasks)

**Frontend:**
- Vanilla JavaScript (no framework overhead)
- Chart.js (data visualization)
- Modern CSS with CSS Grid/Flexbox

**Infrastructure:**
- Docker & Docker Compose
- Gunicorn + Uvicorn workers

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url> pool-manager
cd pool-manager
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Edit `.env` file** with your settings:
```env
# Database
DB_USER=pooluser
DB_PASSWORD=your_secure_password
DB_NAME=pooldb

# Application  
SECRET_KEY=generate-a-random-secret-key
DEFAULT_USER_EMAIL=admin@example.com

# Email (optional - for alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

4. **Start the application**
```bash
docker-compose up --build
```

5. **Access the application**
- Frontend: http://localhost:8000/static/index.html
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Default Login

- Email: `admin@example.com`
- Password: `admin123`

**⚠️ Change this password in production!**

## Project Structure

```
pool-manager/
├── app/
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── api/routes/      # API endpoints
│   ├── services/        # Business logic
│   ├── alembic/         # Database migrations
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   └── main.py          # FastAPI app
├── static/
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript
│   └── index.html       # Frontend
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## API Endpoints

### Health
- `GET /health` - Basic health check
- `GET /readyz` - Readiness check (includes DB)

### Tasks
- `GET /tasks/` - List all tasks
- `POST /tasks/` - Create a task
- `GET /tasks/{id}` - Get task details
- `PUT /tasks/{id}` - Update a task
- `POST /tasks/{id}/complete` - Mark task complete
- `DELETE /tasks/{id}` - Delete a task

### Inventory
- `GET /inventory/` - List all items
- `POST /inventory/` - Add an item
- `GET /inventory/{id}` - Get item details
- `PUT /inventory/{id}` - Update an item
- `DELETE /inventory/{id}` - Delete an item

### Readings
- `GET /readings/types` - List reading types
- `POST /readings/types` - Create reading type
- `GET /readings/?slug={slug}&days={days}` - Get readings
- `POST /readings/` - Create a reading
- `DELETE /readings/{id}` - Delete a reading

### Alerts
- `GET /alerts/` - List all alerts
- `POST /alerts/` - Create an alert
- `DELETE /alerts/{id}` - Delete an alert

## Development

### Running Locally (without Docker)

1. **Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
```

2. **Create database**
```bash
sudo -u postgres psql
CREATE DATABASE pooldb;
CREATE USER pooluser WITH PASSWORD 'poolpass';
GRANT ALL PRIVILEGES ON DATABASE pooldb TO pooluser;
\q
```

3. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Start the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# With Docker
docker-compose exec api pytest

# Locally
pytest
```

### Creating a Migration

```bash
# With Docker
docker-compose exec api alembic revision -m "description"

# Locally
alembic revision -m "description"
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# Database only
docker-compose logs -f db
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | PostgreSQL username | `pooluser` |
| `DB_PASSWORD` | PostgreSQL password | `poolpass` |
| `DB_NAME` | Database name | `pooldb` |
| `SECRET_KEY` | Application secret key | Required |
| `DEBUG` | Enable debug mode | `False` |
| `DEFAULT_USER_EMAIL` | Default user email | `admin@example.com` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `SMTP_FROM_EMAIL` | From email address | - |
| `SMTP_TLS` | Use TLS | `True` |
| `SCHEDULER_ENABLED` | Enable background scheduler | `True` |

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to Google Account → Security
   - 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password as `SMTP_PASSWORD`

## Database Schema

### Reading Types (Default)

| Slug | Name | Unit | Ideal Range |
|------|------|------|-------------|
| `ph` | pH | - | 6.8 - 8.2 |
| `fc` | Free Chlorine | ppm | 0 - 10 |
| `cc` | Combined Chlorine | ppm | 0 - 1 |
| `ta` | Total Alkalinity | ppm | 50 - 180 |
| `ch` | Calcium Hardness | ppm | 100 - 1000 |
| `cya` | Stabilizer (CYA) | ppm | 0 - 200 |
| `salt` | Salt | ppm | 0 - 6000 |
| `temp` | Water Temperature | °F | 30 - 120 |

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs api

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Database connection issues

```bash
# Check if database is ready
docker-compose ps

# Connect to database
docker-compose exec db psql -U pooluser -d pooldb

# Check tables
\dt
```

### Migration issues

```bash
# Check current version
docker-compose exec api alembic current

# View history
docker-compose exec api alembic history

# Downgrade one version
docker-compose exec api alembic downgrade -1
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - feel free to use this project for any purpose.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues first
- Provide detailed information about your environment

## Roadmap

- [ ] User authentication with JWT
- [ ] Multi-pool support
- [ ] Mobile app (React Native)
- [ ] Export data to CSV/PDF
- [ ] Chemical dosage calculator
- [ ] Weather integration
- [ ] Equipment maintenance tracking
- [ ] Cost tracking
- [ ] Historical comparison charts
- [ ] AI-powered recommendations

---

Built with ❤️ for pool owners everywhere