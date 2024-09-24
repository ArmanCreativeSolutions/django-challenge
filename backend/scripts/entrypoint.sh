#!/bin/bash

# Wait for the database and other services to start
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Wait for the cache backend and message broker services to start
echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 0.1
done
echo "RabbitMQ started"

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis started"

# Lint and Format code
echo "Running linter..."
ruff format
ruff check --fix

# Apply migrations
echo "Applying migrations..."
python /backend/manage.py migrate

# Run tests if in a testing environment
if [ "$DJANGO_ENV" == "testing" ]; then
    echo "Running tests..."
    python /backend/manage.py test
fi

# Collect static files
echo "Collecting static files..."
python /backend/manage.py collectstatic --noinput

# Start supervisord, which manages Django and Celery
echo "Starting supervisord..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
