#!/bin/bash
# 🐦 BirdSense Deployment Script
# Developed by Soham
#
# Usage:
#   ./deploy.sh local   - Run locally with Ollama
#   ./deploy.sh docker  - Run in Docker containers
#   ./deploy.sh cloud   - Deploy to cloud (FREE options)

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
    
    if ! command -v python3.12 &> /dev/null; then
        echo -e "${RED}❌ Python 3.12 required. Install with: brew install python@3.12${NC}"
        exit 1
    fi
    
    if ! command -v ollama &> /dev/null; then
        echo -e "${YELLOW}⚠️ Ollama not found. Installing...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ollama
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    fi
    
    echo -e "${GREEN}🚀 Starting Ollama...${NC}"
    ollama serve &> /dev/null &
    sleep 3
    
    echo -e "${GREEN}📥 Pulling AI models...${NC}"
    ollama pull llava:7b
    ollama pull phi4
    
    echo -e "${GREEN}🐍 Setting up Python environment...${NC}"
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo "🚀 Starting BirdSense..."
    python app.py
}

deploy_docker() {
    echo -e "${YELLOW}🐳 Setting up Docker deployment...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker required. Install from https://docker.com${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🔨 Building Docker image (includes BirdNET + TensorFlow)...${NC}"
    docker build -t birdsense .
    
    echo -e "${GREEN}🚀 Starting container...${NC}"
    docker run -d -p 7860:7860 --name birdsense-app \
        -e GROQ_API_KEY="${GROQ_API_KEY:-}" \
        birdsense
    
    echo ""
    echo -e "${GREEN}✅ Running at: http://localhost:7860${NC}"
    echo ""
    echo "To stop: docker stop birdsense-app && docker rm birdsense-app"
}

deploy_cloud() {
    echo -e "${BLUE}☁️  Cloud Deployment Options${NC}"
    echo ""
    echo "Your Docker image includes BirdNET + TensorFlow (~1.5GB)."
    echo "Choose a platform that supports larger containers:"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}OPTION 1: Google Cloud Run (RECOMMENDED - FREE)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ FREE: 2 million requests/month"
    echo "✅ 2GB RAM (enough for BirdNET + TensorFlow)"
    echo "✅ Auto-deploy from GitHub"
    echo ""
    echo "Steps:"
    echo "  1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    echo "  2. Run these commands:"
    echo ""
    echo "     gcloud auth login"
    echo "     gcloud projects create birdsense-app --name='BirdSense'"
    echo "     gcloud config set project birdsense-app"
    echo "     gcloud services enable run.googleapis.com"
    echo ""
    echo "     # Build and deploy"
    echo "     gcloud run deploy birdsense \\"
    echo "       --source=. \\"
    echo "       --region=us-central1 \\"
    echo "       --memory=2Gi \\"
    echo "       --allow-unauthenticated \\"
    echo "       --set-env-vars=GROQ_API_KEY=\$GROQ_API_KEY"
    echo ""
    echo "  3. Your URL: https://birdsense-xxxxx.run.app"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}OPTION 2: Fly.io (FREE tier)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ FREE: 3 shared VMs"
    echo "✅ 1GB RAM (may need to optimize)"
    echo ""
    echo "  flyctl launch --dockerfile Dockerfile"
    echo "  flyctl secrets set GROQ_API_KEY=xxx"
    echo "  flyctl deploy"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}OPTION 3: Railway.app${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ \$5 free credits (enough for testing)"
    echo "✅ Easy GitHub integration"
    echo ""
    echo "  1. Go to https://railway.app"
    echo "  2. New Project → Deploy from GitHub"
    echo "  3. Add GROQ_API_KEY in Variables"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}Get FREE Groq API key: https://console.groq.com${NC}"
    echo "(Used as fallback when Ollama not available)"
}

show_help() {
    echo "Usage: ./deploy.sh [local|docker|cloud]"
    echo ""
    echo "Options:"
    echo -e "  ${GREEN}local${NC}   - Run on your machine with Ollama (best accuracy)"
    echo -e "  ${GREEN}docker${NC}  - Build and run Docker container locally"
    echo -e "  ${GREEN}cloud${NC}   - Deploy to cloud (Google Cloud Run, Fly.io, Railway)"
    echo ""
    echo "All options include full BirdNET + TensorFlow for best accuracy!"
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
