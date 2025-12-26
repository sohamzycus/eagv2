#!/bin/bash
# ============================================
# Prompt Creator - Quick Start Script
# ============================================
# Configuration is loaded from .env file

# Change to script directory
cd "$(dirname "$0")"

echo "============================================"
echo "Prompt Creator"
echo "============================================"

# Check for .env file
if [ -f ".env" ]; then
    echo "✅ Found .env file - credentials will be loaded automatically"
else
    echo "⚠️  No .env file found!"
    echo "   Copy env_template.txt to .env and add your API key"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Kill any existing process on default port
lsof -ti:7860 | xargs kill -9 2>/dev/null || true

# Run the application
echo ""
echo "🚀 Starting UI at http://localhost:7860"
python main.py "$@"

