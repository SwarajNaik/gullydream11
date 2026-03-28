#!/bin/bash
set -e

echo "Setting up GullyDream11 development environment..."

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend && npm install && cd ..

# Install pre-commit hooks (if pre-commit is available)
if command -v pre-commit &> /dev/null || uv run pre-commit --version &> /dev/null 2>&1; then
    echo "Installing pre-commit hooks..."
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg
    echo "Pre-commit hooks installed."
else
    echo "Pre-commit not found. Skipping hook installation."
fi

echo "✅ Setup complete! Run './scripts/run-backend.sh' and './scripts/run-frontend.sh' to start."
