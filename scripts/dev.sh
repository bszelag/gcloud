#!/bin/bash

set -e

echo "Running app locally"
echo "========================================"

show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start development environment"
    echo "  stop      - Stop development environment"
    echo "  build     - Build Docker images"
    echo "  clean     - Clean up containers and volumes"
    echo "  migrate   - Run database migrations"
    echo "  init-db   - Initialize database (wait for ready and run migrations)"
    echo "  help      - Show this help message"
}

start_dev() {
    echo "Starting development environment..."
    
    if ! docker info > /dev/null 2>&1; then
        echo "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    docker compose up -d --build
    
    ./scripts/init-db.sh
    
    echo "Development environment started!"
    echo "API: http://localhost:8000"
    echo "Docs: http://localhost:8000/docs"
    echo "Health: http://localhost:8000/health"
    echo "Database: localhost:5432"
}

stop_dev() {
    echo "Stopping development environment..."
    docker compose down
    echo "Development environment stopped!"
}

build_images() {
    echo "Building Docker images..."
    docker compose build --no-cache
    echo "Images built successfully!"
}

clean_up() {
    echo "Cleaning up containers and volumes..."
    docker compose down -v
    docker system prune -f
    echo "Cleanup completed!"
}

run_migrations() {
    echo "Running database migrations..."
    docker compose exec api alembic upgrade head
    echo "Migrations completed!"
}

case "${1:-help}" in
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    build)
        build_images
        ;;
    clean)
        clean_up
        ;;
    migrate)
        run_migrations
        ;;
    init-db)
        ./scripts/init-db.sh
        ;;
    help|*)
        show_usage
        ;;
esac
