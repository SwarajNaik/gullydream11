#!/bin/bash
set -e

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Convert async URL to sync for Alembic (asyncpg -> psycopg2)
SYNC_DB_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+asyncpg/postgresql/')
export DATABASE_URL="$SYNC_DB_URL"

ACTION=${1:-migrate}

case $ACTION in
    migrate)
        echo "Applying pending migrations..."
        uv run alembic upgrade head
        echo "Migrations applied successfully."
        ;;
    status)
        echo "Current migration status:"
        uv run alembic current
        echo ""
        echo "Migration history:"
        uv run alembic history --verbose
        ;;
    create)
        if [ -z "$2" ]; then
            echo "Usage: $0 create 'migration message'"
            exit 1
        fi
        echo "Creating new migration: $2"
        uv run alembic revision --autogenerate -m "$2"
        echo "Migration created. Review the file in alembic/versions/"
        ;;
    downgrade)
        echo "Rolling back one migration..."
        uv run alembic downgrade -1
        echo "Rollback complete."
        ;;
    reset)
        echo "⚠️  Resetting database to empty state..."
        read -p "Are you sure? (y/N): " confirm
        if [ "$confirm" = "y" ]; then
            uv run alembic downgrade base
            echo "Database reset complete."
        else
            echo "Cancelled."
        fi
        ;;
    *)
        echo "Usage: $0 {migrate|status|create|downgrade|reset}"
        exit 1
        ;;
esac
