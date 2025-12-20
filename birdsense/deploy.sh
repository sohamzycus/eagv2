#!/bin/bash
# 🐦 BirdSense Deployment Script
# Developed by Soham
#
# Usage:
#   ./deploy.sh local   - Run locally with Ollama
#   ./deploy.sh docker  - Run in Docker containers
#   ./deploy.sh cloud   - Deploy to Google Cloud Run

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
    docker run -d -p 7860:7860 --name birdsense-app birdsense
    
    echo ""
    echo -e "${GREEN}✅ Running at: http://localhost:7860${NC}"
    echo ""
    echo "To stop: docker stop birdsense-app && docker rm birdsense-app"
}

deploy_cloud() {
    echo -e "${BLUE}☁️  Deploy to Google Cloud Run${NC}"
    echo ""
    echo "Google Cloud Run: FREE tier with 2GB RAM (enough for BirdNET)"
    echo ""
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${YELLOW}Installing gcloud CLI...${NC}"
        echo "Visit: https://cloud.google.com/sdk/docs/install"
        echo ""
        echo "After install, run:"
        echo "  gcloud auth login"
        echo "  ./deploy.sh cloud"
        exit 1
    fi
    
    echo -e "${GREEN}Deploying to Google Cloud Run...${NC}"
    echo ""
    
    # Deploy
    gcloud run deploy birdsense \
        --source=. \
        --region=us-central1 \
        --memory=2Gi \
        --cpu=1 \
        --timeout=300 \
        --allow-unauthenticated \
        --port=7860
    
    echo ""
    echo -e "${GREEN}✅ Deployed! Your URL is shown above.${NC}"
}

show_help() {
    echo "Usage: ./deploy.sh [local|docker|cloud]"
    echo ""
    echo "Options:"
    echo -e "  ${GREEN}local${NC}   - Run on your machine with Ollama"
    echo -e "  ${GREEN}docker${NC}  - Build and run Docker container locally"
    echo -e "  ${GREEN}cloud${NC}   - Deploy to Google Cloud Run (FREE tier)"
    echo ""
    echo "All options include full BirdNET + TensorFlow!"
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
