#!/bin/bash
# BirdSense Deployment Script
# Developed by Soham
#
# Usage: ./deploy.sh [local|docker]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🐦 BirdSense Deployment"
echo "======================="
echo ""

MODE=${1:-local}

deploy_local() {
    echo -e "${YELLOW}📦 Setting up local deployment...${NC}"
    
    # Check Python version
    if ! command -v python3.12 &> /dev/null; then
        echo -e "${RED}❌ Python 3.12 required. Install with: brew install python@3.12${NC}"
        exit 1
    fi
    
    # Check Ollama
    if ! command -v ollama &> /dev/null; then
        echo -e "${YELLOW}⚠️ Ollama not found. Installing...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ollama
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    fi
    
    # Start Ollama
    echo -e "${GREEN}🚀 Starting Ollama...${NC}"
    ollama serve &> /dev/null &
    sleep 3
    
    # Pull models
    echo -e "${GREEN}📥 Pulling AI models (this may take a while)...${NC}"
    ollama pull llava:7b
    ollama pull phi4
    
    # Create virtual environment
    echo -e "${GREEN}🐍 Setting up Python environment...${NC}"
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Run
    echo ""
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo ""
    echo "🚀 Starting BirdSense..."
    python app.py
}

deploy_docker() {
    echo -e "${YELLOW}🐳 Setting up Docker deployment...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker required. Install from https://docker.com${NC}"
        exit 1
    fi
    
    # Build and run
    echo -e "${GREEN}🔨 Building Docker images...${NC}"
    docker-compose build
    
    echo -e "${GREEN}🚀 Starting services...${NC}"
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo ""
    echo "📍 BirdSense: http://localhost:7860"
    echo "📍 Ollama API: http://localhost:11434"
    echo ""
    echo "⏳ Models are downloading in background..."
    echo "   Check status: docker logs birdsense-model-init"
    echo ""
    echo "To stop: docker-compose down"
}

case $MODE in
    local)
        deploy_local
        ;;
    docker)
        deploy_docker
        ;;
    *)
        echo "Usage: ./deploy.sh [local|docker]"
        echo ""
        echo "Options:"
        echo "  local   - Run directly on your machine (recommended for Mac)"
        echo "  docker  - Run in Docker containers"
        exit 1
        ;;
esac

