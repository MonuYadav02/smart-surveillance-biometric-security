#!/bin/bash

# Smart Surveillance System Startup Script

echo "Starting Smart Surveillance System..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    IS_DOCKER=true
else
    echo "Running on host system"
    IS_DOCKER=false
fi

# Create necessary directories
mkdir -p storage/recordings
mkdir -p storage/motion
mkdir -p storage/emergency
mkdir -p models
mkdir -p logs

# Set permissions
chmod -R 755 storage/
chmod -R 755 models/
chmod -R 755 logs/

# Wait for database to be ready (if using Docker)
if [ "$IS_DOCKER" = true ]; then
    echo "Waiting for database to be ready..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "Database is ready!"
    
    echo "Waiting for Redis to be ready..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is ready!"
fi

# Run database migrations (if needed)
echo "Running database migrations..."
# alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
if [ "$DEBUG" = "true" ]; then
    echo "Starting in development mode..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting in production mode..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
fi