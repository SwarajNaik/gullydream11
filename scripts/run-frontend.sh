#!/bin/bash
set -e

echo "🏏 Starting GullyDream11 Frontend..."

# Load root .env and generate frontend/.env.local
if [ -f .env ]; then
    echo "Generating frontend/.env.local from root .env..."
    grep '^NEXT_PUBLIC_' .env > frontend/.env.local 2>/dev/null || true
    echo "Frontend .env.local generated."
fi

# Install dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Kill any existing process on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start frontend
echo "Starting Next.js dev server on port 3000..."
cd frontend && npm run dev
