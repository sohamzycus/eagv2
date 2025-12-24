#!/bin/bash
# ============================================
# Prompt Creator - Quick Start Script
# ============================================

# Change to script directory
cd "$(dirname "$0")"

# Zycus Azure OpenAI Configuration
export AZURE_OPENAI_API_KEY="********"
export AZURE_OPENAI_ENDPOINT="https://zycus-ptu.azure-api.net/ptu-intakemanagement"
export AZURE_OPENAI_DEPLOYMENT="gpt4o-130524"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
export AZURE_OPENAI_VERIFY_SSL="false"
export LLM_PROVIDER="azure_openai"
export LLM_MODEL="gpt-4o"

echo "============================================"
echo "Prompt Creator - Starting with Azure OpenAI"
echo "============================================"
echo "Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "Deployment: $AZURE_OPENAI_DEPLOYMENT"
echo "API Version: $AZURE_OPENAI_API_VERSION"
echo ""

# Activate virtual environment
source venv/bin/activate

# Kill any existing process on default port
lsof -ti:7860 | xargs kill -9 2>/dev/null || true

# Run the application
echo "🚀 Opening UI at http://localhost:7860"
python main.py "$@"

