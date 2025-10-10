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
