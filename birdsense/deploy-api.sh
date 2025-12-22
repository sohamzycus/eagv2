#!/bin/bash
# 🐦 BirdSense API - Google Cloud Run Deployment
# Developed by Soham
#
# Prerequisites:
# 1. gcloud CLI installed and authenticated
# 2. Docker installed
# 3. Docker Hub account (or use GCR)
#
# Usage: ./deploy-api.sh

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="birdsense-api"
DOCKER_REPO="${DOCKER_REPO:-soham25niyogi/birdsense-api}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🐦 BirdSense API Deployment${NC}"
echo "================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Image: $DOCKER_REPO:$IMAGE_TAG"
echo ""

# Check for API key
if [ -z "$LITELLM_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  LITELLM_API_KEY not set. You'll need to provide it.${NC}"
    read -p "Enter LITELLM_API_KEY: " LITELLM_API_KEY
fi

# Step 1: Build Docker image
echo -e "\n${GREEN}Step 1/3: Building Docker image...${NC}"
docker buildx build \
    --platform linux/amd64 \
    -f Dockerfile.api \
    -t $DOCKER_REPO:$IMAGE_TAG \
    --push \
    .

# Step 2: Deploy to Cloud Run
echo -e "\n${GREEN}Step 2/3: Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image docker.io/$DOCKER_REPO:$IMAGE_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8000 \
    --set-env-vars "IS_AZURE=true" \
    --set-env-vars "LITELLM_API_KEY=$LITELLM_API_KEY" \
    --set-env-vars "LITELLM_API_BASE=https://zycus-ptu.azure-api.net/ptu-intakemanagement" \
    --set-env-vars "AZURE_DEPLOYMENT=gpt4o-130524" \
    --set-env-vars "AZURE_API_VERSION=2024-02-15-preview" \
    --set-env-vars "LITELLM_VISION_MODEL=gpt-4o" \
    --set-env-vars "LITELLM_TEXT_MODEL=gpt-4o" \
    --set-env-vars "JWT_SECRET_KEY=$(openssl rand -hex 32)"

# Step 3: Get service URL
echo -e "\n${GREEN}Step 3/3: Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo "================================"
echo -e "API URL: ${GREEN}$SERVICE_URL${NC}"
echo ""
echo "Test endpoints:"
echo "  Health: curl $SERVICE_URL/health"
echo "  Docs:   $SERVICE_URL/docs"
echo ""
echo "Update mobile app API URL:"
echo "  mobile/src/services/api.ts -> BASE_URL: '$SERVICE_URL'"

