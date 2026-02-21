#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Check if seed data exists, if not, seed the database
echo "Checking if database needs seeding..."
NEEDS_SEED=$(python -c "
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        print('NEEDS_SEED' if user is None else 'ALREADY_SEEDED')

asyncio.run(check())
" 2>/dev/null || echo "NEEDS_SEED")

if [ "$NEEDS_SEED" != "ALREADY_SEEDED" ]; then
    echo "Seeding database..."
    python seed.py
else
    echo "Database already seeded."
fi

# Start the server
echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
