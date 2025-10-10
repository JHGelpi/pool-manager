#!/bin/bash
set -e

echo "📝 Populating all empty files..."

# =============================================================================
# app/database.py
# =============================================================================
cat > app/database.py << 'EOF'
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


# Dependency for routes
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
EOF

# =============================================================================
# app/models/inventory.py
# =============================================================================
cat > app/models/inventory.py << 'EOF'
import uuid
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ChemicalInventory(Base):
    __tablename__ = "chemical_inventory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, index=True)
    quantity_on_hand = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    reorder_threshold = Column(Float, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="inventory_items")
EOF

# =============================================================================
# app/models/task.py
# =============================================================================
cat > app/models/task.py << 'EOF'
import uuid
from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    frequency_days = Column(Integer, nullable=False)
    last_completed_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=False, index=True)
    last_completion_notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
EOF

# =============================================================================
# app/models/alert.py
# =============================================================================
cat > app/models/alert.py << 'EOF'
import uuid
from sqlalchemy import Column, String, Time, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    cadence = Column(String, nullable=False)  # 'daily' or 'weekly'
    _days_of_week = Column('days_of_week', String, nullable=True)  # Comma-separated: "0,2,4"
    alert_time = Column(Time, nullable=False)
    alert_on_low_inventory = Column(Boolean, default=False, nullable=False)
    alert_on_due_tasks = Column(Boolean, default=False, nullable=False)
    last_sent = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    @hybrid_property
    def days_of_week(self):
        """Convert comma-separated string to list of integers"""
        if self._days_of_week:
            return [int(d) for d in self._days_of_week.split(',')]
        return []
    
    @days_of_week.setter
    def days_of_week(self, days_list):
        """Convert list of integers to comma-separated string"""
        if days_list:
            unique_days = sorted(list(set(int(d) for d in days_list)))
            self._days_of_week = ",".join(map(str, unique_days))
        else:
            self._days_of_week = None
EOF

# =============================================================================
# app/models/reading.py
# =============================================================================
cat > app/models/reading.py << 'EOF'
import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Float, Date, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ReadingType(Base):
    __tablename__ = "reading_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    low = Column(Float, nullable=True)  # Recommended low range
    high = Column(Float, nullable=True)  # Recommended high range
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    readings = relationship("Reading", back_populates="reading_type", cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reading_type_id = Column(UUID(as_uuid=True), ForeignKey("reading_types.id"), nullable=False)
    reading_value = Column(Float, nullable=False)
    reading_date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    
    # Relationships
    user = relationship("User", back_populates="readings")
    reading_type = relationship("ReadingType", back_populates="readings")
EOF

# =============================================================================
# docker-compose.yml
# =============================================================================
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: pool_db
    environment:
      POSTGRES_USER: ${DB_USER:-pooluser}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-poolpass}
      POSTGRES_DB: ${DB_NAME:-pooldb}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-pooluser}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - pool_network

  api:
    build: .
    container_name: pool_api
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./static:/app/static
      - ./alembic.ini:/app/alembic.ini
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER:-pooluser}:${DB_PASSWORD:-poolpass}@db:5432/${DB_NAME:-pooldb}
    networks:
      - pool_network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  pool_network:
    driver: bridge
EOF

# =============================================================================
# requirements.txt
# =============================================================================
cat > requirements.txt << 'EOF'
# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
gunicorn==21.2.0
python-multipart==0.0.6

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Configuration
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Authentication
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# Email
aiosmtplib==3.0.1

# Scheduling
apscheduler==3.10.4

# Validation
email-validator==2.1.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
EOF

# =============================================================================
# entrypoint.sh
# =============================================================================
cat > entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h db -U ${DB_USER:-pooluser}; do
  sleep 1
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec gunicorn app.main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
EOF

chmod +x entrypoint.sh

# =============================================================================
# .env file
# =============================================================================
cat > .env << 'EOF'
# Database
DB_USER=pooluser
DB_PASSWORD=poolpass123
DB_NAME=pooldb

# Application
SECRET_KEY=change-this-to-a-secure-random-key-in-production
DEBUG=False
DEFAULT_USER_EMAIL=admin@example.com

# Email (optional - for alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_TLS=True

# Scheduler
SCHEDULER_ENABLED=True
EOF

echo "✅ All files populated successfully!"
echo ""
echo "Next steps:"
echo "1. Review and edit .env file if needed"
echo "2. Stop old containers: cd ../glowing-system && docker-compose down"
echo "3. Return here: cd ../pool-manager"
echo "4. Run: ./setup.sh"

