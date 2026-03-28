#!/bin/bash
set -e

echo "🏏 Starting GullyDream11 Backend..."

# Start Docker services (PostgreSQL + Redis)
echo "Starting Docker services..."
docker-compose up -d db redis

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until docker exec gullydream11-db pg_isready -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
until docker exec gullydream11-redis redis-cli ping > /dev/null 2>&1; do
    sleep 1
done
echo "Redis is ready!"

# Load env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Run migrations
echo "Running database migrations..."
./scripts/run-db-migration.sh migrate

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the backend
echo "Starting FastAPI server on port 8000..."
if [ "$1" = "--no-reload" ]; then
    uv run uvicorn src.app:app --host 0.0.0.0 --port 8000
else
    uv run uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
fi
