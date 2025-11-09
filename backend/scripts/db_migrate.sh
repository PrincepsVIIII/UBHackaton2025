#!/bin/bash
# Database migration script for team use

cd "$(dirname "$0")/.."

echo "Running Alembic migrations..."
alembic upgrade head

echo "✅ Database migrations complete!"

