#!/bin/bash
# 🐦 BirdSense Deployment Script
# Developed by Soham
#
# Usage:
#   ./deploy.sh local   - Run locally with Ollama (best accuracy)
#   ./deploy.sh docker  - Run in Docker containers
#   ./deploy.sh cloud   - Deploy to Render.com (free, permanent URL)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🐦 BirdSense Deployment"
echo "======================="
echo ""

MODE=${1:-help}

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
    echo "To stop: docker-compose down"
}

deploy_cloud() {
    echo -e "${BLUE}☁️  Cloud Deployment (Render.com + Groq FREE API)${NC}"
    echo ""
    echo "Render.com offers FREE Docker hosting with auto-deploy from GitHub."
    echo "Groq offers FREE AI API (no credit card required!)."
    echo ""
    echo -e "${YELLOW}Step 1: Get FREE Groq API Key${NC}"
    echo "   Go to: https://console.groq.com"
    echo "   Sign up (no credit card!) and copy your API key"
    echo ""
    echo -e "${YELLOW}Step 2: Deploy to Render.com${NC}"
    echo "   1. Go to https://render.com"
    echo "   2. Click 'New' → 'Web Service'"
    echo "   3. Connect your GitHub repo: sohamzycus/eagv2"
    echo "   4. Settings:"
    echo "      - Name: birdsense"
    echo "      - Root Directory: birdsense"
    echo "      - Runtime: Docker"
    echo "   5. Add Environment Variable:"
    echo "      - Key: GROQ_API_KEY"
    echo "      - Value: (your FREE Groq key)"
    echo "   6. Click 'Create Web Service'"
    echo ""
    echo -e "${GREEN}✅ Done! Every push to master auto-deploys.${NC}"
    echo ""
    echo -e "${YELLOW}Your permanent URL:${NC} https://birdsense.onrender.com"
    echo ""
    echo "Alternative free platforms:"
    echo "  - Railway.app (free tier)"
    echo "  - Fly.io (free tier)"
    echo "  - Google Cloud Run (free tier)"
}

show_help() {
    echo "Usage: ./deploy.sh [local|docker|cloud]"
    echo ""
    echo "Options:"
    echo -e "  ${GREEN}local${NC}   - Run on your machine with Ollama (best accuracy)"
    echo -e "  ${GREEN}docker${NC}  - Run in Docker containers (portable)"
    echo -e "  ${GREEN}cloud${NC}   - Deploy to Render.com (free, permanent URL, auto-deploy)"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh local   # For development/testing"
    echo "  ./deploy.sh cloud   # For sharing with testers"
}

case $MODE in
    local)
        deploy_local
        ;;
    docker)
        deploy_docker
        ;;
    cloud)
        deploy_cloud
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac
