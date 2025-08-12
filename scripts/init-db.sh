#!/bin/bash

set -e

echo "Initializing database..."

echo "Waiting for database to be ready..."
until docker compose exec -T postgres pg_isready -U birthday_user -d birthday_api; do
    echo "Database is not ready yet. Waiting..."
    sleep 2
done

echo "Database is ready!"

echo "Checking database migration status..."
CURRENT_REVISION=$(docker compose exec -T api alembic current 2>/dev/null | head -n1 | cut -d' ' -f1 || echo "None")
HEAD_REVISION=$(docker compose exec -T api alembic heads 2>/dev/null | head -n1 | cut -d' ' -f1 || echo "None")

if [ "$CURRENT_REVISION" = "$HEAD_REVISION" ] && [ "$CURRENT_REVISION" != "None" ]; then
    echo "Database is up to date (revision: $CURRENT_REVISION)"
else
    echo "Running database migrations..."
    docker compose exec -T api alembic upgrade head
    echo "Migrations completed!"
fi

echo "Database initialization completed!"
