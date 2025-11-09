#!/bin/bash
# Reset database (wipe and reapply all migrations)

cd "$(dirname "$0")/.."

echo "⚠️  WARNING: This will delete your database and reapply all migrations!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Delete database file
rm -f app.db

# Run all migrations
alembic upgrade head

echo "✅ Database reset complete!"

