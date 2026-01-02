#!/bin/bash
# 🐦 BirdSense - GCP Cloud Run Deployment (Web UI + API)
# Developed by Soham
#
# Uses Docker Hub images:
#   - sohamzycus/birdsense (Web UI)
#   - sohamzycus/birdsense-api (REST API)
#
# Prerequisites:
# 1. Docker logged in to Docker Hub
# 2. gcloud CLI authenticated
# 3. LITELLM_API_KEY set
#
# Usage:
#   ./deploy-gcp.sh              # Build, push, and deploy both
#   ./deploy-gcp.sh web          # Deploy web UI only
#   ./deploy-gcp.sh api          # Deploy API only

set -e

# ============ CONFIGURATION ============
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-asia-south1}"  # Mumbai region

# Docker Hub images
DOCKER_USER="sohamzycus"
WEB_IMAGE="${DOCKER_USER}/birdsense"
API_IMAGE="${DOCKER_USER}/birdsense-api"

# Cloud Run services
WEB_SERVICE="birdsense-web"
API_SERVICE="birdsense-api"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}🐦 BirdSense - GCP Cloud Run Deployment${NC}"
echo "=========================================="
echo -e "Docker Hub: ${GREEN}${DOCKER_USER}${NC}"
echo -e "GCP Region: ${GREEN}${REGION}${NC}"
echo ""

# ============ CHECK PREREQUISITES ============
check_prerequisites() {
    echo -e "${BLUE}[1/4]${NC} Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found.${NC}"
        exit 1
    fi
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found.${NC}"
        exit 1
    fi
    
    # Check Docker Hub login
    if ! docker info 2>/dev/null | grep -q "Username"; then
        echo -e "${YELLOW}⚠️  Not logged into Docker Hub. Running 'docker login'...${NC}"
        docker login
    fi
    
    # Check API key
    # API Key - MUST be set as environment variable (never commit to git!)
    if [ -z "$LITELLM_API_KEY" ]; then
        echo -e "${RED}❌ LITELLM_API_KEY not set.${NC}"
        echo "Export it first: export LITELLM_API_KEY='your-api-key'"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Prerequisites OK"
}

# ============ BUILD AND PUSH WEB IMAGE ============
build_web() {
    echo ""
    echo -e "${BLUE}[2/4]${NC} Building Web UI image..."
    
    cd "$(dirname "$0")"
    
    # Build for linux/amd64
    docker buildx build \
        --platform linux/amd64 \
        -t ${WEB_IMAGE}:latest \
        --push \
        .
    
    echo -e "${GREEN}✓${NC} Pushed ${WEB_IMAGE}:latest"
}

# ============ BUILD AND PUSH API IMAGE ============
build_api() {
    echo ""
    echo -e "${BLUE}[3/4]${NC} Building API image..."
    
    cd "$(dirname "$0")"
    
    # Use same Dockerfile with RUN_MODE=api
    docker buildx build \
        --platform linux/amd64 \
        -t ${API_IMAGE}:latest \
        --push \
        .
    
    echo -e "${GREEN}✓${NC} Pushed ${API_IMAGE}:latest"
}

# ============ DEPLOY WEB TO CLOUD RUN ============
deploy_web() {
    echo ""
    echo -e "${BLUE}[4/4]${NC} Deploying Web UI to Cloud Run..."
    
    gcloud run deploy ${WEB_SERVICE} \
        --image docker.io/${WEB_IMAGE}:latest \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --memory 4Gi \
        --cpu 2 \
        --timeout 300 \
        --min-instances 0 \
        --max-instances 5 \
        --port 7860 \
        --set-env-vars "RUN_MODE=gradio" \
        --set-env-vars "IS_AZURE=true" \
        --set-env-vars "LITELLM_API_KEY=${LITELLM_API_KEY}" \
        --set-env-vars "LITELLM_API_BASE=https://zycus-ptu.azure-api.net/ptu-intakemanagement" \
        --set-env-vars "AZURE_DEPLOYMENT=gpt4o-130524" \
        --set-env-vars "AZURE_API_VERSION=2024-02-15-preview" \
        --set-env-vars "LITELLM_VISION_MODEL=gpt-4o" \
        --set-env-vars "LITELLM_TEXT_MODEL=gpt-4o" \
        --set-env-vars "GRADIO_SERVER_NAME=0.0.0.0" \
        --set-env-vars "GRADIO_SERVER_PORT=7860"
    
    WEB_URL=$(gcloud run services describe ${WEB_SERVICE} --region ${REGION} --format 'value(status.url)')
    echo -e "${GREEN}✓${NC} Web UI: ${WEB_URL}"
}

# ============ DEPLOY API TO CLOUD RUN ============
deploy_api() {
    echo ""
    echo -e "${BLUE}[4/4]${NC} Deploying REST API to Cloud Run..."
    
    JWT_SECRET=$(openssl rand -hex 32)
    
    gcloud run deploy ${API_SERVICE} \
        --image docker.io/${API_IMAGE}:latest \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --memory 4Gi \
        --cpu 2 \
        --timeout 300 \
        --min-instances 0 \
        --max-instances 10 \
        --port 8000 \
        --set-env-vars "RUN_MODE=api" \
        --set-env-vars "IS_AZURE=true" \
        --set-env-vars "LITELLM_API_KEY=${LITELLM_API_KEY}" \
        --set-env-vars "LITELLM_API_BASE=https://zycus-ptu.azure-api.net/ptu-intakemanagement" \
        --set-env-vars "AZURE_DEPLOYMENT=gpt4o-130524" \
        --set-env-vars "AZURE_API_VERSION=2024-02-15-preview" \
        --set-env-vars "LITELLM_VISION_MODEL=gpt-4o" \
        --set-env-vars "LITELLM_TEXT_MODEL=gpt-4o" \
        --set-env-vars "JWT_SECRET_KEY=${JWT_SECRET}"
    
    API_URL=$(gcloud run services describe ${API_SERVICE} --region ${REGION} --format 'value(status.url)')
    echo -e "${GREEN}✓${NC} REST API: ${API_URL}"
}

# ============ PRINT SUMMARY ============
print_summary() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}🎉 BirdSense Deployed!${NC}"
    echo "=========================================="
    echo ""
    
    WEB_URL=$(gcloud run services describe ${WEB_SERVICE} --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "Not deployed")
    API_URL=$(gcloud run services describe ${API_SERVICE} --region ${REGION} --format 'value(status.url)' 2>/dev/null || echo "Not deployed")
    
    echo -e "🌐 ${GREEN}Web UI:${NC}   ${WEB_URL}"
    echo -e "🔌 ${GREEN}REST API:${NC} ${API_URL}"
    echo -e "📚 ${GREEN}API Docs:${NC} ${API_URL}/docs"
    echo ""
    echo "Docker Hub images:"
    echo "  ${WEB_IMAGE}:latest"
    echo "  ${API_IMAGE}:latest"
    echo ""
}

# ============ MAIN ============
MODE=${1:-both}

check_prerequisites

case $MODE in
    web)
        build_web
        deploy_web
        ;;
    api)
        build_api
        deploy_api
        ;;
    both|*)
        build_web
        build_api
        deploy_web
        deploy_api
        ;;
esac

print_summary
